from source.DFGSimplifier import DFGSimplifier
from source.DFGTransformer import DFGTransformer
import os
from config.constants import *
from source.Filename import Filename
import logging

logger = logging.getLogger(__name__)

class SimplifyDFGService:
    @staticmethod
    def simplify_dfg(
        output_path: str,
        prompt_context: str = None
    ) -> dict:

        fn = Filename()
        simplifier = DFGSimplifier()
        transformer = DFGTransformer()
        
        input_dir = os.path.join(OUTPUT_PATH, output_path)
        dfg_file = os.path.join(input_dir, fn.get_filename("dfg.json"))

        if not os.path.exists(dfg_file):
            raise ValueError("DFG file not found.")
        
        if prompt_context is not None:
            simplifier.set_context_prompt(prompt_context)
            logger.debug(f"Context prompt updated: {simplifier.get_context_prompt()}")


        print("Transforming DFG JSON to use generic activity names...")
        json_dfg_file = fn.get_filename_path("dfg.json", input_dir)
        json_dfg_generics_file = fn.get_filename_path("dfg.json_generic_act", input_dir)
        json_activity_mapping_file = fn.get_filename_path("dfg.json_activity_mapping_from_dfg", input_dir)

        transformer.dfg_json_replace_activities_with_generics(
            input_json_path=json_dfg_file,
            output_json_path=json_dfg_generics_file,
            mapping_output_path=json_activity_mapping_file
        )

        print(f"Simplifying DFG in json ({json_dfg_generics_file}) using LLM...")
        llm_simplified_dfg_file = fn.get_filename_path("dfg.json_llm_simplified", input_dir)
        simplifier.simplify_dfg(json_dfg_generics_file, llm_simplified_dfg_file)
        
        print("Restoring simplified DFG in json to use original activity names...")
        llm_restored_simplified_dfg_file = fn.get_filename_path("dfg.json_llm_restored_simplified", input_dir)

        transformer.dfg_json_restore_activity_names(
            act_json_path=llm_simplified_dfg_file,
            mapping_path=json_activity_mapping_file,
            output_json_path=llm_restored_simplified_dfg_file
        )

        print("Restoring simplified DFG in json to pm4py DFG format...")
        simplified_dfg_file = fn.get_filename_path("dfg.simplified", input_dir)
        transformer.dfg_named_json_to_pm4py(
            named_json_path=llm_restored_simplified_dfg_file,
            dfg_output_path=simplified_dfg_file
        )

        output_analysis = fn.get_filename_path("dfg.simplified_analysis", input_dir)
        simplifier.analyze_simplified_dfg(llm_restored_simplified_dfg_file, output_analysis)

        simplified_dfg_image = fn.get_filename_path("dfg.simplified_image", input_dir)
        simplifier.convert_dfg_to_image(simplified_dfg_file, simplified_dfg_image)

        simplifier.compute_simplification_info(
            original_dfg_path=os.path.join(input_dir, fn.get_filename("dfg.raw")),
            simplified_dfg_path=simplified_dfg_file
        )

        return {
            "output_analysis": output_analysis,
            "llm_simplified_dfg": llm_restored_simplified_dfg_file,
            "simplified_dfg": simplified_dfg_file,
            "simplified_dfg_image": simplified_dfg_image
        }