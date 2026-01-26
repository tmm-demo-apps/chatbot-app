"""OpenAI LLM client implementation (fallback option)."""
import os
import logging
from typing import List, Dict, Optional

import httpx

from .client import LLMClient

logger = logging.getLogger(__name__)


class OpenAIClient(LLMClient):
    """Client for OpenAI API.
    
    This is a fallback option for environments without Ollama
    or VCF Private AI. Uses the official OpenAI API.
    
    Environment variables:
        OPENAI_API_KEY: OpenAI API key (required)
        OPENAI_MODEL: Model to use (default: gpt-3.5-turbo)
        OPENAI_BASE_URL: API base URL (default: https://api.openai.com/v1)
        LLM_TIMEOUT: Request timeout in seconds (default: 30)
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.timeout = float(os.getenv("LLM_TIMEOUT", "30"))
        
        logger.info(f"Initialized OpenAI client: {self.base_url}, model: {self.model}")
    
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """Send chat messages to OpenAI and get response."""
        full_messages = []
        
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        
        full_messages.extend(messages)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": full_messages
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def health_check(self) -> bool:
        """Check if OpenAI API is available."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False
