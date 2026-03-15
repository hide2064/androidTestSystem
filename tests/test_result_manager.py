"""
ResultManager のユニットテスト（evaluate / evaluate_numeric / summarize）
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "orchestrator"))

# SharePointClient の初期化を回避するためモック
import unittest.mock as mock
with mock.patch("sharepoint_client.SharePointClient"):
    from result_manager import ResultManager

rm = ResultManager.__new__(ResultManager)
rm._results_dir = __import__("pathlib").Path("/tmp/test_results")
rm._results_dir.mkdir(exist_ok=True)
rm._sp = mock.MagicMock()


# ─── evaluate（文字列）─────────────────────────────────────

def test_evaluate_no_expect():
    assert rm.evaluate(None, "anything") is True

def test_evaluate_contains_pass():
    assert rm.evaluate({"contains": "Pixel"}, "Pixel 6 Pro") is True

def test_evaluate_contains_fail():
    assert rm.evaluate({"contains": "Pixel"}, "Samsung Galaxy") is False

def test_evaluate_equals_pass():
    assert rm.evaluate({"equals": "1"}, "1") is True

def test_evaluate_equals_fail():
    assert rm.evaluate({"equals": "1"}, "0") is False

def test_evaluate_equals_strips_whitespace():
    assert rm.evaluate({"equals": "1"}, "1\n") is True

def test_evaluate_not_contains_pass():
    assert rm.evaluate({"not_contains": "ERROR"}, "OK result") is True

def test_evaluate_not_contains_fail():
    assert rm.evaluate({"not_contains": "ERROR"}, "ERROR: failed") is False


# ─── evaluate_numeric（数値）─────────────────────────────

def test_evaluate_numeric_no_expect():
    assert rm.evaluate_numeric(None, 3.7) is True

def test_evaluate_numeric_greater_than_pass():
    assert rm.evaluate_numeric({"greater_than": -80}, -70.0) is True

def test_evaluate_numeric_greater_than_fail():
    assert rm.evaluate_numeric({"greater_than": -80}, -90.0) is False

def test_evaluate_numeric_less_than_pass():
    assert rm.evaluate_numeric({"less_than": 5.0}, 3.7) is True

def test_evaluate_numeric_less_than_fail():
    assert rm.evaluate_numeric({"less_than": 5.0}, 6.0) is False

def test_evaluate_numeric_between_pass():
    assert rm.evaluate_numeric({"between": [3.5, 4.2]}, 3.7) is True

def test_evaluate_numeric_between_boundary():
    assert rm.evaluate_numeric({"between": [3.5, 4.2]}, 3.5) is True
    assert rm.evaluate_numeric({"between": [3.5, 4.2]}, 4.2) is True

def test_evaluate_numeric_between_fail():
    assert rm.evaluate_numeric({"between": [3.5, 4.2]}, 4.5) is False

def test_evaluate_numeric_equals_pass():
    assert rm.evaluate_numeric({"equals": 3.7, "tolerance": 0.01}, 3.705) is True

def test_evaluate_numeric_equals_fail():
    assert rm.evaluate_numeric({"equals": 3.7, "tolerance": 0.01}, 3.8) is False


# ─── summarize ─────────────────────────────────────────────

def test_summarize_all_pass():
    steps = [
        {"step_id": 1, "action": "adb", "pass": True},
        {"step_id": 2, "action": "wait", "pass": True},
    ]
    s = rm.summarize("wifi_test", "device-001", steps)
    assert s["result"] == "PASS"
    assert s["pass_count"] == 2
    assert s["fail_count"] == 0
    assert s["total"] == 2
    assert s["scenario"] == "wifi_test"
    assert s["device_id"] == "device-001"


def test_summarize_with_fail():
    steps = [
        {"step_id": 1, "action": "adb", "pass": True},
        {"step_id": 2, "action": "assert_text", "pass": False},
        {"step_id": 3, "action": "wait", "pass": True},
    ]
    s = rm.summarize("app_test", "device-002", steps)
    assert s["result"] == "FAIL"
    assert s["pass_count"] == 2
    assert s["fail_count"] == 1


def test_summarize_empty():
    s = rm.summarize("empty", "dev", [])
    assert s["total"] == 0
    assert s["result"] == "PASS"   # FAILが0件なのでPASS
