"""
StateManager のユニットテスト
"""
import asyncio, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "orchestrator"))
from state_manager import StateManager


def test_initial_state():
    sm = StateManager()
    assert sm.status == "idle"
    assert not sm.is_running()
    assert not sm.stop_requested()


def test_set_running():
    sm = StateManager()
    sm.set_running("wifi_test", "device-001")
    assert sm.status == "running"
    assert sm.is_running()
    assert sm.current_scenario == "wifi_test"
    assert sm.current_device == "device-001"
    assert sm.start_time is not None
    assert not sm.stop_requested()


def test_request_stop():
    sm = StateManager()
    sm.set_running("wifi_test", "device-001")
    sm.request_stop()
    assert sm.stop_requested()


def test_set_finished():
    sm = StateManager()
    sm.set_running("wifi_test", "device-001")
    summary = {"scenario": "wifi_test", "result": "PASS", "pass_count": 5,
               "fail_count": 0, "total": 5, "timestamp": "2026-03-15T10:00:00",
               "device_id": "device-001", "steps": []}
    sm.set_finished(summary)
    assert sm.status == "idle"
    assert not sm.is_running()
    assert sm.current_step is None


def test_results_limit():
    """直近100件を超えたら古い結果は破棄される"""
    sm = StateManager()
    for i in range(110):
        sm.set_running(f"scenario_{i}", "device")
        sm.set_finished({"scenario": f"scenario_{i}", "result": "PASS",
                         "pass_count": 1, "fail_count": 0, "total": 1,
                         "timestamp": "2026-03-15T10:00:00",
                         "device_id": "device", "steps": []})
    assert len(sm.get_results()) == 100


def test_list_results_limit():
    sm = StateManager()
    for i in range(30):
        sm.set_running(f"s{i}", "d")
        sm.set_finished({"scenario": f"s{i}", "result": "PASS",
                         "pass_count": 1, "fail_count": 0, "total": 1,
                         "timestamp": "2026-03-15T10:00:00",
                         "device_id": "d", "steps": []})
    assert len(sm.list_results(10)) == 10
    assert len(sm.list_results(50)) == 30


def test_get_status_running():
    sm = StateManager()
    sm.set_running("s1", "dev-1")
    sm.set_step({"id": 3, "description": "テストステップ"})
    status = sm.get_status()
    assert status["status"] == "running"
    assert status["scenario"] == "s1"
    assert status["device"] == "dev-1"
    assert status["current_step"]["id"] == 3
    assert status["elapsed"] is not None


def test_set_error():
    sm = StateManager()
    sm.set_running("s1", "d")
    sm.set_error("接続失敗")
    assert sm.status == "error"
    assert not sm.is_running()


def test_log_queue():
    """log_queue に put したエントリが get で取り出せること"""
    async def _run():
        sm = StateManager()
        await sm.log_queue.put({"message": "hello"})
        item = await sm.log_queue.get()
        assert item["message"] == "hello"
    asyncio.run(_run())
