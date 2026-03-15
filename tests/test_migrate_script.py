"""
scripts/migrate_json_to_mysql.py のユニットテスト。

SQLite インメモリ DB でマイグレーションロジックを検証します。
"""
import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

# ── SQLite インメモリ DB ───────────────────────────────────────────────────

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
        pass            INTEGER,
        error_msg       TEXT
    )""",
]

with _ENGINE.begin() as _conn:
    for _stmt in _DDL:
        _conn.execute(text(_stmt))


# ── スクリプトから migrate() と load_json() を取り込む ────────────────────

# migrate_json_to_mysql.py は SQLAlchemy の create_engine を使うが、
# migrate() 関数はエンジンを外から受け取るので直接テストできる。

# モジュールを動的 import
import importlib.util

_SCRIPT = Path(__file__).parent.parent / "scripts" / "migrate_json_to_mysql.py"
_spec = importlib.util.spec_from_file_location("migrate_script", _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)

# .env 読み込みをスキップするためダミー環境変数を設定してからロード
os.environ.setdefault("DB_HOST", "")  # 空でも import は通る
_spec.loader.exec_module(_mod)

load_json = _mod.load_json
migrate   = _mod.migrate


# ── ヘルパー ──────────────────────────────────────────────────────────────

def _count(table):
    with _ENGINE.connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()


def _clear():
    with _ENGINE.begin() as conn:
        conn.execute(text("DELETE FROM android_test_steps"))
        conn.execute(text("DELETE FROM android_test_results"))


def _sample_json(**kwargs):
    base = {
        "run_id":     "20260315T100000_wifi_dev001",
        "scenario":   "wifi_test",
        "device_id":  "dev-001",
        "test_site":  "lab",
        "timestamp":  "2026-03-15T10:00:00",
        "total":      3,
        "pass_count": 2,
        "fail_count": 1,
        "result":     "FAIL",
        "steps": [
            {"step_id": 1, "action": "adb",  "pass": True},
            {"step_id": 2, "action": "wait", "pass": True},
            {"step_id": 3, "action": "adb",  "pass": False, "error": "connection refused"},
        ],
    }
    base.update(kwargs)
    return base


# ── テスト ────────────────────────────────────────────────────────────────

def test_load_json_valid(tmp_path):
    """正常なJSONファイルを load_json() で読み込める"""
    p = tmp_path / "result.json"
    data = _sample_json()
    p.write_text(json.dumps(data), encoding="utf-8")
    loaded = load_json(p)
    assert loaded["run_id"] == data["run_id"]
    assert loaded["total"] == 3


def test_load_json_missing_run_id_returns_skipped():
    """run_id なし → migrate() が 'skipped' を返す"""
    data = _sample_json()
    del data["run_id"]
    with _ENGINE.begin() as conn:
        result = migrate(data, conn, dry_run=False)
    assert "skipped" in result


def test_migrate_dry_run():
    """dry_run=True → DB に何も書き込まれない"""
    _clear()
    data = _sample_json()
    with _ENGINE.begin() as conn:
        status = migrate(data, conn, dry_run=True)
    assert "dry-run" in status
    assert _count("android_test_results") == 0


# ── 以下は MySQL 固有の ON DUPLICATE KEY UPDATE を使うため
#    MagicMock で接続を模倣して呼び出しパターンを検証する ───────────────────

from unittest.mock import MagicMock, call
from sqlalchemy import text as sa_text


def test_migrate_inserts_result():
    """migrate() → conn.execute が正しい回数呼ばれる（results INSERT + steps DELETE + steps INSERT×n）"""
    data = _sample_json()
    mock_conn = MagicMock()
    status = migrate(data, mock_conn, dry_run=False)
    assert "inserted" in status
    # INSERT results (1回) + DELETE steps (1回) + INSERT steps (3件) = 5回
    assert mock_conn.execute.call_count == 5


def test_migrate_inserts_steps():
    """migrate() → ステップ数分だけ INSERT が呼ばれる"""
    data = _sample_json()  # 3ステップ
    mock_conn = MagicMock()
    migrate(data, mock_conn, dry_run=False)
    # 全呼び出しのうち INSERT into android_test_steps が 3 回あること
    calls_sql = [str(c.args[0]) for c in mock_conn.execute.call_args_list if c.args]
    step_inserts = [s for s in calls_sql if "android_test_steps" in s and "INSERT" in s.upper()]
    assert len(step_inserts) == 3


def test_migrate_upsert_no_duplicate():
    """同じ run_id で2回呼んでも mock は state を持たないので status=inserted になること"""
    data = _sample_json()
    mock_conn = MagicMock()
    status1 = migrate(data, mock_conn, dry_run=False)
    status2 = migrate(data, mock_conn, dry_run=False)
    assert "inserted" in status1
    assert "inserted" in status2
    # 2回分なので execute 呼び出し数は 5 * 2 = 10
    assert mock_conn.execute.call_count == 10
