class GetFilenameHelper:

    def __init__(self):
        self.analysis_filename = "simplified-dfg-analysis.txt"
        self.image_filename = "simplified-dfg.svg"

    def get_analysis_filename(self) -> str:
        return self.analysis_filename
    
    def get_image_filename(self) -> str:
        return self.image_filename