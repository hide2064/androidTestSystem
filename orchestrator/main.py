"""
Orchestrator — FastAPI エントリーポイント
"""
import asyncio
import logging

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scenario_parser import ScenarioParser
from scenario_runner import ScenarioRunner
from state_manager import StateManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="Test Orchestrator", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

state = StateManager()
runner = ScenarioRunner(state)


# ─── リクエストモデル ───────────────────────────────────────

class StartTestRequest(BaseModel):
    scenario_name: str
    device_id: str


# ─── REST API ─────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/scenarios")
def list_scenarios():
    """利用可能な試験シナリオ一覧"""
    return ScenarioParser.list_scenarios()

@app.post("/test/start")
async def start_test(req: StartTestRequest):
    """試験を開始する"""
    if state.is_running():
        raise HTTPException(status_code=409, detail="試験が既に実行中です")
    asyncio.create_task(runner.run(req.scenario_name, req.device_id))
    return {"status": "started",
            "scenario": req.scenario_name,
            "device_id": req.device_id}

@app.post("/test/stop")
def stop_test():
    """実行中の試験を中断する"""
    if not state.is_running():
        raise HTTPException(status_code=400, detail="試験は実行中ではありません")
    state.request_stop()
    return {"status": "stop_requested"}

@app.get("/test/status")
def get_status():
    """現在の試験状態を返す"""
    return state.get_status()

@app.get("/results")
def get_results(limit: int = 20):
    """直近の試験結果一覧"""
    return state.list_results(limit)

@app.get("/devices")
async def list_devices():
    """接続中のAndroid端末一覧（Android Agentに問い合わせ）"""
    from agent_client import AndroidAgentClient
    try:
        return await AndroidAgentClient().list_devices()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Android Agentに接続できません: {e}")

@app.get("/instruments")
async def list_instruments():
    """接続中の計測器一覧（Equipment Agentに問い合わせ）"""
    from agent_client import EquipmentAgentClient
    try:
        return await EquipmentAgentClient().list_instruments()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Equipment Agentに接続できません: {e}")


# ─── WebSocket（リアルタイムログ）─────────────────────────

@app.websocket("/ws/log")
async def websocket_log(websocket: WebSocket):
    """ブラウザにリアルタイムでログを送信する"""
    await websocket.accept()
    try:
        while True:
            log_entry = await state.log_queue.get()
            await websocket.send_json(log_entry)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
