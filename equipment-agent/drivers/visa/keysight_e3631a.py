"""
Keysight E3631A 三出力電源ドライバ
接続方式: VISA (GPIB / USB / LAN)
config 例:
  address: "GPIB0::5::INSTR"
"""
import sys
sys.path.insert(0, "/app")

from base_driver import BaseDriver, MeasureResult

try:
    import pyvisa
    _PYVISA_AVAILABLE = True
except ImportError:
    _PYVISA_AVAILABLE = False


# チャンネル定義
_CHANNELS = {
    1: "P6V",
    2: "P25V",
    3: "N25V",
}

_MEASURE_MAP = {
    "voltage_ch1": (1, "MEAS:VOLT?", "V"),
    "current_ch1": (1, "MEAS:CURR?", "A"),
    "voltage_ch2": (2, "MEAS:VOLT?", "V"),
    "current_ch2": (2, "MEAS:CURR?", "A"),
    "voltage_ch3": (3, "MEAS:VOLT?", "V"),
    "current_ch3": (3, "MEAS:CURR?", "A"),
}


class Driver(BaseDriver):

    def connect(self) -> None:
        if not _PYVISA_AVAILABLE:
            raise RuntimeError("pyvisa がインストールされていません")
        rm = pyvisa.ResourceManager()
        address = self.config["address"]
        self._inst = rm.open_resource(address)
        self._inst.timeout = self.config.get("timeout_ms", 5000)
        self._connected = True

    def disconnect(self) -> None:
        if self._connected:
            self._inst.close()
            self._connected = False

    def send_command(self, command: str) -> str:
        if "?" in command:
            return self._inst.query(command).strip()
        self._inst.write(command)
        return ""

    def measure(self, parameter: str) -> MeasureResult:
        if parameter not in _MEASURE_MAP:
            raise ValueError(f"未対応のパラメータ: {parameter}  対応: {list(_MEASURE_MAP)}")
        ch, query, unit = _MEASURE_MAP[parameter]
        self.send_command(f"INST {_CHANNELS[ch]}")
        raw = self.send_command(query)
        return MeasureResult(value=float(raw), unit=unit, raw=raw)

    # ─── 機材固有メソッド ─────────────────────────────────

    def set_voltage(self, channel: int, voltage: float) -> None:
        """指定チャンネルの電圧を設定する (channel: 1-3)"""
        self.send_command(f"INST {_CHANNELS[channel]}")
        self.send_command(f"VOLT {voltage:.4f}")

    def set_current_limit(self, channel: int, current: float) -> None:
        """電流リミットを設定する"""
        self.send_command(f"INST {_CHANNELS[channel]}")
        self.send_command(f"CURR {current:.4f}")

    def output_on(self) -> None:
        self.send_command("OUTP ON")

    def output_off(self) -> None:
        self.send_command("OUTP OFF")
