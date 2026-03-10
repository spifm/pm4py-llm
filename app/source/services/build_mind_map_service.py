from source.mind_map.mind_map_builder import MindMapBuilder
import os
from source.Filename import Filename
import logging

logger = logging.getLogger(__name__)

class MindMapBuilderService:

    def __init__(self):
        self.fn = Filename()
   
    def build_mind_map(
        self,
        output_path: str
    ) -> str:
        
        logger.info("Starting MindMapBuilderService")

        # Get Simplified DFG analysis from the output path
        llm_simplified_analysis_path = self.fn.get_filename_path("dfg.simplified_analysis", output_path)
        if not os.path.exists(llm_simplified_analysis_path):
            raise FileNotFoundError(f"Simplified DFG analysis file not found: {llm_simplified_analysis_path}")
        with open(llm_simplified_analysis_path, 'r', encoding='utf-8') as f:
            simplified_analysis = f.read()
        
        # Build the mind map using the analysis
        builder = MindMapBuilder()
        mind_map_file = builder.build_mind_map(simplified_analysis, output_path)

        # TODO: use a new container to generate the image from the mind map file, and return both files (mind map file and image file)
        

        return mind_map_file