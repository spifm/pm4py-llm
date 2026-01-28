import requests
from .LlmClientInterface import LlmClientInterface

class OllamaClient(LlmClientInterface):

    def _exec_ollama_prompt(self, prompt: str, output_file: str, payload: dict, url: str) -> str | None:

        self.logger.debug(f"URL: {url}")

        max_len = 500
        prompt_preview = prompt if len(prompt) <= max_len else prompt[:max_len] + "..."
        self.logger.debug(f"Simplificated prompt (truncated to {max_len} chars): {prompt_preview}")

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.logger.exception(f"Error in Ollama request: {e}")
            return None

        self.logger.info(f"Response status code: {response.status_code}")
        self.logger.debug(f"Response content: {response.content}")
        json_response = response.json()

        if "message" in json_response:
            result = json_response["message"]["content"]
        elif "response" in json_response:
            result = json_response["response"]
        else:
            self.logger.error("Unexpected response format from Ollama API.")
            raise ValueError(f"Unexpected response format from Ollama API.")
            

        self.logger.debug(f"Response content result: {result}")

        with open(output_file, 'a') as f:
            f.write(result + "\n\n")

        return result


    def exec_json_prompt(self, prompt: str, output_file: str) -> str | None:
        ollama_config = self.config["llm"]['ollama']
        ollama_json_prompt_config = ollama_config.get('json_prompt_config', {})

        url_domain = ollama_json_prompt_config.get('api_url', ollama_config['api_url'])
        endpoint = ollama_json_prompt_config.get('api_endpoint', ollama_config['api_endpoint'])
        url = f"{url_domain}{endpoint}"

        payload = {
            "format": "json",
            "model": ollama_json_prompt_config.get('model_name', ollama_config['model_name']),
            "stream": False,
            "options": ollama_json_prompt_config.get('options', ollama_config['options']),
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "prompt": prompt
        }

        return self._exec_ollama_prompt(prompt, output_file, payload, url)

    def exec_prompt(self, prompt: str, output_file: str) -> str | None:
        ollama_config = self.config["llm"]['ollama']
        url = f"{ollama_config['api_url']}{ollama_config['api_endpoint']}"

        payload = {
            "model": ollama_config['model_name'],
            "stream": False,
            "options": ollama_config['options'],
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "prompt": prompt
        }

        return self._exec_ollama_prompt(prompt, output_file, payload, url)