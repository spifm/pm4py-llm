from pathlib import Path

class PromptLoader:

    @staticmethod
    def load_template(prompt_path: str) -> str:
        """
        Load a prompt template from a text file.

        Args:
            prompt_path: Relative or absolute path to the prompt file.

        Returns:
            The prompt text content.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        path = Path(prompt_path)
        base_path = 'config'

        if not path.is_absolute():
            path = Path(base_path) / path
            path = path.resolve()

        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")

        return path.read_text(encoding="utf-8")