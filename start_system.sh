#!/bin/bash

# 既存のプロセスを殺す
echo "🔄 Killing existing processes..."

# WebSocketサーバーを殺す
pkill -f "start_websocket_server.py"
pkill -f "websocket_server.py"

# フロントエンドプロセスを殺す (npm run dev)
pkill -f "vite"
pkill -f "npm run dev"

# モニタリングシステムを殺す
pkill -f "continuous_monitoring.py"

# Pythonプロセスの中でparental-control関連を殺す
pkill -f "parental-control"

echo "✅ Existing processes killed"

# 少し待機
sleep 2

echo "🚀 Starting all system components..."

# プロジェクトルートに移動
cd "$(dirname "$0")"

# WebSocketサーバー起動（バックグラウンド）
echo "📡 Starting WebSocket server..."
cd src
python start_websocket_server.py &
WEBSOCKET_PID=$!
echo "WebSocket server started with PID: $WEBSOCKET_PID"

# フロントエンド起動（バックグラウンド）
echo "🌐 Starting frontend..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

# モニタリングシステム起動（バックグラウンド）
echo "👁️ Starting monitoring system..."
cd ../src
python continuous_monitoring.py &
MONITORING_PID=$!
echo "Monitoring system started with PID: $MONITORING_PID"

echo ""
echo "🎉 All systems started successfully!"
echo "📡 WebSocket server: http://localhost:8080"
echo "🌐 Frontend: http://localhost:5173"
echo "👁️ Monitoring system: Running in background"
echo ""
echo "To stop all processes, run: ./stop_system.sh"
echo "Or press Ctrl+C to stop this script and all background processes"

# プロセスIDを保存
echo "$WEBSOCKET_PID" > .websocket.pid
echo "$FRONTEND_PID" > .frontend.pid
echo "$MONITORING_PID" > .monitoring.pid

# スクリプトが終了するまで待機
wait 