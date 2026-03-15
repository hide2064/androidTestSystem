"""
EquipmentAgent — プラグインローダー & 機材マネージャー
YAMLを読み込み、ドライバを動的にロードして管理する。
新機材追加時にこのファイルを変更する必要はない。
"""
import importlib
import logging
from pathlib import Path

import yaml

from base_driver import BaseDriver, MeasureResult

logger = logging.getLogger(__name__)


class EquipmentAgent:

    def __init__(self, config_path: str = "config/equipment.yaml"):
        self._drivers: dict[str, BaseDriver] = {}
        self._load_config(config_path)

    # ─── 初期化 ────────────────────────────────────────────

    def _load_config(self, config_path: str) -> None:
        path = Path(config_path)
        if not path.exists():
            logger.warning("equipment.yaml が見つかりません: %s", config_path)
            return

        with open(path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        for name, inst_config in (config.get("instruments") or {}).items():
            driver_path = inst_config["driver"]  # 例: "visa.keysight_e3631a"
            try:
                module = importlib.import_module(f"drivers.{driver_path}")
                driver_class = module.Driver
                self._drivers[name] = driver_class(name=name, config=inst_config)
                logger.info("ドライバをロード: %s -> %s", name, driver_path)
            except Exception as exc:
                logger.error("ドライバのロードに失敗: %s (%s): %s", name, driver_path, exc)

    # ─── 外部API (FastAPI から呼ばれる) ──────────────────

    def list_instruments(self) -> list[dict]:
        return [d.get_status() for d in self._drivers.values()]

    def connect(self, name: str) -> None:
        driver = self._get(name)
        driver.connect()
        logger.info("接続: %s", name)

    def connect_all(self) -> dict[str, str]:
        """全機材に接続を試みる。結果を名前→"ok"/"error:..." で返す"""
        results = {}
        for name in self._drivers:
            try:
                self._drivers[name].connect()
                results[name] = "ok"
            except Exception as e:
                results[name] = f"error: {e}"
        return results

    def disconnect(self, name: str) -> None:
        self._get(name).disconnect()

    def send_command(self, name: str, command: str) -> str:
        return self._get(name).send_command(command)

    def measure(self, name: str, parameter: str) -> dict:
        result: MeasureResult = self._get(name).measure(parameter)
        return {"value": result.value, "unit": result.unit, "raw": result.raw}

    def call_method(self, name: str, method: str, kwargs: dict) -> any:
        """ドライバ固有メソッドを呼ぶ（set_voltage, output_on 等）"""
        driver = self._get(name)
        func = getattr(driver, method, None)
        if func is None:
            raise AttributeError(f"ドライバ '{name}' にメソッド '{method}' が存在しません")
        return func(**kwargs)

    def reset(self, name: str) -> None:
        self._get(name).reset()

    def get_id(self, name: str) -> str:
        return self._get(name).get_id()

    # ─── 内部ヘルパー ──────────────────────────────────────

    def _get(self, name: str) -> BaseDriver:
        if name not in self._drivers:
            raise KeyError(f"機材 '{name}' が設定に存在しません。利用可能: {list(self._drivers)}")
        return self._drivers[name]
