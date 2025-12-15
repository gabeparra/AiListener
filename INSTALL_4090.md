# Glup Installation Guide - RTX 4090

## Quick Start

This guide will help you install Glup on a system with an NVIDIA RTX 4090 GPU for optimal performance.

### Prerequisites

- NVIDIA RTX 4090 GPU (24GB VRAM)
- NVIDIA drivers installed (check with `nvidia-smi`)
- Python 3.11+
- pip (Python package manager)

### Step 1: Install Ollama with GPU Support

Run the automated installation script:

```bash
./scripts/install_ollama_4090.sh
```

Or manually:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama (it will automatically use your GPU)
ollama serve
```

### Step 2: Download a Model

Ollama automatically uses CUDA/GPU acceleration when available. For RTX 4090, recommended models:

**High Quality (Recommended):**
```bash
ollama pull llama3.1:70b    # Best quality, ~40GB
ollama pull llama3:70b      # Excellent alternative, ~40GB
```

**Balanced:**
```bash
ollama pull mistral-nemo:12b    # Good balance, ~12GB
ollama pull qwen2.5:72b         # High quality alternative
```

**Fast Testing:**
```bash
ollama pull llama3.2:3b     # Quick for testing, ~2GB
```

### Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set your model
# OLLAMA_MODEL=llama3.1:70b
```

### Step 4: Install Python Dependencies

```bash
# Create virtual environment (if not already created)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install the package in editable mode
pip install -e .
```

### Step 5: Run Glup

```bash
# With Web UI (Recommended)
python -m caption_ai --web

# Then open http://127.0.0.1:8000 in your browser

# Or without Web UI (CLI only)
python -m caption_ai
```

## Verifying GPU Usage

Monitor GPU utilization:

```bash
# Watch GPU usage in real-time
watch -n 1 nvidia-smi

# Check if Ollama is using GPU
nvidia-smi
```

You should see `ollama` process using GPU memory when running.

## Troubleshooting

### Ollama not using GPU

1. Verify NVIDIA drivers:
   ```bash
   nvidia-smi
   ```

2. Check Ollama logs:
   ```bash
   ollama serve
   ```
   Look for CUDA/GPU initialization messages.

3. Verify CUDA is available:
   ```bash
   ollama run llama3.2:3b "test"
   ```
   Check GPU memory usage with `nvidia-smi` during this command.

### Out of Memory

If you get OOM errors with 70b models:
- Use a smaller model (e.g., `llama3.2:3b` or `mistral-nemo:12b`)
- Close other GPU-intensive applications
- The 4090 has 24GB VRAM - models up to ~40GB work with quantization

### Ollama Not Starting

```bash
# Kill existing Ollama processes
pkill ollama

# Start fresh
ollama serve
```

### Controlling Ollama Service

Ollama should NOT auto-start to prevent memory issues. Use the control script:

```bash
# Start Ollama manually
./scripts/control_ollama.sh start

# Stop Ollama
./scripts/control_ollama.sh stop

# Check status
./scripts/control_ollama.sh status

# Restart
./scripts/control_ollama.sh restart
```

Or manually:
```bash
# Start
ollama serve &

# Stop (force kill all instances)
pkill -9 ollama
```

**Note:** Ollama auto-start has been disabled. You must start it manually when needed.

## Performance Tips

1. **Model Selection**: For RTX 4090, `llama3.1:70b` provides excellent quality and reasonable speed
2. **Batch Processing**: Glup processes segments in batches - adjust `summary_interval_seconds` in code if needed
3. **GPU Monitoring**: Keep `nvidia-smi` running to monitor GPU usage
4. **Model Caching**: Ollama caches models in memory after first load - subsequent runs are faster

## Next Steps

- Customize Glup's personality in `src/caption_ai/prompts.py`
- Adjust summary intervals in `src/caption_ai/main.py`
- Set up real audio capture (see README.md for roadmap)

