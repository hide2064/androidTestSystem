"""
MockDriver のユニットテスト
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "equipment-agent"))
from drivers.mock.mock_driver import Driver


def test_connect_disconnect():
    d = Driver(name="test", config={})
    assert not d.is_connected
    d.connect()
    assert d.is_connected
    d.disconnect()
    assert not d.is_connected


def test_get_id():
    d = Driver(name="my_mock", config={})
    d.connect()
    result = d.get_id()
    assert "MOCK" in result
    assert "my_mock" in result


def test_send_command_idn():
    d = Driver(name="x", config={})
    d.connect()
    assert "MOCK" in d.send_command("*IDN?")


def test_send_command_rst():
    d = Driver(name="x", config={})
    d.connect()
    assert d.send_command("*RST") == ""


def test_send_command_other():
    d = Driver(name="x", config={})
    d.connect()
    resp = d.send_command("MEAS:VOLT?")
    assert "MOCK_RESPONSE" in resp


def test_measure_with_configured_value():
    d = Driver(name="x", config={"mock_values": {"voltage_ch1": 3.7}})
    d.connect()
    result = d.measure("voltage_ch1")
    assert abs(result.value - 3.7) < 0.5  # ノイズ込みで許容範囲
    assert result.unit == "mock"


def test_measure_unknown_parameter():
    d = Driver(name="x", config={})
    d.connect()
    # 未定義パラメータはbase=0.0で動作すること
    result = d.measure("unknown_param")
    assert isinstance(result.value, float)


def test_reset_via_base():
    d = Driver(name="x", config={})
    d.connect()
    d.reset()  # 例外が出ないこと（*RST を send_command 経由で呼ぶ）
