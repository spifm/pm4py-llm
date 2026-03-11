import os


class Filename:

    FILENAMES = {
        "info": "info.txt",
        "petri_net": {
            "image": "petri_net.png",
            "raw": "petri_net.pnml",
            "abstract": "abstract-petri-net.txt"
        },
        "bpmn": {
            "image": "bpmn.png"
        },
        "dfg": {
            "image": "dfg.png",
            "raw": "dfg.dfg",
            "abstract": "abstract-dfg.txt",
            "analysis": "dfg-analysis.txt",
            "llm_simplified": "llm-simplified-dfg.txt",
            "simplified": "simplified-dfg.dfg",
            "simplified_image": "simplified-dfg.png",
            "simplified_analysis": "simplified-dfg-analysis.txt",
            "json": "dfg.json",
            "json_activity_mapping_from_dfg": "dfg-activity_mapping.json",
            "json_generic_act_filtered_by_freq": "dfg-generic-activities-filtered-by-freq.json",
            "json_generic_act": "dfg-generic-activities.json",
            "json_llm_simplified": "llm-simplified-dfg.json",
            "json_llm_restored_simplified": "llm-restored-simplified-dfg.json",
            "performance_image": "performance-dfg.png",
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

