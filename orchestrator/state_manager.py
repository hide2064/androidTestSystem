"""
StateManager — 試験の実行状態を一元管理するクラス
"""
import asyncio
from datetime import datetime
from typing import Optional


class StateManager:

    def __init__(self):
        self.status: str = "idle"           # idle / running / finished / error
        self.current_scenario: Optional[str] = None
        self.current_device: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.current_step: Optional[dict] = None
        self._stop_requested: bool = False
        self.log_queue: asyncio.Queue = asyncio.Queue()
        self._results: list[dict] = []

    # ─── 状態遷移 ──────────────────────────────────────────

    def set_running(self, scenario_name: str, device_id: str) -> None:
        self.status = "running"
        self.current_scenario = scenario_name
        self.current_device = device_id
        self.start_time = datetime.now()
        self.current_step = None
        self._stop_requested = False

    def set_step(self, step: dict) -> None:
        self.current_step = step

    def request_stop(self) -> None:
        self._stop_requested = True

    def stop_requested(self) -> bool:
        return self._stop_requested

    def is_running(self) -> bool:
        return self.status == "running"

    def set_finished(self, summary: dict) -> None:
        self.status = "idle"
        self.current_step = None
        self._results.insert(0, summary)
        self._results = self._results[:100]   # 直近100件保持

    def set_error(self, message: str) -> None:
        self.status = "error"
        self.current_step = None

    # ─── 状態取得 ──────────────────────────────────────────

    def get_status(self) -> dict:
        elapsed = None
        if self.start_time:
            elapsed = str(datetime.now() - self.start_time).split(".")[0]
        return {
            "status": self.status,
            "scenario": self.current_scenario,
            "device": self.current_device,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "elapsed": elapsed,
            "current_step": self.current_step,
        }

    def get_results(self) -> list[dict]:
        return self._results

    def list_results(self, limit: int = 20) -> list[dict]:
        return self._results[:limit]
