"""
AdbClient — ホストPCのADB Serverを経由してAndroid端末を操作する
"""
import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

ADB_SERVER_HOST = os.getenv("ADB_SERVER_HOST", "host.docker.internal")
ADB_SERVER_PORT = os.getenv("ADB_SERVER_PORT", "5037")


def _adb(args: str, device_id: str | None = None) -> subprocess.CompletedProcess:
    """ADB コマンドを実行する共通関数"""
    base = f"adb -H {ADB_SERVER_HOST} -P {ADB_SERVER_PORT}"
    if device_id:
        base += f" -s {device_id}"
    cmd = f"{base} {args}"
    logger.debug("ADB: %s", cmd)
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)


class AdbClient:

    @staticmethod
    def list_devices() -> list[dict]:
        """接続中の端末一覧を返す"""
        result = _adb("devices -l")
        devices = []
        for line in result.stdout.splitlines()[1:]:
            line = line.strip()
            if not line or "offline" in line:
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                info = {"id": parts[0], "status": "online"}
                # model や product をパース
                for part in parts[2:]:
                    if ":" in part:
                        k, v = part.split(":", 1)
                        info[k] = v
                devices.append(info)
        return devices

    @staticmethod
    def shell(device_id: str, command: str) -> dict:
        """adb shell コマンドを実行する"""
        result = _adb(f"shell {command}", device_id)
        return {"stdout": result.stdout.strip(), "stderr": result.stderr.strip(),
                "returncode": result.returncode}

    @staticmethod
    def push(device_id: str, local_path: str, remote_path: str) -> dict:
        result = _adb(f"push {local_path} {remote_path}", device_id)
        return {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()}

    @staticmethod
    def pull(device_id: str, remote_path: str, local_path: str) -> dict:
        result = _adb(f"pull {remote_path} {local_path}", device_id)
        return {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()}

    @staticmethod
    def install(device_id: str, apk_path: str) -> dict:
        result = _adb(f"install -r {apk_path}", device_id)
        return {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()}

    @staticmethod
    def screencap(device_id: str, save_path: str) -> str:
        """スクリーンショットをホストに保存してパスを返す"""
        remote = "/sdcard/sc_tmp.png"
        _adb(f"shell screencap -p {remote}", device_id)
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        _adb(f"pull {remote} {save_path}", device_id)
        _adb(f"shell rm {remote}", device_id)
        return save_path

    @staticmethod
    def set_wifi(device_id: str, enabled: bool) -> None:
        val = "1" if enabled else "0"
        _adb(f"shell settings put global wifi_on {val}", device_id)

    @staticmethod
    def set_airplane_mode(device_id: str, enabled: bool) -> None:
        val = "1" if enabled else "0"
        _adb(f"shell settings put global airplane_mode_on {val}", device_id)
        # ブロードキャストで即時反映
        _adb(f"shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state {str(enabled).lower()}", device_id)

    @staticmethod
    def reboot(device_id: str) -> None:
        _adb("reboot", device_id)

    @staticmethod
    def get_logcat(device_id: str, lines: int = 200) -> str:
        result = _adb(f"logcat -d -t {lines}", device_id)
        return result.stdout

    @staticmethod
    def get_prop(device_id: str, prop: str) -> str:
        result = _adb(f"shell getprop {prop}", device_id)
        return result.stdout.strip()
