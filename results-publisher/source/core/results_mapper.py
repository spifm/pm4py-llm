from helpers.get_filename_helper import GetFilenameHelper
from datetime import datetime
from pathlib import Path;

class ResultMapper:

    def __init__(self):
        self.file_helper = GetFilenameHelper()

    def get_file_maps(self) -> dict:
        """
        Maps the original filenames to new filenames based on the current date and original file extensions.
        Returns:
            dict: A dictionary mapping original filenames to new filenames.
        """

        yyyymmdd = datetime.now().strftime("%Y%m%d")

        analysis_filename = self.file_helper.get_analysis_filename()
        analysis_filename_extension = Path(analysis_filename).suffix
        image_filename = self.file_helper.get_image_filename()
        image_filename_extension = Path(image_filename).suffix

        return {
            analysis_filename: f"{yyyymmdd}{analysis_filename_extension}",
            image_filename: f"{yyyymmdd}{image_filename_extension}"
        }