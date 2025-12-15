#!/bin/bash
# Installation script for Glup on RTX 4090 with Ollama GPU support

set -e

echo "╔══════════════════════════════════════════════════════╗"
echo "║  Glup Installation - RTX 4090 GPU Configuration      ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Check for NVIDIA GPU
echo "[1/5] Checking NVIDIA GPU..."
if command -v nvidia-smi &> /dev/null; then
    echo "✓ NVIDIA drivers detected"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo "⚠ Warning: nvidia-smi not found. GPU acceleration may not work."
fi

# Install Ollama if not present
echo ""
echo "[2/5] Installing Ollama..."
if command -v ollama &> /dev/null; then
    echo "✓ Ollama already installed"
    ollama --version
else
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Start Ollama service
echo ""
echo "[3/5] Starting Ollama service..."
if pgrep -x "ollama" > /dev/null; then
    echo "✓ Ollama service already running"
else
    echo "Starting Ollama in background..."
    ollama serve &
    sleep 3
fi

# Verify Ollama is accessible
echo ""
echo "[4/5] Verifying Ollama setup..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama API is accessible"
else
    echo "⚠ Warning: Could not connect to Ollama. Please start it manually:"
    echo "   ollama serve"
    exit 1
fi

# Pull recommended model for RTX 4090
echo ""
echo "[5/5] Downloading recommended model for RTX 4090..."
echo "This may take a while depending on your internet connection..."
echo ""
echo "Recommended: llama3.1:70b (high quality, ~40GB)"
echo "Alternative: llama3:70b (excellent quality, ~40GB)"
echo "Fast option: llama3.2:3b (quick testing, ~2GB)"
echo ""

read -p "Enter model name to download (default: llama3.1:70b): " model_name
model_name=${model_name:-llama3.1:70b}

echo "Downloading $model_name..."
ollama pull "$model_name"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Installation Complete                                ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "IMPORTANT: Disabling Ollama auto-start to prevent memory issues..."
sudo systemctl stop ollama 2>/dev/null || true
sudo systemctl disable ollama 2>/dev/null || true
echo "✓ Ollama auto-start disabled"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env:"
echo "   cp .env.example .env"
echo ""
echo "2. Update .env with your model:"
echo "   OLLAMA_MODEL=$model_name"
echo ""
echo "3. Install the package (if not already done):"
echo "   pip install -e ."
echo ""
echo "4. Start Ollama manually when needed:"
echo "   ./scripts/control_ollama.sh start"
echo "   # Or: ollama serve &"
echo ""
echo "5. Run Glup:"
echo "   python -m caption_ai --web"
echo ""
echo "To stop Ollama:"
echo "   ./scripts/control_ollama.sh stop"
echo ""
echo "Ollama will automatically use your RTX 4090 GPU for inference."
echo "Monitor GPU usage with: watch -n 1 nvidia-smi"

