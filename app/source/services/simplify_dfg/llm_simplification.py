import logging
import os

logger = logging.getLogger(__name__)


class LlmSimplification:
    """Runs the LLM simplification step and produces the final artifacts.

    Takes a DFG (with generic activity names) that already fits the LLM context
    window, simplifies it, restores the original activity names and generates
    the pm4py DFG, analysis, images and simplification metrics.
    """

    def __init__(self, dfg_simplifier, dfg_transformer, fn):
        self._dfg_simplifier = dfg_simplifier
        self._dfg_transformer = dfg_transformer
        self._fn = fn

    def run(self, json_dfg_to_simplify: str, mapping_file: str, input_dir: str) -> dict:
        fn = self._fn

        logger.info("Simplifying DFG in json (%s) using LLM...", json_dfg_to_simplify)
        llm_simplified_dfg_file = fn.get_filename_path("dfg.json_llm_simplified", input_dir)
        self._dfg_simplifier.simplify(json_dfg_to_simplify, llm_simplified_dfg_file)

        logger.info("Restoring simplified DFG in json to use original activity names...")
        llm_restored_simplified_dfg_file = fn.get_filename_path(
            "dfg.json_llm_restored_simplified", input_dir
        )
        self._dfg_transformer.dfg_json_restore_activity_names(
            act_json_path=llm_simplified_dfg_file,
            mapping_path=mapping_file,
            output_json_path=llm_restored_simplified_dfg_file,
            add_activity_numbers=True,
        )

        logger.info("Restoring simplified DFG in json to pm4py DFG format...")
        simplified_dfg_file = fn.get_filename_path("dfg.simplified", input_dir)
        self._dfg_transformer.dfg_named_json_to_pm4py(
            named_json_path=llm_restored_simplified_dfg_file,
            dfg_output_path=simplified_dfg_file,
        )

        output_analysis = fn.get_filename_path("dfg.simplified_analysis", input_dir)
        self._dfg_simplifier.analyze_simplified_dfg(
            llm_restored_simplified_dfg_file, output_analysis
        )

        image_formats = self._dfg_simplifier.config["llm"]["dfg"]["simplify_dfg"]["image_formats"]
        simplified_dfg_images = fn.get_filename_paths_for_formats(
            "dfg.simplified_image", input_dir, image_formats
        )
        self._dfg_simplifier.convert_dfg_to_image(
            simplified_dfg_file, list(simplified_dfg_images.values())
        )
        self._dfg_simplifier.compute_simplification_info(
            original_dfg_path=os.path.join(input_dir, fn.get_filename("dfg.raw")),
            simplified_dfg_path=simplified_dfg_file,
        )

        return {
            "output_analysis": output_analysis,
            "llm_simplified_dfg": llm_restored_simplified_dfg_file,
            "simplified_dfg": simplified_dfg_file,
            "simplified_dfg_images": simplified_dfg_images,
        }
