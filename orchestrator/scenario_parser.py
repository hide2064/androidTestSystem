"""
ScenarioParser — YAMLシナリオファイルの読み込みとバリデーション
"""
import glob
from pathlib import Path
from typing import Any

import yaml


REQUIRED_STEP_KEYS = {"id", "description", "action"}
VALID_ACTIONS = {"adb", "tap", "input_text", "assert_text", "assert_exists",
                 "equipment_measure", "equipment_method", "equipment_command",
                 "wait", "screenshot"}


class ScenarioParser:

    @staticmethod
    def load(scenario_path: str) -> dict:
        """YAMLファイルを読み込んでバリデーションする"""
        path = Path(scenario_path)
        if not path.exists():
            raise FileNotFoundError(f"シナリオファイルが見つかりません: {scenario_path}")

        with open(path, encoding="utf-8") as f:
            scenario = yaml.safe_load(f)

        ScenarioParser._validate(scenario, scenario_path)
        return scenario

    @staticmethod
    def _validate(scenario: dict, path: str) -> None:
        if "name" not in scenario:
            raise ValueError(f"[{path}] 'name' フィールドが必要です")
        if "steps" not in scenario or not isinstance(scenario["steps"], list):
            raise ValueError(f"[{path}] 'steps' リストが必要です")

        for step in scenario["steps"]:
            missing = REQUIRED_STEP_KEYS - set(step.keys())
            if missing:
                raise ValueError(f"[{path}] step id={step.get('id', '?')} に必須キーがありません: {missing}")
            action = step["action"]
            if action not in VALID_ACTIONS:
                raise ValueError(f"[{path}] 未知の action: '{action}'  有効: {VALID_ACTIONS}")

    @staticmethod
    def list_scenarios(scenarios_dir: str = "scenarios") -> list[dict]:
        """シナリオ一覧を返す"""
        result = []
        for filepath in sorted(glob.glob(f"{scenarios_dir}/*.yaml")):
            try:
                with open(filepath, encoding="utf-8") as f:
                    sc = yaml.safe_load(f)
                result.append({
                    "name": Path(filepath).stem,
                    "display_name": sc.get("name", Path(filepath).stem),
                    "description": sc.get("description", ""),
                    "version": sc.get("version", ""),
                    "step_count": len(sc.get("steps", [])),
                })
            except Exception as e:
                result.append({"name": Path(filepath).stem, "error": str(e)})
        return result
