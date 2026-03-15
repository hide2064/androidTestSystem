"""
ScenarioRunner — YAMLシナリオを1ステップずつ実行する試験エンジン
"""
import asyncio
import logging
from datetime import datetime

from agent_client import AndroidAgentClient, EquipmentAgentClient
from result_manager import ResultManager
from scenario_parser import ScenarioParser
from state_manager import StateManager

logger = logging.getLogger(__name__)


class ScenarioRunner:

    def __init__(self, state: StateManager):
        self.state = state
        self.android = AndroidAgentClient()
        self.equipment = EquipmentAgentClient()
        self.result_mgr = ResultManager()

    async def run(self, scenario_name: str, device_id: str) -> None:
        """シナリオを上から順に実行するメインループ"""
        try:
            scenario = ScenarioParser.load(f"scenarios/{scenario_name}.yaml")
        except Exception as e:
            await self._log(f"シナリオ読み込みエラー: {e}", level="ERROR")
            self.state.set_error(str(e))
            return

        self.state.set_running(scenario_name, device_id)
        await self._log(f"=== 試験開始: {scenario.get('name', scenario_name)} ===")
        await self._log(f"端末: {device_id}")

        step_results: list[dict] = []

        for step in scenario["steps"]:
            if self.state.stop_requested():
                await self._log("⏹ 試験を中断しました")
                break

            step_num = step["id"]
            desc = step["description"]
            self.state.set_step({"id": step_num, "description": desc})
            await self._log(f"[Step {step_num}] {desc}")

            try:
                result = await self._execute_step(step, device_id)
                step_results.append(result)
                icon = "✅" if result["pass"] else "❌"
                await self._log(f"  → {icon} {'PASS' if result['pass'] else 'FAIL'}")

                # on_fail: stop の場合は即中断
                if not result["pass"] and step.get("on_fail") == "stop":
                    await self._log("  → on_fail:stop のため試験を中断します")
                    break

            except Exception as exc:
                msg = str(exc)
                logger.exception("Step %s でエラー", step_num)
                await self._log(f"  → ⚠️ ERROR: {msg}")
                step_results.append({
                    "step_id": step_num,
                    "action": step.get("action"),
                    "pass": False,
                    "error": msg,
                })
                if step.get("on_fail") == "stop":
                    break

        summary = self.result_mgr.summarize(scenario_name, device_id, step_results)
        await self.result_mgr.save_and_send(summary)
        self.state.set_finished(summary)

        total = summary["total"]
        passed = summary["pass_count"]
        verdict = "✅ PASS" if summary["result"] == "PASS" else "❌ FAIL"
        await self._log(f"=== 試験完了: {verdict}  ({passed}/{total} PASS) ===")

    # ─── ステップ実行 ─────────────────────────────────────

    async def _execute_step(self, step: dict, device_id: str) -> dict:
        action = step["action"]
        base = {"step_id": step["id"], "action": action}

        # ── ADB コマンド ─────────────────────────────────
        if action == "adb":
            stdout = await self.android.adb_command(device_id, step["command"])
            passed = self.result_mgr.evaluate(step.get("expect"), stdout)
            return {**base, "pass": passed, "response": stdout}

        # ── Appium タップ ─────────────────────────────────
        elif action == "tap":
            await self.android.tap(device_id, step["locator_type"], step["locator_value"])
            return {**base, "pass": True}

        # ── テキスト入力 ─────────────────────────────────
        elif action == "input_text":
            await self.android.input_text(
                device_id, step["locator_type"], step["locator_value"], step["text"]
            )
            return {**base, "pass": True}

        # ── テキスト確認 ─────────────────────────────────
        elif action == "assert_text":
            text = await self.android.get_text(
                device_id, step["locator_type"], step["locator_value"]
            )
            passed = self.result_mgr.evaluate(step.get("expect"), text)
            return {**base, "pass": passed, "actual": text,
                    "expected": step.get("expect")}

        # ── 要素存在確認 ─────────────────────────────────
        elif action == "assert_exists":
            exists = await self.android.assert_exists(
                device_id, step["locator_type"], step["locator_value"]
            )
            return {**base, "pass": exists}

        # ── 計測器 測定 ───────────────────────────────────
        elif action == "equipment_measure":
            result = await self.equipment.measure(step["device"], step["parameter"])
            value = result["value"]
            passed = self.result_mgr.evaluate_numeric(step.get("expect"), value)
            await self._log(f"    計測値: {value} {result.get('unit', '')}")
            return {**base, "pass": passed,
                    "value": value, "unit": result.get("unit"),
                    "expected": step.get("expect")}

        # ── 計測器 メソッド呼び出し ──────────────────────
        elif action == "equipment_method":
            result = await self.equipment.call_method(
                step["device"], step["method"], step.get("args", {})
            )
            return {**base, "pass": True, "response": result}

        # ── 計測器 生コマンド ────────────────────────────
        elif action == "equipment_command":
            response = await self.equipment.send_command(step["device"], step["command"])
            passed = self.result_mgr.evaluate(step.get("expect"), response)
            return {**base, "pass": passed, "response": response}

        # ── スクリーンショット ────────────────────────────
        elif action == "screenshot":
            save_path = step.get("save_path", f"/app/results/sc_step{step['id']}.png")
            path = await self.android.screenshot(device_id, save_path)
            return {**base, "pass": True, "path": path}

        # ── 待機 ─────────────────────────────────────────
        elif action == "wait":
            await asyncio.sleep(step["seconds"])
            return {**base, "pass": True}

        else:
            raise ValueError(f"未知の action: {action}")

    # ─── ログ送信 ─────────────────────────────────────────

    async def _log(self, message: str, level: str = "INFO") -> None:
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": message,
        }
        logger.log(getattr(logging, level, logging.INFO), message)
        await self.state.log_queue.put(entry)
