from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class CleanJson:
    @staticmethod
    def clean_json(file_path: str) -> None:
        """
        Cleans a JSON file by removing leading and trailing code fences if present,
        and then loads the cleaned content as a JSON object.

        Args:
            file_path: Path to the JSON file to be cleaned.
        Returns:
            A dictionary containing the cleaned JSON content, or None if an error occurs.
        """
        CleanJson._clean_json_fences(file_path)

    @staticmethod
    def _clean_json_fences(file_path: str) -> None:
        """
        Removes leading ```json and trailing ``` fences from a file if present.
        Modifies the file in place.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        content = path.read_text(encoding="utf-8").strip()

        if content.startswith("```json"):
            content = content[len("```json"):].lstrip()
            logger.debug("Removed leading ```json fence from JSON content.")

        if content.endswith("```"):
            content = content[:-3].rstrip()
            logger.debug("Removed trailing ``` fence from JSON content.")

        path.write_text(content + "\n", encoding="utf-8")