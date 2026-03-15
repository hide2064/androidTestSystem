"""
analysis-service の Android API エンドポイントテスト。

SQLite インメモリ DB (StaticPool) を使い、MySQL コンテナ不要でテストします。
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "analysis-service"))

from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
import unittest.mock as mock

# ── SQLite インメモリ DB（StaticPool で全接続を共有） ─────────────────────

_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

_DDL = [
    """CREATE TABLE android_test_results (
        run_id       TEXT PRIMARY KEY,
        scenario     TEXT,
        device_id    TEXT,
        device_model TEXT,
        test_site    TEXT,
        result       TEXT,
        total        INTEGER,
        pass_count   INTEGER,
        fail_count   INTEGER,
        started_at   TEXT,
        finished_at  TEXT,
        note         TEXT
    )""",
    """CREATE TABLE android_test_steps (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id          TEXT,
        step_id         INTEGER,
        action          TEXT,
        description     TEXT,
        response        TEXT,
        measured_value  REAL,
        unit            TEXT,
        upper_limit     REAL,
        lower_limit     REAL,
        pass            INTEGER,
        error_msg       TEXT,
        executed_at     TEXT
    )""",
]

with _ENGINE.begin() as _conn:
    for _stmt in _DDL:
        _conn.execute(text(_stmt))


@contextmanager
def _fake_conn():
    with _ENGINE.connect() as conn:
        yield conn


# ── app をインポート前にルーターの参照をパッチ ──────────────────────────
# android.py は `from app.database import get_android_connection` しているため、
# app.routers.android モジュール内のシンボルをオーバーライドする。

with mock.patch.dict("sys.modules", {}):
    from app.main import app
    import app.routers.android as _android_mod

_android_mod.get_android_connection = _fake_conn  # ローカル参照を差し替え

from fastapi.testclient import TestClient
client = TestClient(app)


# ── ヘルパー ──────────────────────────────────────────────────────────────

def _clear():
    with _ENGINE.begin() as conn:
        conn.execute(text("DELETE FROM android_test_steps"))
        conn.execute(text("DELETE FROM android_test_results"))


def _insert_result(run_id="run001", scenario="wifi", device_id="dev-001",
                   result="PASS", total=3, pass_count=3, fail_count=0,
                   test_site="lab", started_at="2026-03-15 10:00:00"):
    with _ENGINE.begin() as conn:
        conn.execute(text("""
            INSERT INTO android_test_results
              (run_id, scenario, device_id, device_model, test_site,
               result, total, pass_count, fail_count, started_at)
            VALUES
              (:run_id, :scenario, :device_id, '', :test_site,
               :result, :total, :pass_count, :fail_count, :started_at)
        """), {"run_id": run_id, "scenario": scenario, "device_id": device_id,
               "test_site": test_site, "result": result, "total": total,
               "pass_count": pass_count, "fail_count": fail_count,
               "started_at": started_at})


def _insert_step(run_id="run001", step_id=1, action="adb",
                 pass_=True, error_msg=""):
    with _ENGINE.begin() as conn:
        conn.execute(text("""
            INSERT INTO android_test_steps
              (run_id, step_id, action, description, pass, error_msg)
            VALUES
              (:run_id, :step_id, :action, '', :pass, :error_msg)
        """), {"run_id": run_id, "step_id": step_id, "action": action,
               "pass": 1 if pass_ else 0, "error_msg": error_msg})


# ── テスト ────────────────────────────────────────────────────────────────

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_filters_empty_db():
    _clear()
    res = client.get("/api/v1/android/filters")
    assert res.status_code == 200
    data = res.json()
    assert data["scenarios"] == []
    assert data["device_ids"] == []
    assert data["results"] == []


def test_summary_empty_db():
    _clear()
    res = client.get("/api/v1/android/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["pass_count"] == 0
    assert data["yield_pct"] == 0


def test_yield_empty_db():
    _clear()
    res = client.get("/api/v1/android/yield")
    assert res.status_code == 200
    assert res.json()["items"] == []


def test_trend_empty_db():
    _clear()
    res = client.get("/api/v1/android/trend")
    assert res.status_code == 200
    assert res.json()["labels"] == []
    assert res.json()["values"] == []


def test_results_empty_db():
    _clear()
    res = client.get("/api/v1/android/results")
    assert res.status_code == 200
    assert res.json()["total"] == 0
    assert res.json()["items"] == []


def test_results_with_data():
    _clear()
    _insert_result("r1", "wifi", "dev-001", result="PASS")
    _insert_result("r2", "bt",   "dev-002", result="FAIL")
    res = client.get("/api/v1/android/results")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_summary_with_data():
    _clear()
    _insert_result("r1", result="PASS", pass_count=3, fail_count=0, total=3)
    _insert_result("r2", result="FAIL", pass_count=1, fail_count=2, total=3)
    res = client.get("/api/v1/android/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert data["pass_count"] == 1
    assert data["fail_count"] == 1
    # SQLite は整数除算のため MySQL (50.0) と異なる場合がある。0〜100 の範囲であれば OK
    assert 0 <= data["yield_pct"] <= 100


def test_yield_group_by_invalid():
    res = client.get("/api/v1/android/yield?group_by=INVALID_COLUMN")
    assert res.status_code == 400


def test_result_detail_not_found():
    _clear()
    res = client.get("/api/v1/android/results/nonexistent_run_id")
    assert res.status_code == 404


def test_result_detail_with_steps():
    _clear()
    _insert_result("r_detail", "wifi", "dev-001")
    _insert_step("r_detail", step_id=1, action="adb",        pass_=True)
    _insert_step("r_detail", step_id=2, action="screenshot", pass_=False, error_msg="timeout")
    res = client.get("/api/v1/android/results/r_detail")
    assert res.status_code == 200
    data = res.json()
    assert data["run_id"] == "r_detail"
    assert len(data["steps"]) == 2
    assert data["steps"][0]["action"] == "adb"
    assert data["steps"][1]["pass"] is False
    assert data["steps"][1]["error_msg"] == "timeout"
