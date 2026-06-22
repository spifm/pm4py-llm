from models.schema import Result
from helpers.get_filename_helper import GetFilenameHelper
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ResultBuilder:

    def __init__(self):
        self.file_helper = GetFilenameHelper()

    def build_result(self, results_directory: str) -> Result:
        """
        Builds a result object from the specified results directory.
        """
        result = Result(
            results_directory=results_directory,
            files={
                "analysis": self.file_helper.get_analysis_filename(),
            }
        )

        summary_filename = self.file_helper.get_summary_filename()
        if (Path(results_directory) / summary_filename).exists():
            result.files["summary"] = summary_filename
        else:
            logger.warning(
                "Summary file '%s' not found in '%s'; skipping it from publication.",
                summary_filename,
                results_directory,
            )

        image_paths = [
            image_path
            for image_path in sorted(Path(results_directory).glob(self.file_helper.get_image_filename_pattern()))
            if image_path.suffix != ".dfg"
        ]
        if not image_paths:
            raise FileNotFoundError(
                f"No simplified DFG images found matching {self.file_helper.get_image_filename_pattern()}"
            )

        for image_path in image_paths:
            result.files[f"image_{image_path.suffix.lstrip('.')}"] = image_path.name

        return result
