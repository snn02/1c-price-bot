import asyncio
import json
import logging
from typing import Any

from price_bot.common.config import Settings
from price_bot.common.exceptions import MCPError
from price_bot.common.types import Product, QuoteResult, QuoteItem

logger = logging.getLogger(__name__)


class McpClient:
    def __init__(self, settings: Settings) -> None:
        self._server_path = settings.mcp_server_path
        self._process: asyncio.subprocess.Process | None = None
        self._alive = False
        self._lock = asyncio.Lock()
        self._request_id = 0

    async def start(self) -> None:
        await self._ensure_alive()

    async def stop(self) -> None:
        if self._process and self._process.returncode is None:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._process.kill()
        self._process = None
        self._alive = False

    async def _ensure_alive(self) -> None:
        async with self._lock:
            if self._alive and self._process and self._process.returncode is None:
                return
            await self._start_process()

    async def _start_process(self) -> None:
        try:
            self._process = await asyncio.create_subprocess_exec(
                self._server_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self._alive = True
            await self._initialize()
        except (FileNotFoundError, OSError) as exc:
            self._alive = False
            raise MCPError(f"Failed to start MCP server: {exc}") from exc

    async def _initialize(self) -> None:
        """Send MCP initialize handshake."""
        init_request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "price-bot", "version": "1.0.0"},
            },
        }
        await self._send(init_request)
        await self._recv()
        notify = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
        await self._send(notify)

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    async def _send(self, data: dict) -> None:
        assert self._process and self._process.stdin
        payload = json.dumps(data) + "\n"
        self._process.stdin.write(payload.encode())
        await self._process.stdin.drain()

    async def _recv(self) -> dict:
        assert self._process and self._process.stdout
        while True:
            line = await asyncio.wait_for(self._process.stdout.readline(), timeout=30)
            if not line:
                raise MCPError("MCP server closed connection")
            text = line.decode().strip()
            if not text:
                continue
            return json.loads(text)

    async def _call_tool(self, name: str, arguments: dict) -> Any:
        await self._ensure_alive()
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
        try:
            await self._send(request)
            response = await self._recv()
        except Exception as exc:
            self._alive = False
            raise MCPError(f"MCP call failed: {exc}") from exc

        if "error" in response:
            raise MCPError(f"MCP error: {response['error']}")

        result = response.get("result", {})
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            return json.loads(content[0]["text"])
        return result

    async def search_products(self, query: str, limit: int = 10) -> list[Product]:
        data = await self._call_tool("search_products", {"query": query, "limit": limit})
        items = data.get("items", [])
        return [
            Product(
                code=item["code"],
                name=item["name"],
                price_retail=float(item["price_retail"]),
                vat=item["vat"],
            )
            for item in items
        ]

    async def get_product(self, code: str) -> Product | None:
        try:
            data = await self._call_tool("get_product", {"code": code})
        except MCPError:
            return None
        if not data or not data.get("code"):
            return None
        return Product(
            code=data["code"],
            name=data["name"],
            price_retail=float(data["price_retail"]),
            vat=data["vat"],
        )

    async def build_quote(self, items: list[dict]) -> QuoteResult:
        data = await self._call_tool("build_quote", {"items": items})
        result_items = []
        for item in data.get("items", []):
            result_items.append(
                QuoteItem(
                    id=0,
                    quote_draft_id=0,
                    source_query=item.get("name", ""),
                    qty=item.get("qty", 1),
                    status="selected",
                    selected_product_code=item.get("code"),
                    selected_product_name=item.get("name"),
                    price_retail=float(item.get("price_retail", 0)),
                    vat=item.get("vat"),
                    line_sum=float(item.get("line_sum", 0)),
                )
            )
        return QuoteResult(items=result_items, total_sum=float(data.get("total_sum", 0)))

    async def refresh_prices(self) -> str:
        data = await self._call_tool("refresh_prices", {})
        return data.get("message", data.get("status", "Готово"))
