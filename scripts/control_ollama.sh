#!/bin/bash
# Easy Ollama control script

case "$1" in
    start)
        echo "Starting Ollama..."
        ollama serve > /dev/null 2>&1 &
        sleep 2
        if pgrep -x ollama > /dev/null; then
            echo "✓ Ollama started (PID: $(pgrep -x ollama))"
        else
            echo "✗ Failed to start Ollama"
            exit 1
        fi
        ;;
    stop)
        echo "Stopping Ollama..."
        pkill -9 ollama
        sleep 1
        if pgrep -x ollama > /dev/null; then
            echo "✗ Some Ollama processes still running"
            sudo pkill -9 ollama 2>/dev/null
            sleep 1
        fi
        if ! pgrep -x ollama > /dev/null; then
            echo "✓ Ollama stopped"
        else
            echo "✗ Failed to stop all Ollama processes"
            echo "Run: sudo pkill -9 ollama"
            exit 1
        fi
        ;;
    status)
        if pgrep -x ollama > /dev/null; then
            echo "✓ Ollama is running"
            ps aux | grep ollama | grep -v grep
        else
            echo "✗ Ollama is not running"
        fi
        ;;
    restart)
        $0 stop
        sleep 1
        $0 start
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        echo ""
        echo "Easy control for Ollama service"
        echo "  start   - Start Ollama server"
        echo "  stop    - Stop all Ollama processes"
        echo "  status  - Check if Ollama is running"
        echo "  restart - Restart Ollama"
        exit 1
        ;;
esac

exit 0

