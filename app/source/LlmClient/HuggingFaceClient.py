from huggingface_hub import InferenceClient
from .LlmClientInterface import LlmClientInterface

class HuggingFaceClient(LlmClientInterface):

    def exec_prompt(self, prompt: str, output_file: str) -> str | None:
        if self.config["llm"]['huggingface']['model_type'] == 'text-generation-inference':
            self._exec_prompt_for_huggingface_text_generation_inference(prompt, output_file)
        elif self.config["llm"]['huggingface']['model_type'] == 'vllm':
            self._exec_prompt_for_huggingface_vllm(prompt, output_file)
        else:
            self.logger.error("Huggingface model type not supported")

    def _exec_prompt_for_huggingface_text_generation_inference(self, prompt, output_file):
        try:
            client = InferenceClient(
                self.config["llm"]['huggingface']['model_name'],
                token=self.config["llm"]['huggingface']['hugging_face_api_key'],
            )

            with open(output_file, 'a') as f:
                for message in client.chat_completion(
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=self.config["llm"]['huggingface']['max_tokens'],
                        stream=True,
                    ):
                    f.write(message.choices[0].delta.content)
                f.write("\n\n")
        except Exception as e:
            self.logger.exception(f"Error executing prompt with Huggingface Text Generation Inference: {e}")
            raise


    def _exec_prompt_for_huggingface_vllm(self, prompt, output_file):
        # TODO: Implement VLLM
        pass

    
    def exec_json_prompt(self, prompt: str, output_file: str) -> str | None:
        return self.exec_prompt(prompt, output_file)
