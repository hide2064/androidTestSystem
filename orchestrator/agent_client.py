"""
AgentClient — Android Agent / Equipment Agent との HTTP通信
"""
import os
import httpx

ANDROID_AGENT_URL = os.getenv("ANDROID_AGENT_URL", "http://android-agent:5000")
EQUIPMENT_AGENT_URL = os.getenv("EQUIPMENT_AGENT_URL", "http://equipment-agent:5001")

TIMEOUT = 30.0


class AndroidAgentClient:

    async def adb_command(self, device_id: str, command: str) -> str:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            resp = await c.post(f"{ANDROID_AGENT_URL}/adb/command",
                                json={"device_id": device_id, "command": command})
            resp.raise_for_status()
            return resp.json().get("stdout", "")

    async def tap(self, device_id: str, locator_type: str, locator_value: str) -> dict:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            resp = await c.post(f"{ANDROID_AGENT_URL}/appium/tap",
                                json={"device_id": device_id,
                                      "locator_type": locator_type,
                                      "locator_value": locator_value})
            resp.raise_for_status()
            return resp.json()

    async def input_text(self, device_id: str, locator_type: str,
                         locator_value: str, text: str) -> dict:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            resp = await c.post(f"{ANDROID_AGENT_URL}/appium/input_text",
                                json={"device_id": device_id,
                                      "locator_type": locator_type,
                                      "locator_value": locator_value,
                                      "text": text})
            resp.raise_for_status()
            return resp.json()

    async def get_text(self, device_id: str, locator_type: str, locator_value: str) -> str:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            resp = await c.get(f"{ANDROID_AGENT_URL}/appium/get_text",
                               params={"device_id": device_id,
                                       "locator_type": locator_type,
                                       "locator_value": locator_value})
            resp.raise_for_status()
            return resp.json().get("text", "")

    async def assert_exists(self, device_id: str, locator_type: str, locator_value: str) -> bool:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            resp = await c.get(f"{ANDROID_AGENT_URL}/appium/exists",
                               params={"device_id": device_id,
                                       "locator_type": locator_type,
                                       "locator_value": locator_value})
            resp.raise_for_status()
            return resp.json().get("exists", False)

    async def screenshot(self, device_id: str, save_path: str) -> str:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            resp = await c.post(f"{ANDROID_AGENT_URL}/adb/screenshot",
                                json={"device_id": device_id, "save_path": save_path})
            resp.raise_for_status()
            return resp.json().get("path", "")

    async def list_devices(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            resp = await c.get(f"{ANDROID_AGENT_URL}/devices")
            resp.raise_for_status()
            return resp.json()


class EquipmentAgentClient:

    async def measure(self, instrument: str, parameter: str) -> dict:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            resp = await c.get(f"{EQUIPMENT_AGENT_URL}/instruments/{instrument}/measure/{parameter}")
            resp.raise_for_status()
            return resp.json()

    async def call_method(self, instrument: str, method: str, kwargs: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            resp = await c.post(f"{EQUIPMENT_AGENT_URL}/instruments/{instrument}/method",
                                json={"method": method, "kwargs": kwargs or {}})
            resp.raise_for_status()
            return resp.json()

    async def send_command(self, instrument: str, command: str) -> str:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            resp = await c.post(f"{EQUIPMENT_AGENT_URL}/instruments/{instrument}/command",
                                json={"command": command})
            resp.raise_for_status()
            return resp.json().get("response", "")

    async def list_instruments(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            resp = await c.get(f"{EQUIPMENT_AGENT_URL}/instruments")
            resp.raise_for_status()
            return resp.json()
