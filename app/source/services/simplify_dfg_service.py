from source.core.dfg.dfg_filter import DFGFilter
from source.core.dfg.dfg_simplifier import DFGSimplifier
from source.core.dfg.dfg_transformer import DFGTransformer
import os
from config.constants import *
from source.helpers.filename_getter import Filename
import logging

logger = logging.getLogger(__name__)
output_dir = "/output"

class SimplifyDFGService:
    @staticmethod
    def simplify_dfg(
        output_path: str,
        prompt_context: str = None
    ) -> dict:

        fn = Filename()
        dfg_simplifier = DFGSimplifier()
        dfg_transformer = DFGTransformer()
        dfg_filter = DFGFilter()
        
        input_dir = os.path.join(output_dir, output_path)
        dfg_file = os.path.join(input_dir, fn.get_filename("dfg.json"))

        if not os.path.exists(dfg_file):
            raise ValueError("DFG file not found.")
        
        if prompt_context is not None:
            dfg_simplifier.set_context_prompt(prompt_context)
            logger.debug(f"Context prompt updated: {dfg_simplifier.get_context_prompt()}")


        print("Transforming DFG JSON to use generic activity names...")
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
            else:
                if i == max_attempts - 1:
                    logger.error(f"Prompt exceeds token limits after {max_attempts} attempts.")
                else:
                    try:
                        logger.info(f"Prompt exceeds token limits, attempting to simplify further in try {i+1}.")
                        reduced_dfg_filename = fn.get_filename_path("dfg.json_generic_act_filtered_by_freq", input_dir)
                        dfg_filter.filter_json_dfg_by_frequency(
                            json_dfg_path=json_dfg_to_simplify,
                            json_output_path=reduced_dfg_filename,
                            frequency_threshold=i + 1 # TODO Find better strategy
                        )
                        json_dfg_to_simplify = reduced_dfg_filename
                    except Exception as e:
                        logger.error(f"Error during DFG filtering attempt {i+1}: {e}")
                        raise

        # Update transitions ratios to retain/remove if dfg was filtered
        if json_dfg_generics_file != json_dfg_to_simplify:
            dfg_simplifier.update_transition_ratios(json_dfg_generics_file, json_dfg_to_simplify)

        # Simplify DFG using LLM
        print(f"Simplifying DFG in json ({json_dfg_to_simplify}) using LLM...")
        llm_simplified_dfg_file = fn.get_filename_path("dfg.json_llm_simplified", input_dir)
        dfg_simplifier.simplify(json_dfg_to_simplify, llm_simplified_dfg_file)
        
        print("Restoring simplified DFG in json to use original activity names...")
        llm_restored_simplified_dfg_file = fn.get_filename_path("dfg.json_llm_restored_simplified", input_dir)

        dfg_transformer.dfg_json_restore_activity_names(
            act_json_path=llm_simplified_dfg_file,
            mapping_path=json_activity_mapping_file,
            output_json_path=llm_restored_simplified_dfg_file
        )

        print("Restoring simplified DFG in json to pm4py DFG format...")
        simplified_dfg_file = fn.get_filename_path("dfg.simplified", input_dir)
        dfg_transformer.dfg_named_json_to_pm4py(
            named_json_path=llm_restored_simplified_dfg_file,
            dfg_output_path=simplified_dfg_file
        )

        output_analysis = fn.get_filename_path("dfg.simplified_analysis", input_dir)
        dfg_simplifier.analyze_simplified_dfg(llm_restored_simplified_dfg_file, output_analysis)

        simplified_dfg_image = fn.get_filename_path("dfg.simplified_image", input_dir)
        dfg_simplifier.convert_dfg_to_image(simplified_dfg_file, simplified_dfg_image)
        dfg_simplifier.compute_simplification_info(
            original_dfg_path=os.path.join(input_dir, fn.get_filename("dfg.raw")),
            simplified_dfg_path=simplified_dfg_file
        )

        return {
            "output_analysis": output_analysis,
            "llm_simplified_dfg": llm_restored_simplified_dfg_file,
            "simplified_dfg": simplified_dfg_file,
            "simplified_dfg_image": simplified_dfg_image
        }