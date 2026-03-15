"""
汎用 REST API 機材ドライバ
HTTP GET/POST で制御する機材向け
config 例:
  base_url: "http://192.168.1.30:8080"
  measure_endpoints:
    voltage: "/measure/voltage"
    temperature: "/measure/temp"
  command_endpoint: "/command"
  value_key: "value"       # レスポンスJSONのどのキーを値として使うか
  unit_key: "unit"
"""
import sys
sys.path.insert(0, "/app")

from base_driver import BaseDriver, MeasureResult

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False


class Driver(BaseDriver):

    def connect(self) -> None:
        if not _REQUESTS_AVAILABLE:
            raise RuntimeError("requests がインストールされていません")
        self._base_url = self.config["base_url"].rstrip("/")
        self._timeout = self.config.get("timeout", 10)
        # 疎通確認
        resp = requests.get(f"{self._base_url}/status", timeout=self._timeout)
        resp.raise_for_status()
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def send_command(self, command: str) -> str:
        endpoint = self.config.get("command_endpoint", "/command")
        resp = requests.post(
            f"{self._base_url}{endpoint}",
            json={"command": command},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")

    def measure(self, parameter: str) -> MeasureResult:
        endpoints = self.config.get("measure_endpoints", {})
        if parameter not in endpoints:
            raise ValueError(f"未対応のパラメータ: {parameter}  config.measure_endpoints に定義してください")
        resp = requests.get(
            f"{self._base_url}{endpoints[parameter]}",
            timeout=self._timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        value_key = self.config.get("value_key", "value")
        unit_key = self.config.get("unit_key", "unit")
        return MeasureResult(
            value=float(data[value_key]),
            unit=data.get(unit_key, ""),
            raw=str(data),
        )
