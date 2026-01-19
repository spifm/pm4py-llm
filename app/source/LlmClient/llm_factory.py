from logging import Logger
from typing import Any, Dict
from .LlmClientInterface import LlmClientInterface
from .OpenAIClient import OpenAIClient
from .OllamaClient import OllamaClient
from .HuggingFaceClient import HuggingFaceClient

def create_llm_client(config: Dict[str, Any], logger: Logger) -> LlmClientInterface:
    provider = config["llm"]["llm_provider"]
    if provider == "openai":
        return OpenAIClient(config, logger)
    elif provider == "ollama":
        return OllamaClient(config, logger)
    elif provider == "huggingface":
        return HuggingFaceClient(config, logger)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
