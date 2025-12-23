#!/bin/bash
# Start ADNI MCP HTTP Server for ChatGPT Desktop

echo "🚀 Starting ADNI MCP HTTP Server..."
echo ""

cd "$(dirname "$0")"

# Start the HTTP server
uv run python mcp_server/http_server.py

