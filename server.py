import contextlib
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route


class MCPAcceptHeaderMiddleware:
    """
    Some health-checkers or clients call the MCP endpoint without
    Accept: text/event-stream. This middleware makes the server tolerant.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = list(scope.get("headers", []))
            accept_index = None

            for index, (key, value) in enumerate(headers):
                if key.lower() == b"accept":
                    accept_index = index
                    break

            required_accept = b"application/json, text/event-stream"

            if accept_index is None:
                headers.append((b"accept", required_accept))
            else:
                current_accept = headers[accept_index][1]

                if b"text/event-stream" not in current_accept:
                    current_accept += b", text/event-stream"

                if b"application/json" not in current_accept:
                    current_accept += b", application/json"

                headers[accept_index] = (b"accept", current_accept)

            scope = dict(scope)
            scope["headers"] = headers

        await self.app(scope, receive, send)


mcp = FastMCP(
    name="ReceiptMCP",
    instructions="ReceiptMCP(영수증MCP) provides tools for receipt parsing and spending records.",
    stateless_http=True,
    json_response=True,
)


async def root(request):
    return JSONResponse(
        {
            "status": "ok",
            "service": "ReceiptMCP",
            "mcp_endpoint": "/mcp",
        }
    )


async def health(request):
    return JSONResponse(
        {
            "status": "healthy",
            "service": "ReceiptMCP",
        }
    )


@mcp.tool(
    name="health_check",
    description="Checks whether ReceiptMCP(영수증MCP) is running correctly.",
    annotations=ToolAnnotations(
        title="Health Check",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=False,
        idempotentHint=True,
    ),
)
def health_check() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "ReceiptMCP",
    }


@mcp.tool(
    name="analyze_receipt_text",
    description="Parses plain receipt text into simple structured rows for ReceiptMCP(영수증MCP).",
    annotations=ToolAnnotations(
        title="Analyze Receipt Text",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=False,
        idempotentHint=True,
    ),
)
def analyze_receipt_text(receipt_text: str) -> dict[str, Any]:
    lines = [line.strip() for line in receipt_text.splitlines() if line.strip()]

    return {
        "store_name": lines[0] if lines else None,
        "line_count": len(lines),
        "items": [
            {
                "line_no": index + 1,
                "text": line,
            }
            for index, line in enumerate(lines)
        ],
    }


@mcp.tool(
    name="format_receipt_table",
    description="Formats receipt text as a markdown table for ReceiptMCP(영수증MCP).",
    annotations=ToolAnnotations(
        title="Format Receipt Table",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=False,
        idempotentHint=True,
    ),
)
def format_receipt_table(receipt_text: str) -> str:
    lines = [line.strip() for line in receipt_text.splitlines() if line.strip()]

    if not lines:
        return "No receipt text was provided."

    table_lines = [
        "| No | Receipt line |",
        "|---:|---|",
    ]

    for index, line in enumerate(lines, start=1):
        safe_line = line.replace("|", "\\|")
        table_lines.append(f"| {index} | {safe_line} |")

    return "\n".join(table_lines)


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    async with mcp.session_manager.run():
        yield


mcp_http_app = MCPAcceptHeaderMiddleware(mcp.streamable_http_app())

app = Starlette(
    routes=[
        Route("/", root, methods=["GET"]),
        Route("/health", health, methods=["GET"]),
        Mount("/", app=mcp_http_app),
    ],
    lifespan=lifespan,
)
