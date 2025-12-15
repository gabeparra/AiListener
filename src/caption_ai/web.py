"""Web server for Glup UI."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from caption_ai.bus import Segment
from caption_ai.storage import Storage
from caption_ai.config import config
from caption_ai.llm.router import get_llm_client
from caption_ai.prompts import get_system_prompt
from caption_ai.code_reader import code_reader


class ModelChangeRequest(BaseModel):
    model: str

app = FastAPI(title="Glup - Advanced Meeting Intelligence")

# CORS middleware for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
storage: Storage | None = None
llm_client = None
websocket_connections: list[WebSocket] = []
summary_callbacks: list[callable] = []
summarizer_running: bool = True  # Controls whether summarizer processes segments
summarizer_instance = None  # Reference to the summarizer instance


def set_llm_client(client=None, model: str | None = None):
    """Set the LLM client for chat."""
    global llm_client
    if client is None:
        llm_client = get_llm_client(config.llm_provider)
        # If it's a LocalOllamaClient and we have a model, set it
        if model and hasattr(llm_client, 'set_model'):
            llm_client.set_model(model)
        elif model and hasattr(llm_client, '__class__'):
            # Recreate with new model if it's LocalOllamaClient
            from caption_ai.llm.local_ollama import LocalOllamaClient
            if isinstance(llm_client, LocalOllamaClient):
                llm_client = LocalOllamaClient(model=model)
    else:
        llm_client = client


def set_storage(storage_instance: Storage) -> None:
    """Set the storage instance."""
    global storage
    storage = storage_instance
    # Initialize LLM client when storage is set
    if llm_client is None:
        set_llm_client()


def set_storage(storage_instance: Storage) -> None:
    """Set the storage instance."""
    global storage
    storage = storage_instance
    # Initialize LLM client when storage is set
    if llm_client is None:
        set_llm_client()


async def broadcast_summary(summary: str) -> None:
    """Broadcast new summary to all WebSocket connections."""
    if not websocket_connections:
        return

    message = json.dumps({"type": "summary", "summary": summary})
    disconnected = []

    for connection in websocket_connections:
        try:
            await connection.send_text(message)
        except Exception:
            disconnected.append(connection)

    # Remove disconnected clients
    for conn in disconnected:
        if conn in websocket_connections:
            websocket_connections.remove(conn)


async def broadcast_segment(segment: Segment) -> None:
    """Broadcast new segment to all WebSocket connections."""
    if not websocket_connections:
        return

    message = json.dumps({
        "type": "segment",
        "segment": {
            "timestamp": segment.timestamp.isoformat(),
            "text": segment.text,
            "speaker": segment.speaker,
        },
    })
    disconnected = []

    for connection in websocket_connections:
        try:
            await connection.send_text(message)
        except Exception:
            disconnected.append(connection)

    # Remove disconnected clients
    for conn in disconnected:
        if conn in websocket_connections:
            websocket_connections.remove(conn)


@app.get("/", response_class=HTMLResponse)
async def get_index() -> str:
    """Serve the main UI."""
    # Check for built React app first
    built_html = Path(__file__).parent.parent.parent / "web" / "dist" / "index.html"
    if built_html.exists():
        return built_html.read_text()
    
    # Fallback to default HTML
    html_path = Path(__file__).parent.parent.parent / "web" / "index.html"
    if html_path.exists():
        return html_path.read_text()
    return get_default_html()


# Serve static files from React build
static_path = Path(__file__).parent.parent.parent / "web" / "dist"
if static_path.exists():
    app.mount("/assets", StaticFiles(directory=str(static_path / "assets")), name="assets")


def get_default_html() -> str:
    """Return default HTML if file doesn't exist."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Glup - Advanced Meeting Intelligence</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: #0a0a0a;
            color: #e0e0e0;
            overflow-x: hidden;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            border-bottom: 2px solid #ff0000;
            padding: 20px 0;
            margin-bottom: 30px;
        }
        h1 {
            color: #ff0000;
            text-shadow: 0 0 10px #ff0000;
            font-size: 2.5em;
            letter-spacing: 3px;
        }
        .subtitle {
            color: #888;
            font-size: 0.9em;
            margin-top: 5px;
        }
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        @media (max-width: 968px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }
        .panel {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 0 20px rgba(255, 0, 0, 0.1);
        }
        .panel h2 {
            color: #ff4444;
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        .segments {
            max-height: 500px;
            overflow-y: auto;
        }
        .segment {
            background: #252525;
            padding: 12px;
            margin-bottom: 10px;
            border-left: 3px solid #ff0000;
            border-radius: 4px;
        }
        .segment-time {
            color: #888;
            font-size: 0.85em;
            margin-bottom: 5px;
        }
        .segment-speaker {
            color: #ff6666;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .segment-text {
            color: #e0e0e0;
            line-height: 1.6;
        }
        .summary {
            background: #252525;
            padding: 15px;
            border-left: 3px solid #00ff00;
            border-radius: 4px;
            line-height: 1.8;
            color: #e0e0e0;
        }
        .status {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #1a1a1a;
            border: 1px solid #333;
            padding: 10px 15px;
            border-radius: 5px;
            font-size: 0.9em;
        }
        .status.connected {
            border-color: #00ff00;
            color: #00ff00;
        }
        .status.disconnected {
            border-color: #ff0000;
            color: #ff0000;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        .status.connected .status-indicator {
            background: #00ff00;
        }
        .status.disconnected .status-indicator {
            background: #ff0000;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #1a1a1a;
        }
        ::-webkit-scrollbar-thumb {
            background: #ff0000;
            border-radius: 4px;
        }
        .empty-state {
            text-align: center;
            color: #666;
            padding: 40px;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="status disconnected" id="status">
        <span class="status-indicator"></span>
        <span id="status-text">Disconnected</span>
    </div>
    <div class="container">
        <header>
            <h1>GLUP</h1>
            <div class="subtitle">Advanced Meeting Intelligence | Neural Processing Active</div>
        </header>
        <div class="main-content">
            <div class="panel">
                <h2>Conversation Segments</h2>
                <div class="segments" id="segments">
                    <div class="empty-state">Awaiting conversation data...</div>
                </div>
            </div>
            <div class="panel">
                <h2>Glup Analysis</h2>
                <div id="summary">
                    <div class="empty-state">No analysis available yet...</div>
                </div>
            </div>
        </div>
    </div>
    <script>
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        const segmentsDiv = document.getElementById('segments');
        const summaryDiv = document.getElementById('summary');
        const statusDiv = document.getElementById('status');
        const statusText = document.getElementById('status-text');
        
        function updateStatus(connected) {
            if (connected) {
                statusDiv.className = 'status connected';
                statusText.textContent = 'Connected';
            } else {
                statusDiv.className = 'status disconnected';
                statusText.textContent = 'Disconnected';
            }
        }
        
        function addSegment(segment) {
            if (segmentsDiv.querySelector('.empty-state')) {
                segmentsDiv.innerHTML = '';
            }
            const div = document.createElement('div');
            div.className = 'segment';
            const date = new Date(segment.timestamp);
            div.innerHTML = `
                <div class="segment-time">${date.toLocaleTimeString()}</div>
                <div class="segment-speaker">${segment.speaker || 'Speaker'}</div>
                <div class="segment-text">${segment.text}</div>
            `;
            segmentsDiv.insertBefore(div, segmentsDiv.firstChild);
            segmentsDiv.scrollTop = 0;
        }
        
        function updateSummary(summary) {
            summaryDiv.innerHTML = `<div class="summary">${summary.replace(/\\n/g, '<br>')}</div>`;
        }
        
        ws.onopen = () => {
            updateStatus(true);
            ws.send(JSON.stringify({type: 'init'}));
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'segment') {
                addSegment(data.segment);
            } else if (data.type === 'summary') {
                updateSummary(data.summary);
            } else if (data.type === 'init') {
                if (data.segments) {
                    data.segments.forEach(s => addSegment(s));
                }
                if (data.summary) {
                    updateSummary(data.summary);
                }
            }
        };
        
        ws.onclose = () => {
            updateStatus(false);
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        };
        
        ws.onerror = () => {
            updateStatus(false);
        };
    </script>
</body>
</html>"""


@app.get("/api/segments")
async def get_segments(limit: int = 50) -> JSONResponse:
    """Get recent segments."""
    if not storage:
        return JSONResponse({"error": "Storage not initialized"}, status_code=500)

    segments = []
    async for segment in storage.fetch_recent(limit=limit):
        segments.append({
            "timestamp": segment.timestamp.isoformat(),
            "text": segment.text,
            "speaker": segment.speaker,
        })

    return JSONResponse({"segments": list(reversed(segments))})


@app.get("/api/summary")
async def get_summary() -> JSONResponse:
    """Get latest summary."""
    if not storage:
        return JSONResponse({"error": "Storage not initialized"}, status_code=500)

    summary = await storage.get_latest_summary()
    return JSONResponse({"summary": summary})


@app.get("/api/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({
        "status": "ok",
        "backend": "running",
        "storage": "initialized" if storage else "not initialized",
        "llm_client": "ready" if llm_client else "not ready",
    })


@app.get("/api/code/files")
async def list_code_files(directory: str | None = None, max_depth: int = 5) -> JSONResponse:
    """List code files in the project."""
    try:
        if directory:
            dir_path = Path(directory)
        else:
            dir_path = None
        
        files = code_reader.list_code_files(directory=dir_path, max_depth=max_depth)
        return JSONResponse({"files": files, "count": len(files)})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/code/read")
async def read_code_file(file_path: str, max_lines: int = 1000) -> JSONResponse:
    """Read a code file."""
    try:
        file_data = code_reader.read_file(file_path, max_lines=max_lines)
        if file_data:
            return JSONResponse(file_data)
        else:
            return JSONResponse({"error": "File not found or cannot be read"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/code/search")
async def search_code(query: str, max_results: int = 10) -> JSONResponse:
    """Search for text in code files."""
    try:
        results = code_reader.search_in_files(query, max_results=max_results)
        return JSONResponse({"results": results, "count": len(results)})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/conversations")
async def get_conversations(session_id: str | None = None, limit: int = 50) -> JSONResponse:
    """Get conversation history."""
    if not storage:
        return JSONResponse({"error": "Storage not initialized"}, status_code=500)
    
    try:
        if session_id:
            conversations = await storage.get_conversation_history(session_id, limit=limit)
        else:
            conversations = await storage.get_all_conversations(limit=limit)
        
        return JSONResponse({
            "conversations": conversations,
            "count": len(conversations),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/conversations/sessions")
async def get_conversation_sessions() -> JSONResponse:
    """Get list of conversation sessions."""
    if not storage:
        return JSONResponse({"error": "Storage not initialized"}, status_code=500)
    
    try:
        sessions = await storage.get_conversation_sessions()
        return JSONResponse({"sessions": sessions, "count": len(sessions)})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


class ConversationSearchRequest(BaseModel):
    query: str
    limit: int = 20


@app.post("/api/conversations/search")
async def search_conversations(request: ConversationSearchRequest) -> JSONResponse:
    """Search conversations."""
    if not storage:
        return JSONResponse({"error": "Storage not initialized"}, status_code=500)
    
    try:
        query = request.query.lower()
        limit = request.limit
        
        all_conversations = await storage.get_all_conversations(limit=200)
        results = []
        
        for conv in all_conversations:
            if query in conv["message"].lower():
                results.append(conv)
                if len(results) >= limit:
                    break
        
        return JSONResponse({
            "results": results,
            "count": len(results),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/summarizer/status")
async def get_summarizer_status() -> JSONResponse:
    """Get summarizer running status."""
    global summarizer_running
    return JSONResponse({
        "running": summarizer_running,
    })


class SummarizerToggleRequest(BaseModel):
    running: bool


@app.post("/api/summarizer/toggle")
async def toggle_summarizer(request: SummarizerToggleRequest) -> JSONResponse:
    """Toggle summarizer on/off."""
    global summarizer_running, summarizer_instance
    
    try:
        new_state = request.running
        summarizer_running = new_state
        
        # If we have a summarizer instance, we could pause it
        # For now, we just set the flag - the summarizer will check this
        
        # Broadcast to all WebSocket connections
        message = json.dumps({
            "type": "summarizer_state",
            "running": summarizer_running,
        })
        disconnected = []
        for connection in websocket_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            if conn in websocket_connections:
                websocket_connections.remove(conn)
        
        return JSONResponse({
            "success": True,
            "running": summarizer_running,
            "message": f"Summarizer {'started' if summarizer_running else 'paused'}",
        })
    except Exception as e:
        return JSONResponse({
            "error": f"Failed to toggle summarizer: {str(e)}"
        }, status_code=500)


def set_summarizer(summarizer) -> None:
    """Set the summarizer instance reference."""
    global summarizer_instance
    summarizer_instance = summarizer


def get_summarizer_running() -> bool:
    """Get whether summarizer should be running."""
    return summarizer_running


@app.get("/api/models")
async def get_models() -> JSONResponse:
    """Get current model and list available models from Ollama."""
    try:
        import httpx
        
        # Get current model
        current_model = config.ollama_model
        
        # Fetch available models from Ollama
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{config.ollama_base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                available_models = [model.get("name", "") for model in data.get("models", [])]
            else:
                available_models = []
        
        return JSONResponse({
            "current_model": current_model,
            "available_models": available_models,
            "models": available_models,
        })
    except Exception as e:
        return JSONResponse({
            "current_model": config.ollama_model,
            "available_models": [],
            "models": [],
            "error": str(e),
        }, status_code=500)


@app.post("/api/models")
async def set_model(request: ModelChangeRequest) -> JSONResponse:
    """Change the Ollama model."""
    try:
        import httpx
        
        new_model = request.model
        
        # Verify model exists in Ollama
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{config.ollama_base_url}/api/tags")
            if response.status_code != 200:
                return JSONResponse({
                    "error": "Cannot connect to Ollama. Make sure it's running."
                }, status_code=503)
            
            data = response.json()
            available_models = [model.get("name", "") for model in data.get("models", [])]
            
            if new_model not in available_models:
                return JSONResponse({
                    "error": f"Model '{new_model}' not found. Available models: {', '.join(available_models[:5])}"
                }, status_code=404)
        
        # Update config
        config.ollama_model = new_model
        
        # Reinitialize LLM client with new model
        global llm_client
        set_llm_client(model=new_model)
        
        # Broadcast model change to all WebSocket connections
        message = json.dumps({"type": "model_changed", "model": new_model})
        disconnected = []
        for connection in websocket_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            if conn in websocket_connections:
                websocket_connections.remove(conn)
        
        return JSONResponse({
            "success": True,
            "model": new_model,
            "message": f"Model changed to {new_model}",
        })
    except Exception as e:
        return JSONResponse({
            "error": f"Failed to change model: {str(e)}"
        }, status_code=500)


async def handle_chat_message(message: str, websocket: WebSocket, session_id: str = "default") -> None:
    """Handle chat message from user and respond with Glup."""
    if not llm_client:
        await websocket.send_json({
            "type": "chat_response",
            "response": "Error: LLM client not initialized. Please check configuration.",
        })
        return

    try:
        # Save user message to conversation history
        if storage:
            await storage.save_conversation(session_id, "user", message)
        
        # Get conversation history for context
        conversation_history = []
        if storage:
            conversation_history = await storage.get_conversation_history(
                session_id, limit=20
            )
        # Check if user wants to read code or analyze code
        message_lower = message.lower()
        code_context = ""
        
        # Detect code-related queries
        code_keywords = ['read code', 'show code', 'analyze code', 'explain code', 
                        'read file', 'show file', 'code in', 'file:', 'function', 
                        'class', 'module', 'import', 'search code', 'find code']
        
        if any(keyword in message_lower for keyword in code_keywords):
            # Try to extract file path or search query
            if 'file:' in message_lower or 'read ' in message_lower:
                # Extract potential file path
                parts = message.split()
                file_path = None
                for i, part in enumerate(parts):
                    if 'file:' in part.lower() or (i > 0 and parts[i-1].lower() in ['read', 'show', 'file']):
                        if 'file:' in part:
                            file_path = part.split(':', 1)[1]
                        else:
                            file_path = part
                        break
                
                if file_path:
                    file_data = code_reader.read_file(file_path)
                    if file_data:
                        code_context = f"\n\nCode file: {file_data['path']}\n```{file_data['extension'][1:] if file_data['extension'] else 'text'}\n{file_data['content']}\n```\n"
                    else:
                        code_context = f"\n\nNote: Could not read file '{file_path}'. Use /list to see available files."
            
            elif 'search' in message_lower or 'find' in message_lower:
                # Extract search query
                search_terms = message
                if 'search' in message_lower:
                    search_terms = message.split('search', 1)[-1].strip()
                elif 'find' in message_lower:
                    search_terms = message.split('find', 1)[-1].strip()
                
                results = code_reader.search_in_files(search_terms, max_results=5)
                if results:
                    code_context = "\n\nSearch results in codebase:\n"
                    for result in results:
                        code_context += f"\nFile: {result['file']} ({result['match_count']} matches)\n"
                        for match in result['matches'][:2]:
                            code_context += f"  Line {match['line']}: {match['content']}\n"
                else:
                    code_context = f"\n\nNo code found matching: {search_terms}"
            
            elif 'list' in message_lower or 'files' in message_lower:
                files = code_reader.list_code_files(max_depth=3)
                if files:
                    code_context = f"\n\nAvailable code files ({len(files)} total):\n"
                    for file_info in files[:20]:  # Limit to first 20
                        code_context += f"  - {file_info['path']}\n"
                    if len(files) > 20:
                        code_context += f"  ... and {len(files) - 20} more files\n"
                else:
                    code_context = "\n\nNo code files found."
        
        # Build conversation context from history
        history_context = ""
        if conversation_history and len(conversation_history) > 1:
            history_context = "\n\nPrevious conversation context:\n"
            # Include last 10 messages for context (excluding current)
            for conv in conversation_history[-10:-1]:
                role_label = "User" if conv["role"] == "user" else "Glup"
                history_context += f"{role_label}: {conv['message']}\n"
        
        # Build chat prompt with Glup personality, code context, and conversation history
        chat_prompt = f"""The user is asking: {message}
{code_context}
{history_context}

Respond as Glup - be intelligent, calculated, slightly menacing, analytical, and direct. 
Keep responses concise but maintain your distinctive personality. If code is provided, 
analyze it with your characteristic precision and insight. If previous conversation context 
is provided, you can reference it naturally."""
        
        reply = await llm_client.complete(chat_prompt)
        response = reply.content if reply else "I am processing your query..."
        
        # Save Glup's response to conversation history
        if storage:
            await storage.save_conversation(session_id, "assistant", response)
        
        await websocket.send_json({
            "type": "chat_response",
            "response": response,
        })
    except Exception as e:
        await websocket.send_json({
            "type": "chat_response",
            "response": f"Error processing your message: {str(e)}",
        })


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    websocket_connections.append(websocket)

    try:
        # Send initial data
        if storage:
            segments = []
            async for segment in storage.fetch_recent(limit=50):
                segments.append({
                    "timestamp": segment.timestamp.isoformat(),
                    "text": segment.text,
                    "speaker": segment.speaker,
                })
            summary = await storage.get_latest_summary()

            await websocket.send_json({
                "type": "init",
                "segments": list(reversed(segments)),
                "summary": summary,
                "current_model": config.ollama_model,
            })

        # Initialize LLM client if not already done
        if llm_client is None:
            set_llm_client()

        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                if message_data.get("type") == "chat":
                    # Handle chat message
                    user_message = message_data.get("message", "")
                    await handle_chat_message(user_message, websocket)
                elif message_data.get("type") == "init":
                    # Client requesting initial data - already sent above
                    pass
            except json.JSONDecodeError:
                pass
            except WebSocketDisconnect:
                break
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the web server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)

