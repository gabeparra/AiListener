# Ollama Control Guide

Ollama has been configured to **NOT auto-start** to prevent memory issues and crashes.

## Quick Control

Use the provided script:
```bash
./scripts/control_ollama.sh {start|stop|status|restart}
```

## Manual Control

**Start Ollama:**
```bash
ollama serve &
```

**Stop Ollama:**
```bash
./scripts/control_ollama.sh stop
# Or manually:
pkill -9 ollama
```

**Force stop (if stuck):**
```bash
sudo pkill -9 ollama
```

## Disable Auto-Start (if re-enabled)

If Ollama auto-start gets re-enabled, disable it:
```bash
sudo systemctl stop ollama
sudo systemctl disable ollama
```

## Check Status

```bash
./scripts/control_ollama.sh status
# Or:
pgrep -af ollama
```

## Why Disabled?

- Prevents WSL memory crashes
- Easier to control and terminate
- Only runs when you explicitly need it
- Prevents background resource usage

