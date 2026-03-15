"""
EquipmentAgent のユニットテスト（モックドライバを使用）
"""
import os, sys, textwrap, tempfile, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "equipment-agent"))
from agent import EquipmentAgent
from base_driver import MeasureResult


def make_config(content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml",
                                   delete=False, encoding="utf-8")
    f.write(textwrap.dedent(content))
    f.close()
    return f.name


# ─── モックドライバを使ったロード確認 ────────────────────

def test_load_mock_drivers():
    cfg = make_config("""
        instruments:
          mock_power:
            driver: mock.mock_driver
            connection: mock
            description: "モック電源"
            mock_values:
              voltage_ch1: 3.7
          mock_rf:
            driver: mock.mock_driver
            connection: mock
            description: "モックRF"
            mock_values:
              peak_power: -30.0
    """)
    agent = EquipmentAgent(config_path=cfg)
    instruments = agent.list_instruments()
    names = [i["name"] for i in instruments]
    assert "mock_power" in names
    assert "mock_rf" in names


def test_connect_mock():
    cfg = make_config("""
        instruments:
          mock_power:
            driver: mock.mock_driver
            connection: mock
            mock_values:
              voltage_ch1: 3.7
    """)
    agent = EquipmentAgent(config_path=cfg)
    agent.connect("mock_power")
    status = agent.list_instruments()
    assert status[0]["connected"] is True


def test_measure_mock():
    cfg = make_config("""
        instruments:
          mock_power:
            driver: mock.mock_driver
            connection: mock
            mock_values:
              voltage_ch1: 3.7
    """)
    agent = EquipmentAgent(config_path=cfg)
    agent.connect("mock_power")
    result = agent.measure("mock_power", "voltage_ch1")
    # モックはノイズを加えるので許容範囲で確認
    assert abs(result["value"] - 3.7) < 0.5
    assert "unit" in result


def test_send_command_mock():
    cfg = make_config("""
        instruments:
          mock1:
            driver: mock.mock_driver
            connection: mock
    """)
    agent = EquipmentAgent(config_path=cfg)
    agent.connect("mock1")
    resp = agent.send_command("mock1", "*IDN?")
    assert "MOCK" in resp


def test_get_id_mock():
    cfg = make_config("""
        instruments:
          mock1:
            driver: mock.mock_driver
            connection: mock
    """)
    agent = EquipmentAgent(config_path=cfg)
    agent.connect("mock1")
    id_str = agent.get_id("mock1")
    assert "MOCK" in id_str


def test_call_method_not_found():
    cfg = make_config("""
        instruments:
          mock1:
            driver: mock.mock_driver
            connection: mock
    """)
    agent = EquipmentAgent(config_path=cfg)
    agent.connect("mock1")
    with pytest.raises(AttributeError, match="nonexistent_method"):
        agent.call_method("mock1", "nonexistent_method", {})


def test_get_unknown_instrument():
    cfg = make_config("instruments:\n  mock1:\n    driver: mock.mock_driver\n    connection: mock\n")
    agent = EquipmentAgent(config_path=cfg)
    with pytest.raises(KeyError, match="no_such_device"):
        agent.measure("no_such_device", "voltage")


def test_connect_all():
    cfg = make_config("""
        instruments:
          m1:
            driver: mock.mock_driver
            connection: mock
          m2:
            driver: mock.mock_driver
            connection: mock
    """)
    agent = EquipmentAgent(config_path=cfg)
    results = agent.connect_all()
    assert results["m1"] == "ok"
    assert results["m2"] == "ok"


def test_missing_config():
    """存在しない config でも例外なく起動できること（警告ログのみ）"""
    agent = EquipmentAgent(config_path="/nonexistent/equipment.yaml")
    assert agent.list_instruments() == []


def test_invalid_driver_path():
    """不正なドライバパスはロードをスキップしてログ出力するだけ"""
    cfg = make_config("""
        instruments:
          bad:
            driver: nonexistent.driver
            connection: mock
    """)
    agent = EquipmentAgent(config_path=cfg)  # 例外にならないこと
    assert agent.list_instruments() == []
