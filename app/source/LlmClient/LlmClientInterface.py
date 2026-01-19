from abc import ABC, abstractmethod
from typing import Any, Dict
from logging import Logger

class LlmClientInterface(ABC):
    def __init__(self, config: Dict[str, Any], logger: Logger):
        self.config = config
        self.logger = logger

    @abstractmethod
    def exec_prompt(self, prompt: str, output_file: str) -> str | None:
        ...
