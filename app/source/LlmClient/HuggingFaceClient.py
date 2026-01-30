from huggingface_hub import InferenceClient
from .LlmClientInterface import LlmClientInterface
from typing import Any, Dict

class HuggingFaceClient(LlmClientInterface):

    def _init_config(self) -> None:
        config = self.config["llm"]['huggingface']
        self.model_name = config['model_name']
        self.model_type = config['model_type']
        self.api_key = config['hugging_face_api_key']
        self.max_tokens = config['max_tokens']

    def exec_prompt(self, prompt: str, output_file: str) -> Dict [str, Any] | None:
        if self.model_type == 'text-generation-inference':
            return self._exec_prompt_for_huggingface_text_generation_inference(prompt, output_file)
        elif self.model_type == 'vllm':
            return self._exec_prompt_for_huggingface_vllm(prompt, output_file)
        else:
            raise ValueError("Huggingface model type not supported")

    def _exec_prompt_for_huggingface_text_generation_inference(self, prompt, output_file) -> Dict [str, Any] | None:
        try:
            client = InferenceClient(
                self.model_name,
                token=self.api_key,
            )

            with open(output_file, 'a') as f:
                for message in client.chat_completion(
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=self.max_tokens,
                        stream=True,
                    ):
                    f.write(message.choices[0].delta.content)
                f.write("\n\n")
        except Exception as e:
            self.logger.exception(f"Error executing prompt with Huggingface Text Generation Inference: {e}")
            raise


    def _exec_prompt_for_huggingface_vllm(self, prompt, output_file) -> Dict [str, Any] | None:
        # TODO: Implement VLLM
        raise NotImplementedError("Huggingface VLLM client not implemented yet.")

    
    def exec_json_prompt(self, prompt: str, output_file: str) -> Dict [str, Any] | None:
        return self.exec_prompt(prompt, output_file)
    

    def eval_max_tokens_for_json_prompt(self, prompt: str) -> bool:
        self.logger.warning("Token counting not implemented for HuggingFaceClient.")
        return True
