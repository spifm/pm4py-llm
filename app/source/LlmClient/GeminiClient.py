from google import genai
from .LlmClientInterface import LlmClientInterface
from typing import Dict, Any
import time
from datetime import datetime, timezone

class GeminiClient(LlmClientInterface):

    def _init_config(self) -> None:
        config = self.config["llm"]['gemini']
        self.model_name = config['model_name']
        self.api_key = config['api_key']

    def _gemini_metrics(self, response, t0_perf: float, t1_perf: float) -> dict:
        um = getattr(response, "usage_metadata", None)

        prompt_tokens = getattr(um, "prompt_token_count", 0) if um else 0
        output_tokens = getattr(um, "candidates_token_count", 0) if um else 0
        thoughts_tokens = getattr(um, "thoughts_token_count", 0) if um else 0
        total_tokens = getattr(um, "total_token_count", 0) if um else 0

        latency_ms = (t1_perf - t0_perf) * 1000.0

        return {
            "Input tokens": int(prompt_tokens),
            "Output tokens": int(output_tokens),
            "Total duration ms": round(latency_ms, 4),
            "thoughts_token_count": int(thoughts_tokens),
            "total_token_count": int(total_tokens),
        }
    
    def exec_prompt(self, prompt: str, output_file: str) -> Dict [str, Any] | None:
        t0 = time.perf_counter()
        try:
            client = genai.Client(api_key=self.api_key)

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            t1 = time.perf_counter()

        except Exception as e:
            self.logger.error(f"Error during Gemini request: {e}")
            raise

        self.logger.debug(f"Gemini response: {response}")

        with open(output_file, 'a') as f:
            f.write(response.text + "\n\n")

        return self._gemini_metrics(response, t0, t1)
    
    
    def exec_json_prompt(self, prompt: str, output_file: str) -> Dict [str, Any] | None:
        return self.exec_prompt(prompt, output_file)
    
    
    def eval_max_tokens_for_json_prompt(self, prompt: str) -> bool:
        self.logger.warning("Token counting not implemented for GeminiClient.")
        return True