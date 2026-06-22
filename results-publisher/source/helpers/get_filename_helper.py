class GetFilenameHelper:

    def __init__(self):
        self.analysis_filename = "simplified-dfg-analysis.txt"
        self.summary_filename = "simplified-dfg-summary.txt"
        self.image_filename_pattern = "simplified-dfg.*"

    def get_analysis_filename(self) -> str:
        return self.analysis_filename

    def get_summary_filename(self) -> str:
        return self.summary_filename

    def get_image_filename_pattern(self) -> str:
        return self.image_filename_pattern
