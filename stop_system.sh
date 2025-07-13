#!/bin/bash

echo "🛑 Stopping all system components..."

# PIDファイルから既存のプロセスを殺す
if [ -f .websocket.pid ]; then
    WEBSOCKET_PID=$(cat .websocket.pid)
    if kill -0 $WEBSOCKET_PID 2>/dev/null; then
        kill $WEBSOCKET_PID
        echo "✅ WebSocket server stopped (PID: $WEBSOCKET_PID)"
    fi
    rm .websocket.pid
fi

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo "✅ Frontend stopped (PID: $FRONTEND_PID)"
    fi
    rm .frontend.pid
fi

if [ -f .monitoring.pid ]; then
    MONITORING_PID=$(cat .monitoring.pid)
    if kill -0 $MONITORING_PID 2>/dev/null; then
        kill $MONITORING_PID
        echo "✅ Monitoring system stopped (PID: $MONITORING_PID)"
    fi
    rm .monitoring.pid
fi

# 念のため、プロセス名でも殺す
echo "🔄 Killing any remaining processes..."

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

echo "🎉 All system components stopped successfully!" 