from mcp.server.fastmcp import FastMCP

mcp = FastMCP("receipt-mcp")


@mcp.tool()
def hello(name: str) -> str:
    """
    테스트용 MCP 도구입니다.
    """
    return f"안녕하세요, {name}님. MCP 서버가 정상 동작합니다."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
