"""
SharePointClient — Microsoft Graph API 経由でSharePointに試験結果を送信
"""
import logging
import os
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

TENANT_ID     = os.getenv("SHAREPOINT_TENANT_ID", "")
CLIENT_ID     = os.getenv("SHAREPOINT_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("SHAREPOINT_CLIENT_SECRET", "")
SITE_URL      = os.getenv("SHAREPOINT_SITE_URL", "")

TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class SharePointClient:

    def __init__(self):
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._site_id: Optional[str] = None
        self._list_id: Optional[str] = None

    # ─── 認証 ─────────────────────────────────────────────

    async def _get_token(self) -> str:
        """アクセストークンを取得（キャッシュあり）"""
        if self._token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._token

        if not all([TENANT_ID, CLIENT_ID, CLIENT_SECRET]):
            raise RuntimeError("SharePoint認証情報が設定されていません (.env を確認してください)")

        async with httpx.AsyncClient() as c:
            resp = await c.post(TOKEN_URL, data={
                "grant_type": "client_credentials",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "scope": "https://graph.microsoft.com/.default",
            })
            resp.raise_for_status()
            data = resp.json()

        self._token = data["access_token"]
        # expires_in は秒数、余裕を持って60秒早めに失効扱い
        from datetime import timedelta
        self._token_expiry = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
        return self._token

    async def _headers(self) -> dict:
        token = await self._get_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # ─── Site / List 解決 ────────────────────────────────

    async def _get_site_id(self) -> str:
        if self._site_id:
            return self._site_id
        # SITE_URL 例: https://contoso.sharepoint.com/sites/test
        # → hostname と path を分割
        from urllib.parse import urlparse
        parsed = urlparse(SITE_URL)
        hostname = parsed.hostname
        path = parsed.path.lstrip("/")
        async with httpx.AsyncClient() as c:
            resp = await c.get(
                f"{GRAPH_BASE}/sites/{hostname}:/{path}",
                headers=await self._headers()
            )
            resp.raise_for_status()
            self._site_id = resp.json()["id"]
        return self._site_id

    async def _get_list_id(self, list_name: str = "TestResults") -> str:
        if self._list_id:
            return self._list_id
        site_id = await self._get_site_id()
        async with httpx.AsyncClient() as c:
            resp = await c.get(
                f"{GRAPH_BASE}/sites/{site_id}/lists/{list_name}",
                headers=await self._headers()
            )
            if resp.status_code == 404:
                # リストが存在しなければ作成
                self._list_id = await self._create_list(site_id, list_name)
            else:
                resp.raise_for_status()
                self._list_id = resp.json()["id"]
        return self._list_id

    async def _create_list(self, site_id: str, list_name: str) -> str:
        """TestResults リストを自動作成する"""
        body = {
            "displayName": list_name,
            "columns": [
                {"name": "Scenario",   "text": {}},
                {"name": "DeviceId",   "text": {}},
                {"name": "TestSite",   "text": {}},
                {"name": "Result",     "text": {}},
                {"name": "PassCount",  "number": {}},
                {"name": "FailCount",  "number": {}},
                {"name": "Total",      "number": {}},
                {"name": "Timestamp",  "dateTime": {}},
                {"name": "Details",    "text": {"allowMultipleLines": True}},
            ],
            "list": {"template": "genericList"},
        }
        async with httpx.AsyncClient() as c:
            resp = await c.post(
                f"{GRAPH_BASE}/sites/{site_id}/lists",
                headers=await self._headers(),
                json=body
            )
            resp.raise_for_status()
            logger.info("SharePoint リスト '%s' を作成しました", list_name)
            return resp.json()["id"]

    # ─── 結果送信 ─────────────────────────────────────────

    async def send_result(self, summary: dict) -> None:
        """試験結果を SharePoint Lists に1行追加する"""
        import json
        site_id = await self._get_site_id()
        list_id = await self._get_list_id()

        item = {
            "fields": {
                "Title":      f"{summary['scenario']} / {summary['device_id']}",
                "Scenario":   summary["scenario"],
                "DeviceId":   summary["device_id"],
                "TestSite":   summary.get("test_site", ""),
                "Result":     summary["result"],
                "PassCount":  summary["pass_count"],
                "FailCount":  summary["fail_count"],
                "Total":      summary["total"],
                "Timestamp":  summary["timestamp"],
                "Details":    json.dumps(summary["steps"], ensure_ascii=False)[:4000],
            }
        }

        async with httpx.AsyncClient() as c:
            resp = await c.post(
                f"{GRAPH_BASE}/sites/{site_id}/lists/{list_id}/items",
                headers=await self._headers(),
                json=item
            )
            resp.raise_for_status()
            logger.info("SharePoint に結果を送信しました: %s", summary["result"])
