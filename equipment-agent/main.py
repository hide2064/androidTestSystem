"""
Equipment Agent — FastAPI エントリーポイント
Orchestrator から REST API で呼ばれる
"""
import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import EquipmentAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="Equipment Agent", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

agent = EquipmentAgent()


# ─── リクエストモデル ───────────────────────────────────────

class CommandRequest(BaseModel):
    command: str

class MethodRequest(BaseModel):
    method: str
    kwargs: dict[str, Any] = {}


# ─── エンドポイント ────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/instruments")
def list_instruments():
    """接続設定されている機材の一覧と接続状態を返す"""
    return agent.list_instruments()

@app.post("/instruments/{name}/connect")
def connect(name: str):
    try:
        agent.connect(name)
        return {"status": "connected", "name": name}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/instruments/connect_all")
def connect_all():
    """全機材に接続を試みる"""
    return agent.connect_all()

@app.post("/instruments/{name}/disconnect")
def disconnect(name: str):
    try:
        agent.disconnect(name)
        return {"status": "disconnected", "name": name}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/instruments/{name}/command")
def send_command(name: str, req: CommandRequest):
    """生コマンドを送信して応答を返す（SCPIコマンド等）"""
    try:
        result = agent.send_command(name, req.command)
        return {"response": result}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/instruments/{name}/measure/{parameter}")
def measure(name: str, parameter: str):
    """指定パラメータを測定して値を返す"""
    try:
        return agent.measure(name, parameter)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/instruments/{name}/method")
def call_method(name: str, req: MethodRequest):
    """ドライバ固有メソッドを呼ぶ（set_voltage, output_on 等）"""
    try:
        result = agent.call_method(name, req.method, req.kwargs)
        return {"result": result}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AttributeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/instruments/{name}/reset")
def reset(name: str):
    try:
        agent.reset(name)
        return {"status": "reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/instruments/{name}/id")
def get_id(name: str):
    try:
        return {"id": agent.get_id(name)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
