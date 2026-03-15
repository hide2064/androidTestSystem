"""
ResultManager — 試験結果の集計・判定・MySQL保存・SharePoint送信
"""
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text

from sharepoint_client import SharePointClient

logger = logging.getLogger(__name__)


def _make_engine():
    """環境変数から SQLAlchemy エンジンを生成する。DB_HOST 未設定なら None を返す。"""
    host = os.getenv("DB_HOST")
    if not host:
        return None
    port = os.getenv("DB_PORT", "3306")
    user = os.getenv("DB_USER", "testuser")
    password = os.getenv("DB_PASSWORD", "")
    name = os.getenv("DB_NAME", "testSystemDB")
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)


class ResultManager:

    def __init__(self):
        self._sp = SharePointClient()
        self._results_dir = Path("results")
        self._results_dir.mkdir(exist_ok=True)
        self._engine = _make_engine()
        if self._engine:
            logger.info("MySQL 接続設定完了: %s/%s", os.getenv("DB_HOST"), os.getenv("DB_NAME"))
        else:
            logger.info("DB_HOST 未設定のため MySQL 書き込みを無効化")

    def summarize(self, scenario_name: str, device_id: str,
                  step_results: list[dict]) -> dict:
        """ステップ結果リストから試験サマリーを生成する"""
        total = len(step_results)
        passed = sum(1 for r in step_results if r.get("pass"))
        failed = total - passed

        # run_id: タイムスタンプ + シナリオ名 + デバイスID でユニークなIDを生成
        ts = datetime.now()
        run_id = f"{ts.strftime('%Y%m%dT%H%M%S')}_{scenario_name}_{device_id}"

        summary = {
            "run_id": run_id,
            "scenario": scenario_name,
            "device_id": device_id,
            "test_site": os.getenv("TEST_SITE", "unknown"),
            "timestamp": ts.isoformat(),
            "total": total,
            "pass_count": passed,
            "fail_count": failed,
            "result": "PASS" if failed == 0 else "FAIL",
            "steps": step_results,
        }
        return summary

    async def save_and_send(self, summary: dict) -> None:
        """ローカル保存 → MySQL書き込み → SharePoint送信"""
        # ① ローカルJSON保存（必ず実行）
        filename = (f"{summary['timestamp'][:19].replace(':', '-')}_"
                    f"{summary['scenario']}_{summary['device_id']}.json")
        local_path = self._results_dir / filename
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        logger.info("結果を保存: %s", local_path)

        # ② MySQL書き込み（失敗しても試験全体はエラーにしない）
        if self._engine:
            try:
                self._save_to_mysql(summary)
                logger.info("MySQL書き込み完了: run_id=%s", summary.get("run_id"))
            except Exception as e:
                logger.warning("MySQL書き込みに失敗（ローカル保存は完了）: %s", e)

        # ③ SharePoint送信（失敗しても試験全体はエラーにしない）
        try:
            await self._sp.send_result(summary)
        except Exception as e:
            logger.warning("SharePoint送信に失敗（ローカル保存は完了）: %s", e)

    def _save_to_mysql(self, summary: dict) -> None:
        """android_test_results + android_test_steps に書き込む"""
        run_id = summary.get("run_id") or str(uuid.uuid4())
        started_at = summary.get("timestamp", datetime.now().isoformat())
        finished_at = datetime.now().isoformat()

        with self._engine.begin() as conn:
            # サマリ行を INSERT
            conn.execute(text("""
                INSERT INTO android_test_results
                    (run_id, scenario, device_id, test_site,
                     started_at, finished_at,
                     total, pass_count, fail_count, result)
                VALUES
                    (:run_id, :scenario, :device_id, :test_site,
                     :started_at, :finished_at,
                     :total, :pass_count, :fail_count, :result)
                ON DUPLICATE KEY UPDATE
                    finished_at = VALUES(finished_at),
                    total       = VALUES(total),
                    pass_count  = VALUES(pass_count),
                    fail_count  = VALUES(fail_count),
                    result      = VALUES(result)
            """), {
                "run_id":      run_id,
                "scenario":    summary["scenario"],
                "device_id":   summary["device_id"],
                "test_site":   summary.get("test_site", "unknown"),
                "started_at":  started_at,
                "finished_at": finished_at,
                "total":       summary["total"],
                "pass_count":  summary["pass_count"],
                "fail_count":  summary["fail_count"],
                "result":      summary["result"],
            })

            # ステップ行を INSERT（既存行は削除して再挿入）
            conn.execute(text(
                "DELETE FROM android_test_steps WHERE run_id = :run_id"
            ), {"run_id": run_id})

            for step in summary.get("steps", []):
                conn.execute(text("""
                    INSERT INTO android_test_steps
                        (run_id, step_id, action, description,
                         response, measured_value, unit,
                         upper_limit, lower_limit, pass, error_msg)
                    VALUES
                        (:run_id, :step_id, :action, :description,
                         :response, :measured_value, :unit,
                         :upper_limit, :lower_limit, :pass, :error_msg)
                """), {
                    "run_id":        run_id,
                    "step_id":       step.get("step_id"),
                    "action":        step.get("action", ""),
                    "description":   step.get("description"),
                    "response":      str(step.get("response", "")) if step.get("response") is not None else None,
                    "measured_value": step.get("measured_value"),
                    "unit":          step.get("unit"),
                    "upper_limit":   step.get("upper_limit"),
                    "lower_limit":   step.get("lower_limit"),
                    "pass":          bool(step.get("pass", False)),
                    "error_msg":     step.get("error"),
                })

    def evaluate(self, expect: dict | None, response: str) -> bool:
        """期待値に対してレスポンスを評価してPass/Failを返す"""
        if not expect:
            return True
        if "contains" in expect:
            return str(expect["contains"]) in response
        if "equals" in expect:
            return str(expect["equals"]) == response.strip()
        if "not_contains" in expect:
            return str(expect["not_contains"]) not in response
        return True

    def evaluate_numeric(self, expect: dict | None, value: float) -> bool:
        """数値の期待値評価"""
        if not expect:
            return True
        if "greater_than" in expect:
            return value > expect["greater_than"]
        if "less_than" in expect:
            return value < expect["less_than"]
        if "between" in expect:
            lo, hi = expect["between"]
            return lo <= value <= hi
        if "equals" in expect:
            return abs(value - expect["equals"]) < expect.get("tolerance", 0.001)
        return True
