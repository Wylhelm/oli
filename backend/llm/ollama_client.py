"""
OLI Ollama Client
LLM integration using local Ollama instance

Model: gpt-oss:120b-cloud
Endpoint: http://localhost:11434
"""

import httpx
import json
from typing import Optional, AsyncGenerator
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response from LLM"""
    content: str
    model: str
    total_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None


class OllamaClient:
    """
    Client for Ollama local LLM
    
    Uses the Ollama REST API for text generation and chat completions.
    
    Configure via environment variables:
    - OLLAMA_MODEL: Model name (default: gpt-oss:120b-cloud)
    - OLLAMA_BASE_URL: Ollama API URL (default: http://localhost:11434)
    """
    
    import os
    DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:120b-cloud")
    DEFAULT_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    
    def __init__(
        self,
        model: str = None,
        base_url: str = None,
        timeout: float = 120.0
    ):
        import os
        self.model = model or os.environ.get("OLLAMA_MODEL", self.DEFAULT_MODEL)
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", self.DEFAULT_BASE_URL)
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)
        self.async_client = httpx.AsyncClient(timeout=timeout)
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> LLMResponse:
        """
        Generate text completion (synchronous)
        
        Args:
            prompt: The prompt to complete
            system: Optional system prompt
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum tokens to generate
        
        Returns:
            LLMResponse with generated content
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data.get("response", ""),
                model=data.get("model", self.model),
                total_duration=data.get("total_duration"),
                prompt_eval_count=data.get("prompt_eval_count"),
                eval_count=data.get("eval_count")
            )
        except httpx.HTTPError as e:
            raise ConnectionError(f"Ollama API error: {e}")
    
    async def generate_async(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> LLMResponse:
        """
        Generate text completion (asynchronous)
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = await self.async_client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data.get("response", ""),
                model=data.get("model", self.model),
                total_duration=data.get("total_duration"),
                prompt_eval_count=data.get("prompt_eval_count"),
                eval_count=data.get("eval_count")
            )
        except httpx.HTTPError as e:
            raise ConnectionError(f"Ollama API error: {e}")
    
    async def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.1
    ) -> AsyncGenerator[str, None]:
        """
        Generate text with streaming (for real-time UI updates)
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        
        if system:
            payload["system"] = system
        
        async with self.async_client.stream("POST", url, json=payload) as response:
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
    
    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> LLMResponse:
        """
        Chat completion (for multi-turn conversations)
        
        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": "..."}
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            LLMResponse with assistant's reply
        """
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                model=data.get("model", self.model),
                total_duration=data.get("total_duration"),
                prompt_eval_count=data.get("prompt_eval_count"),
                eval_count=data.get("eval_count")
            )
        except httpx.HTTPError as e:
            raise ConnectionError(f"Ollama API error: {e}")
    
    async def chat_async(
        self,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> LLMResponse:
        """
        Chat completion (asynchronous)
        """
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = await self.async_client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                model=data.get("model", self.model),
                total_duration=data.get("total_duration"),
                prompt_eval_count=data.get("prompt_eval_count"),
                eval_count=data.get("eval_count")
            )
        except httpx.HTTPError as e:
            raise ConnectionError(f"Ollama API error: {e}")
    
    def is_available(self) -> bool:
        """Check if Ollama is available and model is loaded"""
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                # Check if our model is available (with or without :latest tag)
                return any(self.model in name or name in self.model for name in model_names)
            return False
        except Exception:
            return False
    
    def test_model(self) -> bool:
        """Test if the model actually responds (quick test)"""
        try:
            response = self.chat(
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            return len(response.content) > 0
        except Exception:
            return False
    
    def list_models(self) -> list[str]:
        """List available models"""
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m.get("name", "") for m in models]
            return []
        except Exception:
            return []
    
    def close(self):
        """Close HTTP clients"""
        self.client.close()
    
    async def aclose(self):
        """Close async HTTP client"""
        await self.async_client.aclose()


# Singleton instance
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Get or create Ollama client singleton"""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client

