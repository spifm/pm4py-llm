from abc import ABC, abstractmethod
from typing import Any, Dict
from logging import Logger

class LlmClientInterface(ABC):
    def __init__(self, config: Dict[str, Any], logger: Logger):
        self.config = config
        self.logger = logger
        self._init_config()

    def _get_dfg_json_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "start_activities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "activity": {"type": "string"},
                        "freq": {"type": "integer", "minimum": 1}
                    },
                    "required": ["activity", "freq"],
                    "additionalProperties": False
                }
                },
                "end_activities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "activity": {"type": "string"},
                        "freq": {"type": "integer", "minimum": 1}
                    },
                    "required": ["activity", "freq"],
                    "additionalProperties": False
                }
                },
                "transitions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "src": {"type": "string"},
                        "tgt": {"type": "string"},
                        "freq": {"type": "integer", "minimum": 1}
                    },
                    "required": ["src", "tgt", "freq"],
                    "additionalProperties": False
                }
                }
            },
            "required": ["start_activities", "end_activities", "transitions"],
            "additionalProperties": False
        }
    
    @abstractmethod
    def _init_config(self) -> None:
        ...

    @abstractmethod
    def exec_prompt(self, prompt: str, output_file: str) -> Dict [str, Any] | None:
        ...

    @abstractmethod
    def exec_json_prompt(self, prompt: str, output_file: str) -> Dict[str, Any] | None:
        ...

    @abstractmethod
    def eval_max_tokens_for_json_prompt(self, prompt: str) -> bool:
        ...
