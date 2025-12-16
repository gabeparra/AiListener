> ⚠️ This repository is archived and kept for historical purposes.
>  
> Active development continues in **ARES**: https://github.com/gabeparra/ares


# Glup - Advanced Meeting Intelligence

Meeting caption listener + summarizer with Glup personality and pluggable LLM backends.

## Overview

Glup is an advanced AI meeting assistant that listens to meeting captions (or generates fake transcript segments for testing) and produces rolling summaries with the calculated, analytical personality of Glup. It supports OpenAI/ChatGPT, Grok, Gemini, and local models via Ollama with full GPU acceleration for RTX 4090 and other NVIDIA GPUs.

## Architecture

```
┌─────────────┐
│   Capture   │──┐
│  (Whisper/  │  │
│   Browser)  │  │
└─────────────┘  │
                 ▼
            ┌─────────┐
            │   Bus   │──┐
            │ (Queue) │  │
            └─────────┘  │
                         │
            ┌─────────┐  │
            │ Storage │◄─┘
            │(SQLite) │
            └─────────┘
                 │
                 ▼
            ┌─────────────┐
            │ Summarizer  │──┐
            │   (Loop)    │  │
            └─────────────┘  │
                             │
            ┌─────────────┐  │
            │ LLM Router  │◄─┘
            └─────────────┘
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
    OpenAI   Gemini   Ollama
     Grok
```

## Installation

### Prerequisites

- Python 3.11+
- pip (Python package manager)
- NVIDIA GPU (RTX 4090 recommended) with drivers installed

### Quick Setup (RTX 4090)

For RTX 4090 systems, see [INSTALL_4090.md](INSTALL_4090.md) for optimized GPU setup.

### Standard Setup

1. Clone the repository:
```bash
git clone https://github.com/gabeparra/AiListener.git
cd AiListener
```

2. Create and activate virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies and package:
```bash
pip install -r requirements.txt
pip install -e .  # Install package in editable mode
```

## Configuration

Create a `.env` file in the project root:

```env
# LLM Provider (openai, grok, gemini, local)
LLM_PROVIDER=local

# OpenAI (if using OpenAI)
OPENAI_API_KEY=sk-...

# Grok (if using Grok)
GROK_API_KEY=xai-...

# Gemini (if using Gemini)
GEMINI_API_KEY=...

# Local Ollama (if using local)
# For RTX 4090, recommended models: llama3.1:70b, llama3:70b, mistral-nemo:12b
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:70b

# Storage (optional, defaults to ~/.caption_ai/segments.db)
STORAGE_PATH=~/.caption_ai/segments.db
```

## Usage

### Running with React Web UI (Recommended)

Glup now includes a React frontend with interactive chat! 

**Development mode (with hot reload):**

1. Install Node.js dependencies:
```bash
npm install
```

2. Start React dev server (terminal 1):
```bash
npm run dev
```

3. Start Glup backend (terminal 2):
```bash
source .venv/bin/activate
python -m caption_ai --web --port 8000
```

4. Open http://localhost:3000 in your browser

**Production mode:**

1. Build React app:
```bash
npm run build
```

2. Start Glup:
```bash
python -m caption_ai --web
```

3. Open http://127.0.0.1:8000

The React web UI provides:
- **Interactive Chat**: Talk directly with Glup using the chat panel
- Real-time conversation segments display
- Live Glup analysis updates
- WebSocket-based streaming for instant updates
- Dark theme with Glup's distinctive styling
- Hot Module Replacement (HMR) for instant development updates

### Running with CLI Only

Run without web UI:

```bash
python -m caption_ai
```

This will:
1. Generate fake meeting transcript segments
2. Store them in SQLite
3. Produce rolling summaries every 15 seconds using the configured LLM
4. Display output in the terminal

### Using Local Ollama

1. Install Ollama from https://ollama.ai

2. **Start Ollama manually** (it's disabled from auto-start):
```bash
# Use the control script
./scripts/control_ollama.sh start

# Or manually
ollama serve &
```

3. Pull a model:
```bash
ollama pull llama3.2:3b
```

4. Set `LLM_PROVIDER=local` in `.env` and run:
```bash
python -m caption_ai --web
```

**Important:** Ollama does NOT auto-start to prevent memory issues. Use `./scripts/control_ollama.sh stop` to terminate it when done.

## Development

### Setup

```bash
# Install with dev dependencies
pip install -r requirements-dev.txt

# Run linting
make lint

# Run tests
make test

# Run the application
make run
```

### Project Structure

```
caption-ai/
├── src/
│   └── caption_ai/
│       ├── __init__.py
│       ├── config.py          # Configuration management
│       ├── bus.py              # Segment queue
│       ├── storage.py          # SQLite storage
│       ├── prompts.py          # Prompt templates
│       ├── summarizer.py       # Rolling summarizer loop
│       ├── main.py             # CLI entrypoint
│       ├── capture/            # Audio capture (future)
│       └── llm/                # LLM clients
│           ├── base.py         # LLM interface
│           ├── router.py       # Provider router
│           ├── openai_api.py
│           ├── gemini_api.py
│           ├── grok_api.py
│           └── local_ollama.py
├── tests/                      # Test suite
├── scripts/                    # Utility scripts
├── pyproject.toml              # Project metadata
├── Makefile                    # Development commands
└── README.md
```

## Roadmap

- [ ] **Whisper Audio Capture**: Real-time audio transcription using faster-whisper
- [ ] **Teams UI Captions**: Extract captions from Microsoft Teams UI
- [ ] **Browser Automation**: Use Playwright to capture captions from web meetings
- [ ] **Full LLM Implementations**: Complete OpenAI, Gemini, and Grok API integrations
- [ ] **Speaker Diarization**: Identify and label speakers
- [ ] **Export Formats**: Export summaries to Markdown, PDF, etc.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper type hints and async patterns
4. Run `make lint` and `make test`
5. Submit a pull request

### Dev Setup

```bash
# Clone and setup
git clone https://github.com/gabeparra/AiListener.git
cd AiListener
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Run tests
pytest

# Format and lint
ruff check .
ruff format .
```

## License

MIT License - see LICENSE file for details.

