# tools/stitch_client.py
import httpx
import os
import traceback


class StitchMCPClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("STITCH_API_KEY")
        if not self.api_key:
            raise ValueError("STITCH_API_KEY is required. Set it in .env or pass it explicitly.")
        self.url = "https://stitch.googleapis.com/mcp"
        self.headers = {
            "X-Goog-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }
        self.request_id = 1

    async def _request(self, method: str, params: dict) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params,
        }
        self.request_id += 1
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(self.url, headers=self.headers, json=payload)
                if response.status_code != 200:
                    print(f"[Stitch HTTP ERROR] {response.status_code}: {response.text}")
                    return {}
                return response.json()
            except Exception:
                traceback.print_exc()
                return {}

    async def call_tool(self, name: str, arguments: dict) -> dict:
        return await self._request("tools/call", {"name": name, "arguments": arguments})
