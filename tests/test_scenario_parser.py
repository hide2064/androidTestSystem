"""
ScenarioParser のユニットテスト
"""
import os, sys, textwrap, tempfile, pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "orchestrator"))
from scenario_parser import ScenarioParser


# ─── フィクスチャ ─────────────────────────────────────────

def write_yaml(content: str) -> str:
    """一時YAMLファイルを作成してパスを返す"""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml",
                                   delete=False, encoding="utf-8")
    f.write(textwrap.dedent(content))
    f.close()
    return f.name


# ─── 正常系 ───────────────────────────────────────────────

def test_load_valid_scenario():
    path = write_yaml("""
        name: テスト試験
        version: "1.0"
        steps:
          - id: 1
            description: ADBコマンド
            action: adb
            command: shell getprop ro.product.model
          - id: 2
            description: 待機
            action: wait
            seconds: 3
    """)
    sc = ScenarioParser.load(path)
    assert sc["name"] == "テスト試験"
    assert len(sc["steps"]) == 2
    assert sc["steps"][0]["action"] == "adb"


def test_load_all_actions():
    """全 action 種別を含むシナリオが正常にロードできること"""
    path = write_yaml("""
        name: 全アクション試験
        steps:
          - {id: 1, description: a, action: adb, command: shell echo}
          - {id: 2, description: b, action: tap, locator_type: id, locator_value: btn}
          - {id: 3, description: c, action: input_text, locator_type: id, locator_value: x, text: hi}
          - {id: 4, description: d, action: assert_text, locator_type: id, locator_value: x}
          - {id: 5, description: e, action: assert_exists, locator_type: id, locator_value: x}
          - {id: 6, description: f, action: equipment_measure, device: d, parameter: v}
          - {id: 7, description: g, action: equipment_method, device: d, method: m}
          - {id: 8, description: h, action: equipment_command, device: d, command: c}
          - {id: 9, description: i, action: screenshot}
          - {id: 10, description: j, action: wait, seconds: 1}
    """)
    sc = ScenarioParser.load(path)
    assert len(sc["steps"]) == 10


# ─── 異常系 ───────────────────────────────────────────────

def test_load_missing_file():
    with pytest.raises(FileNotFoundError):
        ScenarioParser.load("/nonexistent/path/scenario.yaml")


def test_load_missing_name():
    path = write_yaml("""
        steps:
          - {id: 1, description: a, action: wait, seconds: 1}
    """)
    with pytest.raises(ValueError, match="name"):
        ScenarioParser.load(path)


def test_load_missing_steps():
    path = write_yaml("name: test\n")
    with pytest.raises(ValueError, match="steps"):
        ScenarioParser.load(path)


def test_load_missing_required_key():
    path = write_yaml("""
        name: test
        steps:
          - id: 1
            action: adb
    """)
    with pytest.raises(ValueError, match="description"):
        ScenarioParser.load(path)


def test_load_invalid_action():
    path = write_yaml("""
        name: test
        steps:
          - id: 1
            description: test
            action: invalid_action
    """)
    with pytest.raises(ValueError, match="invalid_action"):
        ScenarioParser.load(path)


def test_list_scenarios(tmp_path):
    (tmp_path / "s1.yaml").write_text(
        "name: 試験1\nsteps:\n  - {id: 1, description: a, action: wait, seconds: 1}\n",
        encoding="utf-8"
    )
    (tmp_path / "s2.yaml").write_text(
        "name: 試験2\nsteps:\n  - {id: 1, description: a, action: wait, seconds: 1}\n  - {id: 2, description: b, action: wait, seconds: 1}\n",
        encoding="utf-8"
    )
    result = ScenarioParser.list_scenarios(str(tmp_path))
    assert len(result) == 2
    names = [r["display_name"] for r in result]
    assert "試験1" in names
    assert "試験2" in names
    counts = {r["display_name"]: r["step_count"] for r in result}
    assert counts["試験2"] == 2
