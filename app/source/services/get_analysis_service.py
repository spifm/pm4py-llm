import os
from source.helpers.filename_getter import Filename
from source.Config import Config

class GetAnalysisService:

    def __init__(self):
        self.fn = Filename()
        config_instance = Config()
        config_instance.initialize()
        self.config = config_instance.get()
    
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
            "dfg_images": self.fn.get_filename_paths_for_formats(
                "dfg.image",
                output_dir,
                self.config['discovery']['dfg']['image_formats']
            ),
            "simplified_dfg_analysis": self.fn.get_filename_path("dfg.simplified_analysis", output_dir),
            "simplified_dfg_summary": self.fn.get_filename_path("dfg.simplified_summary", output_dir),
            "simplified_dfg_images": self.fn.get_filename_paths_for_formats(
                "dfg.simplified_image",
                output_dir,
                self.config['llm']['dfg']['simplify_dfg']['image_formats']
            )
        }
    
    def get_simplified_analysis_files(self, output_dir):
        """
        Returns a dictionary with the content of all analysis files in the output_dir.
        The keys of the dictionary are the filenames without extension.
        """
        return {
            "simplified_dfg_analysis": self.fn.get_filename_path("dfg.simplified_analysis", output_dir),
            "simplified_dfg_summary": self.fn.get_filename_path("dfg.simplified_summary", output_dir),
            "simplified_dfg_images": self.fn.get_filename_paths_for_formats(
                "dfg.simplified_image",
                output_dir,
                self.config['llm']['dfg']['simplify_dfg']['image_formats']
            )
        }
