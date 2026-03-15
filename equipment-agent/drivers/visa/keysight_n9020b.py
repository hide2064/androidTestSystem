"""
Keysight N9020B MXA スペクトラムアナライザ ドライバ
接続方式: VISA (GPIB / LAN)
config 例:
  address: "TCPIP0::192.168.1.20::inst0::INSTR"
"""
import sys
sys.path.insert(0, "/app")

from base_driver import BaseDriver, MeasureResult

try:
    import pyvisa
    _PYVISA_AVAILABLE = True
except ImportError:
    _PYVISA_AVAILABLE = False


class Driver(BaseDriver):

    def connect(self) -> None:
        if not _PYVISA_AVAILABLE:
            raise RuntimeError("pyvisa がインストールされていません")
        rm = pyvisa.ResourceManager()
        self._inst = rm.open_resource(self.config["address"])
        self._inst.timeout = self.config.get("timeout_ms", 10000)
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
        handlers = {
            "peak_power":    self._measure_peak_power,
            "channel_power": self._measure_channel_power,
            "center_freq":   self._measure_center_freq,
        }
        if parameter not in handlers:
            raise ValueError(f"未対応のパラメータ: {parameter}  対応: {list(handlers)}")
        return handlers[parameter]()

    # ─── 機材固有メソッド ─────────────────────────────────

    def _measure_peak_power(self) -> MeasureResult:
        self.send_command(":CALC:MARK1:MAX")
        raw = self.send_command(":CALC:MARK1:Y?")
        return MeasureResult(value=float(raw), unit="dBm", raw=raw)

    def _measure_channel_power(self) -> MeasureResult:
        raw = self.send_command(":READ:CHP?").split(",")[0]
        return MeasureResult(value=float(raw), unit="dBm", raw=raw)

    def _measure_center_freq(self) -> MeasureResult:
        raw = self.send_command(":SENS:FREQ:CENT?")
        return MeasureResult(value=float(raw), unit="Hz", raw=raw)

    def set_center_frequency(self, freq_hz: float) -> None:
        self.send_command(f":SENS:FREQ:CENT {freq_hz:.0f}")

    def set_span(self, span_hz: float) -> None:
        self.send_command(f":SENS:FREQ:SPAN {span_hz:.0f}")

    def set_rbw(self, rbw_hz: float) -> None:
        self.send_command(f":SENS:BWID:RES {rbw_hz:.0f}")

    def capture_trace(self) -> list[float]:
        """現在のトレースデータをリストで返す"""
        raw = self.send_command(":TRAC:DATA? TRACE1")
        return [float(v) for v in raw.split(",")]
