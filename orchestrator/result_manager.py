"""
ResultManager — 試験結果の集計・判定・SharePoint送信
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from sharepoint_client import SharePointClient

logger = logging.getLogger(__name__)


class ResultManager:

    def __init__(self):
        self._sp = SharePointClient()
        self._results_dir = Path("results")
        self._results_dir.mkdir(exist_ok=True)

    def summarize(self, scenario_name: str, device_id: str,
                  step_results: list[dict]) -> dict:
        """ステップ結果リストから試験サマリーを生成する"""
        total = len(step_results)
        passed = sum(1 for r in step_results if r.get("pass"))
        failed = total - passed

        summary = {
            "scenario": scenario_name,
            "device_id": device_id,
            "test_site": os.getenv("TEST_SITE", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "total": total,
            "pass_count": passed,
            "fail_count": failed,
            "result": "PASS" if failed == 0 else "FAIL",
            "steps": step_results,
        }
        return summary

    async def save_and_send(self, summary: dict) -> None:
        """ローカルに保存してSharePointにも送信する"""
        # ローカル保存
        filename = (f"{summary['timestamp'][:19].replace(':', '-')}_"
                    f"{summary['scenario']}_{summary['device_id']}.json")
        local_path = self._results_dir / filename
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        logger.info("結果を保存: %s", local_path)

        # SharePoint送信（失敗しても試験全体はエラーにしない）
        try:
            await self._sp.send_result(summary)
        except Exception as e:
            logger.warning("SharePoint送信に失敗（ローカル保存は完了）: %s", e)

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
