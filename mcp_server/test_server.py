#!/usr/bin/env python3
"""
Minimal MCP server test
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("test")

@mcp.resource("test://hello")
def get_hello() -> str:
    """Test resource"""
    return "Hello from ADNI MCP!"

@mcp.tool()
def test_tool(message: str) -> str:
    """Test tool"""
    return f"You said: {message}"

if __name__ == "__main__":
    mcp.run()


