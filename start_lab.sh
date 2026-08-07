#!/usr/bin/env bash
set -e

# Load environment variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo "============================================================"
echo "🚀 Starting VinBank Guardrails Red-Teaming Arena Stack"
echo "============================================================"

# Kill existing background processes on exit
cleanup() {
  echo ""
  echo "🛑 Shutting down processes..."
  kill $(jobs -p) 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 0. Kill any zombie process currently hogging port 3000 or 8000
echo "0️⃣ Cleaning up existing processes on ports 3000 & 8000..."
fuser -k 3000/tcp 2>/dev/null || true
fuser -k 8000/tcp 2>/dev/null || true
sleep 1

# 1. Start Python FastAPI Backend
echo "1️⃣ Starting FastAPI Backend on port 8000..."
uv run python src/api.py &
API_PID=$!

# 2. Start Next.js Frontend
echo "2️⃣ Starting Next.js Frontend on port 3000..."
cd frontend
pnpm dev --port 3000 &
FRONTEND_PID=$!
cd ..

# Wait for local servers to initialize
sleep 3

# 3. Start Cloudflare Tunnel using HTTP2 protocol (bypasses UDP/QUIC timeouts)
if [ -n "$CF_TUNNEL_TOKEN" ]; then
  echo "3️⃣ Exposing Frontend via Cloudflare Tunnel (HTTP2 mode)..."
  pnpm dlx cloudflared tunnel --protocol http2 run --token "$CF_TUNNEL_TOKEN"
else
  echo "⚠️ CF_TUNNEL_TOKEN not found in .env! Running locally only."
  echo "Local URL: http://localhost:3000"
  wait
fi
