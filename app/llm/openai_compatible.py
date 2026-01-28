"""OpenAI-compatible LLM client implementation.

This client works with any OpenAI-compatible API including:
- Ollama (local LLM server)
- VCF Private AI (VMware's enterprise LLM service)
- Any other OpenAI-compatible endpoint

Environment variables:
    LLM_API_URL: Base URL for the LLM service (default: http://ollama:11434)
    LLM_MODEL: Model to use (default: smollm2:360m)
    LLM_API_KEY: Optional API key for authenticated services
    LLM_TIMEOUT: Request timeout override (optional, uses model config if not set)
"""
import os
import logging
from typing import List, Dict, Optional

import httpx

from .client import LLMClient
from .model_configs import get_model_config

logger = logging.getLogger(__name__)


class OpenAICompatibleClient(LLMClient):
    """Client for OpenAI-compatible LLM services.
    
    Supports Ollama, VCF Private AI, and other OpenAI-compatible backends.
    Model-specific parameters are loaded from model_configs.py.
    """
    
    def __init__(self):
        self.base_url = os.getenv("LLM_API_URL", "http://ollama:11434")
        self.model = os.getenv("LLM_MODEL", "smollm2:360m")
        self.api_key = os.getenv("LLM_API_KEY", "")
        
        # Load model-specific configuration
        self.config = get_model_config(self.model)
        
        # Allow timeout override via env var, otherwise use model config
        timeout_override = os.getenv("LLM_TIMEOUT")
        self.timeout = float(timeout_override) if timeout_override else self.config["timeout"]
        
        logger.info(
            f"Initialized OpenAI-compatible client: {self.base_url}, "
            f"model: {self.model}, timeout: {self.timeout}s, "
            f"num_ctx: {self.config['num_ctx']}, num_predict: {self.config['num_predict']}"
        )
    
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """Send chat messages to LLM and get response."""
        full_messages = []
        
        # Add system prompt if provided
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        
        # Add user messages
        full_messages.extend(messages)
        
        logger.info(f"Sending request to {self.base_url} (timeout: {self.timeout}s)...")
        
        # Build request headers
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Build request payload
        # Note: Ollama uses 'options' dict, OpenAI uses top-level params
        # We include both for compatibility
        payload = {
            "model": self.model,
            "messages": full_messages,
            "stream": False,
            "temperature": self.config["temperature"],
            # Ollama-specific options (ignored by OpenAI)
            "options": {
                "num_ctx": self.config["num_ctx"],
                "num_predict": self.config["num_predict"],
                "temperature": self.config["temperature"],
            },
            # OpenAI-compatible params
            "max_tokens": self.config["num_predict"],
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                
                data = response.json()
                logger.info("Received response from LLM")
                return data["choices"][0]["message"]["content"]
                
        except httpx.TimeoutException:
            logger.error(f"LLM request timed out after {self.timeout}s")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"LLM request failed: {type(e).__name__}: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if the LLM service is available."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                # Try Ollama-style health check first
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    return True
                
                # Fall back to OpenAI-style models endpoint
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                response = await client.get(f"{self.base_url}/v1/models", headers=headers)
                return response.status_code == 200
                
        except Exception as e:
            logger.warning(f"LLM health check failed: {e}")
            return False
