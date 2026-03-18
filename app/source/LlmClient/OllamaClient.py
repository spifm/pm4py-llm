import requests
from .LlmClientInterface import LlmClientInterface
from typing import Dict, Any
from source.helpers.clean_json import CleanJson
import time
import json

class OllamaClient(LlmClientInterface):

    def _init_config(self) -> None:
        config = self.config["llm"]['ollama']
        self.url = f"{config['api_url']}{config['api_endpoint']}"
        self.model_name = config['model_name']
        self.options = config.get('options', {})
        self.max_prompt_tokens = config.get('max_prompt_tokens', 0)
        self.think = config.get('think', False)

        json_config = config.get('json_prompt_config', config)
        json_url_domain = json_config.get('api_url', config['api_url'])
        json_endpoint = json_config.get('api_endpoint', config['api_endpoint'])
        self.json_url = f"{json_url_domain}{json_endpoint}"
        self.json_model_name = json_config.get('model_name', config['model_name'])
        self.json_options = json_config.get('options', config['options'])
        self.json_max_prompt_tokens = json_config.get('max_prompt_tokens', self.max_prompt_tokens)
        self.json_think = json_config.get('think', self.think)


    def _get_json_prompt_tokens(self, prompt: str) -> int:

        payload = {
            "model": self.json_model_name,
            "stream": False,
            "options": self.json_options,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "prompt": prompt
        }

        payload["num_predict"] = 0

        response = requests.post(self.json_url, json=payload)

        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.logger.exception(f"Error in Ollama request: {e}")
            return None

        json_response = response.json()
        self.logger.debug(f"get_json_prompt_tokens, prompt_eval_count: {json_response.get('prompt_eval_count', 'N/A')}")

        return int(json_response["prompt_eval_count"])


    def _exec_ollama_prompt(self, prompt: str, output_file: str, payload: dict, url: str) -> Dict [str, Any] | None:

        self.logger.debug(f"URL: {url}")

        max_len = 500
        prompt_preview = prompt if len(prompt) <= max_len else prompt[:max_len] + "..."
        self.logger.debug(f"Simplificated prompt (truncated to {max_len} chars): {prompt_preview}")

        try:
            t0_perf = time.perf_counter()
            response = requests.post(url, json=payload)
            response.raise_for_status()
            t1_perf = time.perf_counter()
        except requests.exceptions.RequestException as e:
            self.logger.exception(f"Error in Ollama request: {e}")
            raise

        self.logger.info(f"Response status code: {response.status_code}")
        self.logger.debug(f"Response content: {response.content}")
        json_response = response.json()

        if "message" in json_response:
            result = json_response["message"]["content"]
        elif "response" in json_response:
            result = json_response["response"]
        else:
            raise ValueError(f"Unexpected response format from Ollama API.")

        self.logger.debug(f"Response content result: {result}")

        with open(output_file, 'a') as f:
            f.write(result + "\n\n")

        # Get metrics to return them
        return {
            "Input tokens": json_response.get("prompt_eval_count", 0),
            "Output tokens": json_response.get("eval_count", 0),
            "Total duration ms": round((t1_perf - t0_perf) * 1000.0, 4),
            "total_duration (from Ollama) ms": int(json_response.get("total_duration", 0) or 0) / 1_000_000,
            "load_duration ms": int(json_response.get("load_duration", 0) or 0) / 1_000_000,
            "prompt_eval_duration ms": int(json_response.get("prompt_eval_duration", 0) or 0) / 1_000_000,
            "eval_duration ms": int(json_response.get("eval_duration", 0) or 0) / 1_000_000,
        }
    

    def exec_json_prompt(self, prompt: str, output_file: str) -> Dict [str, Any] | None:

        payload = {
            "format": self._get_dfg_json_schema(),
            "model": self.json_model_name,
            "stream": False,
            "options": self.json_options,
            "messages": [
                {"role": "user", "content": prompt},
            ],
        }

        if isinstance(self.json_think, dict):
            k, v = next(iter(self.json_think.items()))
            payload[k] = v

        metrics = self._exec_ollama_prompt(prompt, output_file, payload, self.json_url)

        CleanJson.clean_json(output_file)
        
        llm_info = {
            "Provider": "Ollama",
            "Model": self.json_model_name,
            "Think": (
                "Not specified (default value in LLM's API was used)"
                if self.json_think is False
                else json.dumps(self.json_think, ensure_ascii=False)
            ),
            "Options": json.dumps(self.json_options, ensure_ascii=False),
        }

        return {**llm_info, **metrics}


    def exec_prompt(self, prompt: str, output_file: str) -> Dict [str, Any] | None:

        payload = {
            "model": self.model_name,
            "stream": False,
            "options": self.options,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "prompt": prompt
        }

        if self.think is dict:
            k, v = next(iter(self.think.items()))
            payload[k] = v

        metrics = self._exec_ollama_prompt(prompt, output_file, payload, self.url)

        llm_info = {
            "Provider": "Ollama",
            "Model": self.model_name,
            "Think": (
                "Not specified (default value in LLM's API was used)"
                if self.think is False
                else json.dumps(self.think, ensure_ascii=False)
            ),
            "Options": json.dumps(self.options, ensure_ascii=False),
        }

        return {**llm_info, **metrics}


    def eval_max_tokens_for_json_prompt(self, prompt: str) -> bool:
        if self.json_max_prompt_tokens == 0:
            self.logger.warning("Ollama: Maximum prompt tokens for JSON not set; assuming no limit.")
            return True
        else:
            return self.json_max_prompt_tokens >= self._get_json_prompt_tokens(prompt)