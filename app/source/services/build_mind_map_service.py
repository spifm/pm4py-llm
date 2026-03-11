from source.mind_map.mind_map_builder import MindMapBuilder
from source.mind_map.mind_map_render import MindMapRender
from typing import Dict
from source.Filename import Filename
from source.Config import Config
import logging
import os

logger = logging.getLogger(__name__)

class MindMapBuilderService:

    def __init__(self):
        self.fn = Filename()
        self.mind_map_builder = MindMapBuilder()
        self.mind_map_render = MindMapRender()
        self.config = Config().get()
        self.image_format = self.config['mermaid']['image_format']
   
    def build_mind_map(
        self,
        output_path: str
    ) -> Dict[str, str]:
        
        logger.info("Starting MindMapBuilderService")

        # Get Simplified DFG analysis from the output path
        llm_simplified_analysis_path = self.fn.get_filename_path("dfg.simplified_analysis", output_path)
        if not os.path.exists(llm_simplified_analysis_path):
            raise FileNotFoundError(f"Simplified DFG analysis file not found: {llm_simplified_analysis_path}")
        with open(llm_simplified_analysis_path, 'r', encoding='utf-8') as f:
            simplified_analysis = f.read()
        
        # Build the mind map using the analysis and store it in a file
        simplified_mind_map_path = self.fn.get_filename_path("mermaid.simplified_mind_map", output_path)
        mind_map = self.mind_map_builder.build_mind_map(simplified_analysis, simplified_mind_map_path)

        # TODO: use a new container to generate the image from the mind map file, and return both files (mind map file and image file)
        mind_map_image = self.mind_map_render.render_image(
            mind_map,
            self.image_format
        )

        mind_map_image_file = self.fn.get_filename_path(
            "mermaid.simplified_mind_map_image",
            output_path
        ).replace("FORMAT", self.image_format)

        self.mind_map_render.store_image(
            mind_map_image,
            mind_map_image_file
        )

        return {
            "mind_map_file": simplified_mind_map_path,
            "mind_map_image_file": mind_map_image_file
        }