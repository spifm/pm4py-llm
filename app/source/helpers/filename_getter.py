import os


class Filename:

    FILENAMES = {
        "info": "info.txt",
        "petri_net": {
            "image": "petri_net.png",
            "raw": "petri_net.pnml",
            "abstract": "abstract-petri-net.txt",
            "analysis": "petri_net-analysis.txt",
        },
        "bpmn": {
            "image": "bpmn.png"
        },
        "dfg": {
            "image": "dfg.FORMAT",
            "raw": "dfg.dfg",
            "abstract": "abstract-dfg.txt",
            "analysis": "dfg-analysis.txt",
            "llm_simplified": "llm-simplified-dfg.txt",
            "simplified": "simplified-dfg.dfg",
            "simplified_image": "simplified-dfg.FORMAT",
            "simplified_analysis": "simplified-dfg-analysis.txt",
            "simplified_summary": "simplified-dfg-summary.txt",
            "json": "dfg.json",
            "json_activity_mapping_from_dfg": "dfg-activity_mapping.json",
            "json_filtered_by_freq": "filtered-dfg.json",
            "raw_filtered_by_freq": "filtered-dfg.dfg",
            "image_filtered_by_freq": "filtered-dfg.FORMAT",
            "json_generic_act_filtered_by_freq": "dfg-generic-activities-filtered-by-freq.json",
            "json_generic_act": "dfg-generic-activities.json",
            "json_llm_simplified": "llm-simplified-dfg.json",
            "json_llm_restored_simplified": "llm-restored-simplified-dfg.json",
            "performance_image": "performance-dfg.png",
        },
        "temporal_profile": {
            "analysis": "temporal_profile-analysis.txt",
        },
        "mermaid": {
            "simplified_mind_map": "simplified-mind_map.mmd",
            "simplified_mind_map_image": "simplified-mind_map.FORMAT" # FORMAT will be replaced
        }
    }
    

    def get_filename(self, dotted_key, default=None):
        """
        Access to Filename.FILENAMES using dot notation.
        Examples:
          - "dfg.image"  -> FILENAMES["dfg"]["image"]
          - "bpmn.image" -> FILENAMES["bpmn"]["image"]
        """
        node = self.FILENAMES
        for part in dotted_key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node


    def get_filename_path(self, dotted_key, output_dir) -> str:
        """
        Returns the full path combining output_dir + constant filename.
        Example:
          get_filename_path("dfg.raw", output_dir)
        """
        filename = self.get_filename(dotted_key)
        if filename is None:
            raise KeyError(f"Filename key '{dotted_key}' not found in Filename.FILENAMES")
        return os.path.join(output_dir, filename)


    def get_filename_for_format(self, dotted_key, image_format: str) -> str:
        filename = self.get_filename(dotted_key)
        if filename is None:
            raise KeyError(f"Filename key '{dotted_key}' not found in Filename.FILENAMES")
        return filename.replace("FORMAT", image_format)


    def get_filename_path_for_format(self, dotted_key, output_dir, image_format: str) -> str:
        return os.path.join(output_dir, self.get_filename_for_format(dotted_key, image_format))


    def get_filename_paths_for_formats(self, dotted_key, output_dir, image_formats: list[str]) -> dict[str, str]:
        return {
            image_format: self.get_filename_path_for_format(dotted_key, output_dir, image_format)
            for image_format in image_formats
        }

