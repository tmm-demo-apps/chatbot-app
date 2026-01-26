"""VCF Private AI LLM client implementation."""
import os
import logging
from typing import List, Dict, Optional

import httpx

from .client import LLMClient

logger = logging.getLogger(__name__)


class VCFPrivateAIClient(LLMClient):
    """Client for VMware VCF Private AI Model Runtime.
    
    VCF Private AI provides enterprise-grade LLM inference through
    the VMware Cloud Foundation Private AI Ready Infrastructure.
    
    Key benefits:
    - GPU acceleration (NVIDIA Blackwell, Hopper, etc.)
    - Multi-tenant model sharing with namespace isolation
    - Enterprise support from VMware/Broadcom
    - Integrated monitoring via VCF Operations
    
    Environment variables:
        VCF_MODEL_ENDPOINT: Model Runtime endpoint URL
        VCF_MODEL_NAME: Model name (default: llama-3.1-8b)
        VCF_NAMESPACE: Kubernetes namespace (for logging)
        VCF_API_TOKEN: Optional API token (uses SA token if not set)
        LLM_TIMEOUT: Request timeout in seconds (default: 60)
    """
    
    def __init__(self):
        self.endpoint = os.getenv("VCF_MODEL_ENDPOINT")
        if not self.endpoint:
            raise ValueError("VCF_MODEL_ENDPOINT environment variable is required")
        
        self.model = os.getenv("VCF_MODEL_NAME", "llama-3.1-8b")
        self.namespace = os.getenv("VCF_NAMESPACE", "default")
        self.timeout = float(os.getenv("LLM_TIMEOUT", "60"))
        
        # Get authentication token
        self.token = self._get_service_account_token()
        
        logger.info(f"Initialized VCF Private AI client: {self.endpoint}, model: {self.model}")
    
    def _get_service_account_token(self) -> str:
        """Read Kubernetes service account token for authentication.
        
        In Kubernetes, the service account token is mounted at:
        /var/run/secrets/kubernetes.io/serviceaccount/token
        
        Falls back to VCF_API_TOKEN environment variable if not running in K8s.
        """
        token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
        
        try:
            with open(token_path) as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.debug("K8s SA token not found, using VCF_API_TOKEN env var")
            return os.getenv("VCF_API_TOKEN", "")
    
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """Send chat messages to VCF Private AI Model Runtime."""
        full_messages = []
        
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        
        full_messages.extend(messages)
        
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
            # VCF Private AI uses OpenAI-compatible API
            response = await client.post(
                f"{self.endpoint}/v1/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": full_messages,
                    "stream": False
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def health_check(self) -> bool:
        """Check if VCF Private AI Model Runtime is available."""
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            async with httpx.AsyncClient(timeout=5, verify=False) as client:
                response = await client.get(
                    f"{self.endpoint}/v1/models",
                    headers=headers
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"VCF Private AI health check failed: {e}")
            return False
