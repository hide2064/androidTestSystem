"""
AppiumClient — Appium Server を経由してAndroid端末のUIを操作する
"""
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

ADB_HOST = os.getenv("ADB_SERVER_HOST", "host.docker.internal")
ADB_PORT = os.getenv("ADB_SERVER_PORT", "5037")
APPIUM_URL = os.getenv("APPIUM_URL", "http://appium:4723")

try:
    from appium import webdriver
    from appium.webdriver.common.appiumby import AppiumBy
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    _APPIUM_AVAILABLE = True
except ImportError:
    _APPIUM_AVAILABLE = False
    logger.warning("Appium-Python-Client がインストールされていません")


# セッションを端末IDごとにキャッシュ
_sessions: dict[str, Any] = {}


def _get_driver(device_id: str, app_package: Optional[str] = None,
                app_activity: Optional[str] = None) -> Any:
    """指定端末のAppiumドライバを返す（セッション再利用）"""
    if not _APPIUM_AVAILABLE:
        raise RuntimeError("Appium-Python-Client がインストールされていません")

    if device_id in _sessions:
        return _sessions[device_id]

    caps = {
        "platformName": "Android",
        "udid": device_id,
        "automationName": "UiAutomator2",
        "adbHost": ADB_HOST,
        "adbPort": int(ADB_PORT),
        "noReset": True,
    }
    if app_package:
        caps["appPackage"] = app_package
    if app_activity:
        caps["appActivity"] = app_activity

    from appium.options import UiAutomator2Options
    options = UiAutomator2Options().load_capabilities(caps)
    driver = webdriver.Remote(APPIUM_URL, options=options)
    _sessions[device_id] = driver
    return driver


def _locator_by(locator_type: str, locator_value: str) -> tuple:
    """
    WebDriverWait 用の (By, value) タプルを返す。
    Appium 未インストール時は RuntimeError を送出する。
    """
    if not _APPIUM_AVAILABLE:
        raise RuntimeError("Appium が利用できません")

    type_map = {
        "id":    AppiumBy.ID,
        "text":  AppiumBy.ANDROID_UIAUTOMATOR,
        "xpath": AppiumBy.XPATH,
        "class": AppiumBy.CLASS_NAME,
        "desc":  AppiumBy.ACCESSIBILITY_ID,
    }
    by = type_map.get(locator_type)
    if by is None:
        raise ValueError(f"未知のロケータータイプ: {locator_type}  有効: {list(type_map)}")

    if locator_type == "text":
        locator_value = f'new UiSelector().text("{locator_value}")'

    return by, locator_value


class AppiumClient:

    @staticmethod
    def start_session(device_id: str, app_package: str, app_activity: str) -> dict:
        _get_driver(device_id, app_package, app_activity)
        return {"status": "session_started", "device_id": device_id}

    @staticmethod
    def close_session(device_id: str) -> None:
        if device_id in _sessions:
            try:
                _sessions[device_id].quit()
            except Exception:
                pass
            del _sessions[device_id]

    @staticmethod
    def tap(device_id: str, locator_type: str, locator_value: str,
            wait_sec: float = 10) -> dict:
        """要素をタップする（WebDriverWait で出現を待機してからタップ）"""
        driver = _get_driver(device_id)
        by, value = _locator_by(locator_type, locator_value)
        element = WebDriverWait(driver, wait_sec).until(
            EC.presence_of_element_located((by, value))
        )
        element.click()
        return {"status": "tapped"}

    @staticmethod
    def input_text(device_id: str, locator_type: str, locator_value: str,
                   text: str) -> dict:
        """要素にテキストを入力する"""
        driver = _get_driver(device_id)
        by, value = _locator_by(locator_type, locator_value)
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((by, value))
        )
        element.clear()
        element.send_keys(text)
        return {"status": "text_input"}

    @staticmethod
    def get_text(device_id: str, locator_type: str, locator_value: str,
                 wait_sec: float = 10) -> str:
        """要素のテキストを取得する"""
        driver = _get_driver(device_id)
        by, value = _locator_by(locator_type, locator_value)
        element = WebDriverWait(driver, wait_sec).until(
            EC.presence_of_element_located((by, value))
        )
        return element.text

    @staticmethod
    def exists(device_id: str, locator_type: str, locator_value: str) -> bool:
        """要素が存在するか確認する"""
        driver = _get_driver(device_id)
        try:
            by, value = _locator_by(locator_type, locator_value)
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except Exception:
            return False

    @staticmethod
    def get_screenshot_base64(device_id: str) -> str:
        """スクリーンショットをBase64で返す"""
        driver = _get_driver(device_id)
        return driver.get_screenshot_as_base64()
