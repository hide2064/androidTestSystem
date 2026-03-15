"""
Android Agent — FastAPI エントリーポイント
ADB + Appium を REST API として公開する
"""
import logging
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from adb_client import AdbClient
from appium_client import AppiumClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="Android Agent", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ─── リクエストモデル ───────────────────────────────────────

class AdbCommandRequest(BaseModel):
    device_id: str
    command: str

class AdbScreenshotRequest(BaseModel):
    device_id: str
    save_path: str = "/app/results/screenshot.png"

class AppiumSessionRequest(BaseModel):
    device_id: str
    app_package: str
    app_activity: str

class AppiumTapRequest(BaseModel):
    device_id: str
    locator_type: str   # id / text / xpath / class / desc
    locator_value: str

class AppiumInputRequest(BaseModel):
    device_id: str
    locator_type: str
    locator_value: str
    text: str


# ─── ヘルスチェック ────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


# ─── 端末一覧 ─────────────────────────────────────────────

@app.get("/devices")
def list_devices():
    """ADB で認識している端末一覧を返す"""
    try:
        return AdbClient.list_devices()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── ADB エンドポイント ────────────────────────────────────

@app.post("/adb/command")
def adb_command(req: AdbCommandRequest):
    """ADB shell コマンドを実行する"""
    try:
        return AdbClient.shell(req.device_id, req.command)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/adb/screenshot")
def adb_screenshot(req: AdbScreenshotRequest):
    """スクリーンショットを取得してローカルに保存する"""
    try:
        path = AdbClient.screencap(req.device_id, req.save_path)
        return {"path": path, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/adb/reboot")
def adb_reboot(req: AdbCommandRequest):
    """端末を再起動する"""
    try:
        AdbClient.reboot(req.device_id)
        return {"status": "rebooting"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/adb/logcat")
def adb_logcat(device_id: str, lines: int = 200):
    """直近のlogcatを返す"""
    try:
        log = AdbClient.get_logcat(device_id, lines)
        return {"logcat": log}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/adb/prop")
def adb_prop(device_id: str, prop: str):
    """端末のプロパティを取得する（例: ro.product.model）"""
    try:
        return {"value": AdbClient.get_prop(device_id, prop)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Appium エンドポイント ─────────────────────────────────

@app.post("/appium/session/start")
def appium_start_session(req: AppiumSessionRequest):
    """Appiumセッションを開始する"""
    try:
        return AppiumClient.start_session(
            req.device_id, req.app_package, req.app_activity
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/appium/session/close")
def appium_close_session(device_id: str):
    """Appiumセッションを終了する"""
    try:
        AppiumClient.close_session(device_id)
        return {"status": "closed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/appium/tap")
def appium_tap(req: AppiumTapRequest):
    """要素をタップする"""
    try:
        return AppiumClient.tap(req.device_id, req.locator_type, req.locator_value)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/appium/input_text")
def appium_input_text(req: AppiumInputRequest):
    """要素にテキストを入力する"""
    try:
        return AppiumClient.input_text(
            req.device_id, req.locator_type, req.locator_value, req.text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/appium/get_text")
def appium_get_text(device_id: str, locator_type: str, locator_value: str):
    """要素のテキストを取得する"""
    try:
        text = AppiumClient.get_text(device_id, locator_type, locator_value)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/appium/exists")
def appium_exists(device_id: str, locator_type: str, locator_value: str):
    """要素が存在するか確認する"""
    try:
        exists = AppiumClient.exists(device_id, locator_type, locator_value)
        return {"exists": exists}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
