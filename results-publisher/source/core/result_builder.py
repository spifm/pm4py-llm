from models.schema import Result
from helpers.get_filename_helper import GetFilenameHelper

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
                "image": self.file_helper.get_image_filename(),
            }
        )
        return result