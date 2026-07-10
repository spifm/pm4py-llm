from source.core.dfg.dfg_filter import DFGFilter
from source.core.dfg.dfg_frequency import get_min_transition_frequency
from source.core.dfg.dfg_simplifier import DFGSimplifier
from source.core.dfg.dfg_transformer import DFGTransformer
import os
from config.constants import *
from source.helpers.filename_getter import Filename
from source.helpers.info_writer import InfoWriter
import logging

logger = logging.getLogger(__name__)
output_dir = "/output"

class SimplifyDFGService:
    @staticmethod
    def simplify_dfg(
        output_path: str
    ) -> dict:

        fn = Filename()
        dfg_simplifier = DFGSimplifier()
        dfg_transformer = DFGTransformer()
        dfg_filter = DFGFilter()
        
        input_dir = os.path.join(output_dir, output_path)
        dfg_file = os.path.join(input_dir, fn.get_filename("dfg.json"))

        if not os.path.exists(dfg_file):
            raise ValueError("DFG file not found.")

        logger.info("Transforming DFG JSON to use generic activity names...")
        json_dfg_file = fn.get_filename_path("dfg.json", input_dir)
        json_dfg_generics_file = fn.get_filename_path("dfg.json_generic_act", input_dir)
        json_activity_mapping_file = fn.get_filename_path("dfg.json_activity_mapping_from_dfg", input_dir)

        dfg_transformer.dfg_json_replace_activities_with_generics(
            input_json_path=json_dfg_file,
            output_json_path=json_dfg_generics_file,
            mapping_output_path=json_activity_mapping_file
        )

        # Evaluate if the prompt is within token limits
        json_dfg_to_simplify = json_dfg_generics_file
        max_attempts = 3
        for i in range(max_attempts):
            is_within_limit = dfg_simplifier.eval_fit_json_prompt_tokens(json_dfg_to_simplify)
            if is_within_limit:
                logger.info("Prompt is within token limits, proceeding with simplification.")
                break

            try:
                # Start from the least frequent transitions: filter out the
                # current minimum frequency tier and re-evaluate on next pass.
                min_freq = get_min_transition_frequency(json_dfg_to_simplify)
                if min_freq is None:
                    logger.warning("No transitions left to filter; stopping reduction.")
                    break

                logger.info(
                    f"Prompt exceeds token limits, attempting to simplify further "
                    f"in try {i + 1} with frequency filter >{min_freq}."
                )
                reduced_dfg_filename = fn.get_filename_path("dfg.json_generic_act_filtered_by_freq", input_dir)
                info_writer = InfoWriter(input_dir)
                info_writer.write(
                    "\n\n=== DFG Pre-filtered to fit LLM context window ===\n\n"
                    f"Prompt exceeded the LLM token/context window (attempt {i + 1}); "
                    f"applied frequency filter with threshold >{min_freq} to reduce the DFG.\n"
                    f"Proceeding to filter the DFG...\n"
                )
                dfg_filter.filter_json_dfg_by_frequency(
                    json_dfg_path=json_dfg_to_simplify,
                    json_output_path=reduced_dfg_filename,
                    frequency_threshold=min_freq
                )
                json_dfg_to_simplify = reduced_dfg_filename
            except Exception as e:
                logger.error(f"Error during DFG filtering attempt {i + 1} with frequency threshold >{min_freq}: {e}")
                raise
        else:
            if not dfg_simplifier.eval_fit_json_prompt_tokens(json_dfg_to_simplify):
                logger.error(f"Prompt exceeds token limits after {max_attempts} attempts.")


        # Simplify DFG using LLM
        print(f"Simplifying DFG in json ({json_dfg_to_simplify}) using LLM...")
        llm_simplified_dfg_file = fn.get_filename_path("dfg.json_llm_simplified", input_dir)
        dfg_simplifier.simplify(json_dfg_to_simplify, llm_simplified_dfg_file)
        
        print("Restoring simplified DFG in json to use original activity names...")
        llm_restored_simplified_dfg_file = fn.get_filename_path("dfg.json_llm_restored_simplified", input_dir)

        dfg_transformer.dfg_json_restore_activity_names(
            act_json_path=llm_simplified_dfg_file,
            mapping_path=json_activity_mapping_file,
            output_json_path=llm_restored_simplified_dfg_file,
            add_activity_numbers=True
        )

        print("Restoring simplified DFG in json to pm4py DFG format...")
        simplified_dfg_file = fn.get_filename_path("dfg.simplified", input_dir)
        dfg_transformer.dfg_named_json_to_pm4py(
            named_json_path=llm_restored_simplified_dfg_file,
            dfg_output_path=simplified_dfg_file
        )

        output_analysis = fn.get_filename_path("dfg.simplified_analysis", input_dir)
        dfg_simplifier.analyze_simplified_dfg(llm_restored_simplified_dfg_file, output_analysis)

        image_formats = dfg_simplifier.config['llm']['dfg']['simplify_dfg']['image_formats']
        simplified_dfg_images = fn.get_filename_paths_for_formats("dfg.simplified_image", input_dir, image_formats)
        dfg_simplifier.convert_dfg_to_image(simplified_dfg_file, list(simplified_dfg_images.values()))
        dfg_simplifier.compute_simplification_info(
            original_dfg_path=os.path.join(input_dir, fn.get_filename("dfg.raw")),
            simplified_dfg_path=simplified_dfg_file
        )

        return {
            "output_analysis": output_analysis,
            "llm_simplified_dfg": llm_restored_simplified_dfg_file,
            "simplified_dfg": simplified_dfg_file,
            "simplified_dfg_images": simplified_dfg_images
        }
