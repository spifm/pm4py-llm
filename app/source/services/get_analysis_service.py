import os
from source.helpers.filename_getter import Filename

class GetAnalysisService:

    def __init__(self):
        self.fn = Filename()
    
    def get_analysis_files(self, output_dir):
        """
        Returns a dictionary with the content of all analysis files in the output_dir.
        The keys of the dictionary are the filenames without extension.
        """
        if not os.path.exists(output_dir):
            raise FileNotFoundError(f"Output directory '{output_dir}' does not exist.")
        
        dfg_analysis = self.fn.get_filename_path("dfg.analysis", output_dir)
        if not os.path.exists(dfg_analysis):
            dfg_analysis = 'No analysis file found for DFG.'

        return {
            "dfg_analysis": dfg_analysis,
            "dfg_image": self.fn.get_filename_path("dfg.image", output_dir),
            "simplified_dfg_analysis": self.fn.get_filename_path("dfg.simplified_analysis", output_dir),
            "simplified_dfg_image": self.fn.get_filename_path("dfg.simplified_image", output_dir)
        }
    
    def get_simplified_analysis_files(self, output_dir):
        """
        Returns a dictionary with the content of all analysis files in the output_dir.
        The keys of the dictionary are the filenames without extension.
        """
        return {
            "simplified_dfg_analysis": self.fn.get_filename_path("dfg.simplified_analysis", output_dir),
            "simplified_dfg_image": self.fn.get_filename_path("dfg.simplified_image", output_dir)
        }