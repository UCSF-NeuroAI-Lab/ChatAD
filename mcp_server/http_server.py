#!/usr/bin/env python3
"""
ADNI MCP HTTP Server - Exposes the MCP server over HTTP/SSE for remote access
Deploy to Railway or any cloud platform with: uvicorn mcp_server.http_server:app
"""

import os
import sys

# Add parent directory to path to import server module
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI
from mcp_server.server import mcp
import uvicorn

# Create FastAPI app and mount MCP SSE endpoint
app = FastAPI(
    title="ChatAD MCP Server",
    description="ADNI documentation catalog and PDF content as MCP resources",
    version="0.1.0"
)

# Mount the MCP SSE app at root
app.mount("/", mcp.sse_app())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting ChatAD MCP Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
