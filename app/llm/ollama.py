"""Ollama LLM client implementation."""
import os
import logging
from typing import List, Dict, Optional

import httpx

from .client import LLMClient

logger = logging.getLogger(__name__)


class OllamaClient(LLMClient):
    """Client for Ollama local LLM service.
    
    Ollama provides an OpenAI-compatible API, making it easy to
    migrate to other OpenAI-compatible backends (like VCF Private AI).
    
    Environment variables:
        OLLAMA_URL: Base URL for Ollama service (default: http://ollama:11434)
        OLLAMA_MODEL: Model to use (default: llama3.2:3b)
        LLM_TIMEOUT: Request timeout in seconds (default: 30)
    """
    
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.timeout = float(os.getenv("LLM_TIMEOUT", "120"))  # 120s for CPU inference
        
        logger.info(f"Initialized Ollama client: {self.base_url}, model: {self.model}, timeout: {self.timeout}s")
    
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """Send chat messages to Ollama and get response."""
        full_messages = []
        
        # Add system prompt if provided
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        
        # Add user messages
        full_messages.extend(messages)
        
        logger.info(f"Sending request to Ollama (timeout: {self.timeout}s)...")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json={
                        "model": self.model,
                        "messages": full_messages,
                        "stream": False,
                        "max_tokens": 150,  # Limit response length for faster CPU inference
                        "temperature": 0.7
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                logger.info("Received response from Ollama")
                return data["choices"][0]["message"]["content"]
        except httpx.TimeoutException:
            logger.error(f"Ollama request timed out after {self.timeout}s")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Ollama request failed: {type(e).__name__}: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if Ollama is available."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
