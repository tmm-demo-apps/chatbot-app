"""Model-specific configuration parameters.

Each model has different optimal settings for context window, token generation,
and timeout based on its size and the hardware it runs on.

Usage:
    from .model_configs import get_model_config
    config = get_model_config("smollm2:360m")
"""
from typing import TypedDict


class ModelConfig(TypedDict):
    """Configuration parameters for a specific model."""
    num_ctx: int        # Context window size (tokens)
    num_predict: int    # Max tokens to generate
    temperature: float  # Sampling temperature
    timeout: int        # Request timeout in seconds


# Model configurations optimized through benchmarking
MODEL_CONFIGS: dict[str, ModelConfig] = {
    # ===================
    # Ollama Models (CPU)
    # ===================
    
    # SmolLM2 360M - Best for CPU inference (fast, good quality)
    # Benchmarked: ~2-3s response time on Docker CPU
    "smollm2:360m": {
        "num_ctx": 2048,
        "num_predict": 190,
        "temperature": 0.7,
        "timeout": 30,
    },
    
    # SmolLM2 135M - Fastest but lower quality (may hallucinate)
    "smollm2:135m": {
        "num_ctx": 1024,
        "num_predict": 150,
        "temperature": 0.7,
        "timeout": 15,
    },
    
    # SmolLM2 1.7B - Better quality but slow on CPU (~90s)
    "smollm2:1.7b": {
        "num_ctx": 2048,
        "num_predict": 150,
        "temperature": 0.7,
        "timeout": 120,
    },
    
    # TinyLlama - Alternative small model (~65s on CPU)
    "tinyllama:latest": {
        "num_ctx": 1024,
        "num_predict": 100,
        "temperature": 0.7,
        "timeout": 90,
    },
    
    # Llama 3.2 3B - High quality but slow on CPU (~70s)
    "llama3.2:3b": {
        "num_ctx": 2048,
        "num_predict": 100,
        "temperature": 0.7,
        "timeout": 120,
    },
    
    # ==========================
    # VCF Private AI Models (GPU)
    # ==========================
    # These run on GPU-backed infrastructure, so can use larger models
    
    "mistral-7b": {
        "num_ctx": 4096,
        "num_predict": 256,
        "temperature": 0.7,
        "timeout": 30,
    },
    
    "llama2-70b": {
        "num_ctx": 4096,
        "num_predict": 256,
        "temperature": 0.7,
        "timeout": 60,
    },
    
    # ================
    # OpenAI Models
    # ================
    # OpenAI handles these parameters differently, but we include for completeness
    
    "gpt-3.5-turbo": {
        "num_ctx": 4096,
        "num_predict": 256,
        "temperature": 0.7,
        "timeout": 30,
    },
    
    "gpt-4": {
        "num_ctx": 8192,
        "num_predict": 512,
        "temperature": 0.7,
        "timeout": 60,
    },
}

# Default config for unknown models
DEFAULT_CONFIG: ModelConfig = {
    "num_ctx": 2048,
    "num_predict": 100,
    "temperature": 0.7,
    "timeout": 60,
}


def get_model_config(model_name: str) -> ModelConfig:
    """Get configuration for a specific model.
    
    Args:
        model_name: The model identifier (e.g., "smollm2:360m", "gpt-4")
        
    Returns:
        ModelConfig with optimal parameters for the model.
        Returns DEFAULT_CONFIG if model is not found.
    """
    return MODEL_CONFIGS.get(model_name, DEFAULT_CONFIG)
