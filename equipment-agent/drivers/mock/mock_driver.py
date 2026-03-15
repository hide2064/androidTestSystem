"""
モックドライバ — 実機なしで動作確認するためのダミー
config 例:
  mock_values:
    voltage_ch1: 3.7
    rssi: -55.0
"""
import sys
sys.path.insert(0, "/app")

import random
from base_driver import BaseDriver, MeasureResult


class Driver(BaseDriver):
    """テスト・CI用のモック機材ドライバ"""

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def send_command(self, command: str) -> str:
        if command == "*IDN?":
            return f"MOCK,{self.name},0001,1.0"
        if command == "*RST":
            return ""
        return f"MOCK_RESPONSE:{command}"

    def measure(self, parameter: str) -> MeasureResult:
        mock_values: dict = self.config.get("mock_values", {})
        if parameter in mock_values:
            base = mock_values[parameter]
        else:
            base = 0.0
        # 微小なランダムノイズを加えてリアルに見せる
        value = base + random.uniform(-0.05, 0.05) * abs(base + 1)
        return MeasureResult(value=round(value, 4), unit="mock", raw=str(value))
