"""Abstract base class for LLM clients."""
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class LLMClient(ABC):
    """Abstract base class for LLM backends.
    
    All LLM implementations (Ollama, VCF Private AI, OpenAI) must
    implement this interface, allowing easy swapping between backends.
    """
    
    @abstractmethod
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """Send messages to LLM and get response.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            system_prompt: Optional system prompt to prepend
            
        Returns:
            The assistant's response text
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the LLM backend is available.
        
        Returns:
            True if backend is healthy and responding
        """
        pass


def get_llm_client() -> LLMClient:
    """Factory function to get the appropriate LLM client based on configuration.
    
    Environment variables:
        LLM_BACKEND: Which backend to use:
            - 'openai_compatible' (default): Works with Ollama, VCF Private AI, or any OpenAI-compatible API
            - 'openai': OpenAI's official API (requires OPENAI_API_KEY)
            - 'ollama': Legacy, redirects to openai_compatible
            - 'vcf_private_ai': Legacy, redirects to openai_compatible
        
    Returns:
        An instance of the appropriate LLMClient implementation
    """
    backend = os.getenv("LLM_BACKEND", "openai_compatible").lower()
    
    # Primary: OpenAI-compatible client (works with Ollama, VCF Private AI, etc.)
    if backend in ("openai_compatible", "ollama", "vcf_private_ai"):
        from .openai_compatible import OpenAICompatibleClient
        return OpenAICompatibleClient()
    
    # OpenAI's official API (different auth handling)
    elif backend == "openai":
        from .openai_client import OpenAIClient
        return OpenAIClient()
    
    else:
        raise ValueError(f"Unknown LLM backend: {backend}. "
                        f"Supported: openai_compatible, openai")
