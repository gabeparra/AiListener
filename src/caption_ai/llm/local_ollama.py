"""Local Ollama client via HTTP."""

import httpx

from caption_ai.config import config
from caption_ai.llm.base import LLMClient, LLMReply
from caption_ai.prompts import get_system_prompt


class LocalOllamaClient(LLMClient):
    """Local Ollama client implementation."""

    def __init__(self, model: str | None = None) -> None:
        """Initialize Ollama client."""
        self.base_url = config.ollama_base_url
        self.model = model or config.ollama_model
        self.system_prompt = get_system_prompt()
    
    def set_model(self, model: str) -> None:
        """Change the model for this client."""
        self.model = model

    async def complete(self, prompt: str) -> LLMReply:
        """Complete prompt using local Ollama API."""
        # Try /api/chat first (preferred for chat-style interactions)
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                
                # If 404, fall back to /api/generate
                if response.status_code == 404:
                    return await self._complete_with_generate(prompt)
                
                response.raise_for_status()
                
                # Read response text and handle both single JSON and JSON lines
                response_text = response.text
                
                # Try parsing as single JSON first
                try:
                    import json
                    data = json.loads(response_text)
                    if "message" in data:
                        content = data.get("message", {}).get("content", "")
                        return LLMReply(
                            content=content,
                            model=self.model,
                        )
                except (ValueError, json.JSONDecodeError):
                    pass
                
                # Handle streaming JSON lines (multiple JSON objects, one per line)
                content_parts = []
                for line in response_text.strip().split('\n'):
                    if not line.strip():
                        continue
                    try:
                        import json
                        chunk = json.loads(line)
                        if "message" in chunk:
                            msg_content = chunk["message"].get("content", "")
                            if msg_content:
                                content_parts.append(msg_content)
                        if chunk.get("done", False):
                            break
                    except (ValueError, json.JSONDecodeError):
                        continue
                
                content = "".join(content_parts) if content_parts else response_text
                return LLMReply(
                    content=content,
                    model=self.model,
                )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Fallback to generate endpoint
                return await self._complete_with_generate(prompt)
            return LLMReply(
                content=f"HTTP error calling Ollama: {e}",
            )
        except httpx.RequestError as e:
            return LLMReply(
                content=f"Error connecting to Ollama: {e}. "
                f"Make sure Ollama is running at {self.base_url}",
            )
        except Exception as e:
            return LLMReply(
                content=f"Error calling Ollama: {e}",
            )
    
    async def _complete_with_generate(self, prompt: str) -> LLMReply:
        """Fallback to /api/generate endpoint."""
        url = f"{self.base_url}/api/generate"
        # Combine system prompt and user prompt for generate endpoint
        full_prompt = f"{self.system_prompt}\n\n{prompt}"
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                # Read response text and handle both single JSON and JSON lines
                response_text = response.text
                
                # Try parsing as single JSON first
                try:
                    import json
                    data = json.loads(response_text)
                    content = data.get("response", "")
                    return LLMReply(
                        content=content,
                        model=self.model,
                    )
                except (ValueError, json.JSONDecodeError):
                    pass
                
                # Handle streaming JSON lines
                content_parts = []
                for line in response_text.strip().split('\n'):
                    if not line.strip():
                        continue
                    try:
                        import json
                        chunk = json.loads(line)
                        if "response" in chunk:
                            content_parts.append(chunk["response"])
                        if chunk.get("done", False):
                            break
                    except (ValueError, json.JSONDecodeError):
                        continue
                
                content = "".join(content_parts) if content_parts else response_text
                return LLMReply(
                    content=content,
                    model=self.model,
                )
        except Exception as e:
            return LLMReply(
                content=f"Error calling Ollama generate endpoint: {e}",
            )

