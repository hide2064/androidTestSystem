from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MeasureResult:
    value: float
    unit: str
    raw: str = ""
    pass_: bool = True


class BaseDriver(ABC):
    """
    全ての機材ドライバが継承する基底クラス。
    新機材を追加する場合はこのクラスを継承し、
    connect / disconnect / send_command / measure を実装する。
    """

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self._connected = False

    # ─── 必須実装メソッド ───────────────────────────────────

    @abstractmethod
    def connect(self) -> None:
        """機材に接続する"""

    @abstractmethod
    def disconnect(self) -> None:
        """接続を切断する"""

    @abstractmethod
    def send_command(self, command: str) -> str:
        """生コマンドを送信して応答を返す（SCPI等）"""

    @abstractmethod
    def measure(self, parameter: str) -> MeasureResult:
        """
        測定値を取得する。
        parameter 例: "voltage_ch1", "rssi", "peak_power"
        """

    # ─── 共通メソッド（オーバーライド任意）──────────────────

    def reset(self) -> None:
        """機材をリセット（デフォルト: *RST コマンド）"""
        self.send_command("*RST")

    def get_id(self) -> str:
        """機材IDを取得（デフォルト: *IDN? コマンド）"""
        return self.send_command("*IDN?")

    def get_status(self) -> dict:
        """現在の接続状態を返す"""
        return {
            "name": self.name,
            "driver": self.__class__.__module__,
            "connected": self._connected,
            "description": self.config.get("description", ""),
        }

    @property
    def is_connected(self) -> bool:
        return self._connected

    def __repr__(self) -> str:
        status = "接続中" if self._connected else "未接続"
        return f"{self.__class__.__name__}[{self.name}] ({status})"
