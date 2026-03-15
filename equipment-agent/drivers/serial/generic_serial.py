"""
汎用シリアル通信ドライバ
RS-232C / USB-Serial 接続の機材に対応
config 例:
  port: "COM3"          # Linux: "/dev/ttyUSB0"
  baudrate: 9600
  timeout: 2
  terminator: "\\r\\n"
"""
import sys
sys.path.insert(0, "/app")

from base_driver import BaseDriver, MeasureResult

try:
    import serial
    _SERIAL_AVAILABLE = True
except ImportError:
    _SERIAL_AVAILABLE = False


class Driver(BaseDriver):

    def connect(self) -> None:
        if not _SERIAL_AVAILABLE:
            raise RuntimeError("pyserial がインストールされていません")
        self._serial = serial.Serial(
            port=self.config["port"],
            baudrate=self.config.get("baudrate", 9600),
            timeout=self.config.get("timeout", 2),
            bytesize=self.config.get("bytesize", 8),
            parity=self.config.get("parity", "N"),
            stopbits=self.config.get("stopbits", 1),
        )
        self._terminator = self.config.get("terminator", "\r\n")
        self._connected = True

    def disconnect(self) -> None:
        if self._connected and self._serial.is_open:
            self._serial.close()
            self._connected = False

    def send_command(self, command: str) -> str:
        tx = (command + self._terminator).encode()
        self._serial.write(tx)
        self._serial.flush()
        # レスポンスを読む（1行）
        response = self._serial.readline().decode(errors="replace").strip()
        return response

    def measure(self, parameter: str) -> MeasureResult:
        """
        config に measure_commands を定義して使う。
        例:
          measure_commands:
            voltage: "READ:VOLT?"
            temperature: "MEAS:TEMP?"
        """
        commands = self.config.get("measure_commands", {})
        if parameter not in commands:
            raise ValueError(f"未対応のパラメータ: {parameter}  config.measure_commands に定義してください")
        raw = self.send_command(commands[parameter])
        unit = self.config.get("units", {}).get(parameter, "")
        return MeasureResult(value=float(raw), unit=unit, raw=raw)
