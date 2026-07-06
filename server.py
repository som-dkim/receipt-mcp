import contextlib
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route


mcp = FastMCP(
    name="ReceiptMCP",
    instructions="ReceiptMCP(영수증MCP) provides tools for receipt parsing and spending records.",
    stateless_http=True,
)


async def root(request):
    return JSONResponse(
        {
            "status": "ok",
            "service": "ReceiptMCP",
            "message": "ReceiptMCP server is running. MCP endpoint is /mcp.",
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
        idempotentHint=True,
        openWorldHint=False,
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
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def analyze_receipt_text(receipt_text: str) -> dict[str, Any]:
    lines = [line.strip() for line in receipt_text.splitlines() if line.strip()]

    return {
        "store_name": lines[0] if lines else None,
        "raw_text": receipt_text,
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
        idempotentHint=True,
        openWorldHint=False,
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


app = Starlette(
    routes=[
        Route("/", root, methods=["GET"]),
        Route("/health", health, methods=["GET"]),
        Mount("/", app=mcp.streamable_http_app()),
    ],
    lifespan=lifespan,
)
