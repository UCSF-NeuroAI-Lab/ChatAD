#!/bin/bash

cd "$(dirname "$0")"

uv run python mcp_server/http_server.py &
sleep 2
ngrok http --domain=chatad.ngrok.app 8000

