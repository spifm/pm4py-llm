import os
import logging

from source.core.dfg.dfg_filter import DFGFilter
from source.core.dfg.dfg_simplifier import DFGSimplifier
from source.core.dfg.dfg_transformer import DFGTransformer
from source.helpers.filename_getter import Filename
from source.services.simplify_dfg.deterministic_prefilter import DeterministicPreFilter
from source.services.simplify_dfg.token_limit_reducer import TokenLimitReducer
from source.services.simplify_dfg.llm_simplification import LlmSimplification
from config.constants import *

logger = logging.getLogger(__name__)
output_dir = "/output"

class SimplifyDFGService:
    @staticmethod
    def simplify_dfg(
        output_path: str,
        deterministic_ratio: float | None = None,
    ) -> dict:

        fn = Filename()
        dfg_simplifier = DFGSimplifier()
        dfg_transformer = DFGTransformer()
        dfg_filter = DFGFilter()
        
        input_dir = os.path.join(output_dir, output_path)
        json_dfg_file = fn.get_filename_path("dfg.json", input_dir)

        if not os.path.exists(json_dfg_file):
            raise ValueError("DFG file not found.")

        prefilter = DeterministicPreFilter(dfg_filter, fn)
        reducer = TokenLimitReducer(dfg_simplifier, dfg_filter, fn)
        llm_step = LlmSimplification(dfg_simplifier, dfg_transformer, fn)

        # 1. Optional deterministic frequency pre-filter (top ratio% transitions).
        json_dfg_file = prefilter.apply(json_dfg_file, deterministic_ratio, input_dir)

        # 2. Encode: transform DFG JSON to use generic activity names.
        logger.info("Transforming DFG JSON to use generic activity names...")
        json_dfg_generics_file = fn.get_filename_path("dfg.json_generic_act", input_dir)
        json_activity_mapping_file = fn.get_filename_path("dfg.json_activity_mapping_from_dfg", input_dir)

        dfg_transformer.dfg_json_replace_activities_with_generics(
            input_json_path=json_dfg_file,
            output_json_path=json_dfg_generics_file,
            mapping_output_path=json_activity_mapping_file
        )

        # 3. Reduce the DFG until the prompt fits the LLM context window.
        json_dfg_to_simplify = reducer.reduce(json_dfg_generics_file, input_dir)

        # 4. LLM simplification + decode (restore names) and final artifacts.
        return llm_step.run(json_dfg_to_simplify, json_activity_mapping_file, input_dir)
