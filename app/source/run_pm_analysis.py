import pandas
import pm4py
import time
import os
import json
from config.constants import *
from source.Config import Config
from source.Filename import Filename
import source.filtering as filtering
from source.Discovery import Discovery
from source.DFGTransformer import DFGTransformer
from source.Llm import Llm
from source.Preprocessor import Preprocessor
import logging


logger = logging.getLogger(__name__)

def run_pm_analysis(
    dataset_path: str,
    dataset_csv_delimiter: str,
    output_path: str = ""
):
    """
    Full PM analysis execution.
    Returns a dictionary with relevant information for the API.
    """

    # Load configuration parameters
    fn = Filename()
    configInstance = Config()

    configInstance.initialize(
        dataset_path=dataset_path,
        dataset_csv_delimiter=dataset_csv_delimiter,
        output_path=output_path
    )
    config = configInstance.get()

    logger.debug(f"Starting PM analysis with config: {config}")

    dataset_columns = config['dataset']['columns']
    case_id=dataset_columns['case_id']
    activity_key=dataset_columns['activity']
    timestamp_key=dataset_columns['timestamp']
    filter_enabled = config['filter']['enabled']
    filter_level = config['filter']['level']
    filter_attr = config['filter']['attr']
    export_formats = config['filter']['export_formats']
    petri_net_enabled = config['discovery']['petri_net']['enabled']
    dfg_enabled = config['discovery']['dfg']['enabled']
    performance_dfg_enabled = config['discovery']['dfg']['performance-enabled']
    bpmn_enabled = config['discovery']['bpmn']['enabled']
    temporal_profile_enabled = config['discovery']['temporal_profile']
    llm_config = config['llm']


    # Read the dataset
    file_extension = os.path.splitext(dataset_path)[1]

    if file_extension == ".xes":
        log = pm4py.read_xes(dataset_path)
    elif file_extension == ".csv":
        # Convert csv to dataframe
        log_df = pandas.read_csv(dataset_path, sep=config['dataset']['csv_delimiter'])
        # Convert timestamp column to datetime type
        log_df[timestamp_key] = pandas.to_datetime(log_df[timestamp_key], errors='coerce')
        # Convert the CSV event log to XES
        log = pm4py.format_dataframe(log_df,case_id, activity_key,timestamp_key)
        # Convert case_id column to string type
        log[case_id] = log[case_id].astype(str)
    else:
        logger.error("Unsupported file extension, please provide a .xes or .csv file")
        exit(1)


    logger.debug("Columns of the log:\n%s", log.columns.tolist())
    logger.debug("First row of the log:\n%s", log.iloc[0])


    # Create output directory
    if output_path != "":
        output_directory = OUTPUT_PATH + "/" + output_path
    else:
        output_directory = OUTPUT_PATH + "/" + str(int(time.time()))

    try:
        os.makedirs(output_directory, exist_ok=True)
    except Exception as e:
        logger.error(f"Error creating output directory '{output_directory}': {e}")
        exit(1)


    # Filter log by config parameters
    if filter_enabled:
        filtered_log, filtered_info_str = filtering.filter_log(log, filter_attr, filter_level)
    else:
        filtered_log, filtered_info_str = log, ''

    case_values = pm4py.stats.get_trace_attribute_values(filtered_log, case_id)
    number_of_cases = len(case_values)

    # Export filtered log if enabled
    if export_formats:
        for export_format in export_formats:
            filename = "filtered_log" + "-numcases_" + str(number_of_cases) + "-" + filtered_info_str
            filename = os.path.join(output_directory, filename + "." + export_format)
            filtering.export_filtered_log(filtered_log, filename, export_format)

    # Show info in log
    if filter_enabled and filter_level == "event":
        event_values = pm4py.stats.get_event_attribute_values(filtered_log, filter_attr)
        logger.debug("\nEvent values ({}): {}".format(filter_attr, event_values))
    elif filter_enabled and filter_level == "trace":
        trace_values = pm4py.stats.get_trace_attribute_values(filtered_log, 'case:' + filter_attr)
        logger.debug("\nTrace values ({}): {}".format(filter_attr, trace_values))
    
    logger.info("Case IDs: {}".format(case_values))
    logger.info("Number of cases: {}\n".format(number_of_cases))

    # Preprocess log
    if config['preprocess']['enabled']:
        logger.info("Preprocessing log...")
        mapping_activity_json_path = config.get("preprocess", {}).get("mapping_activity_json_path", "")
        with open(mapping_activity_json_path, 'r', encoding='utf-8') as f:
            mapping_json = json.load(f)
        preprocessor = Preprocessor(mapping_activity_json=mapping_json, col_to_map=activity_key)
        filtered_log = preprocessor.map_activities(filtered_log)

    # Create text file with information about the analysis
    with open(output_directory + '/info.txt', 'a') as f:
        f.write("Dataset path: {}\n".format(dataset_path))
        f.write("Dataset extension: {}\n".format(file_extension))
        f.write("Number of cases: {}\n".format(str(number_of_cases)))
        f.write("Filter information: {}\n".format(filtered_info_str))
        if config['preprocess']['enabled']:
            f.write("Preprocessing. Using activity mapping from: {}\n".format(mapping_activity_json_path))

    # Discover and save models
    discovery = Discovery(filtered_log)

    if petri_net_enabled:
        logger.info("Discovering Petri net...")

        image_filename = fn.get_filename_path(output_directory, "petri_net.image")
        abstract_filename = fn.get_filename_path(output_directory, "petri_net.abstract")
        pn_filename = fn.get_filename_path(output_directory, "petri_net.raw")

        abstract_pn, net, im, fm = discovery.get_petri_net(
            image_filename, abstract_filename, pn_filename
        )

    if dfg_enabled:
        logger.info("Discovering DFG...")
        image_filename = fn.get_filename_path("dfg.image", output_directory)
        dfg_filename = fn.get_filename_path("dfg.raw", output_directory)
        abstract_filename = fn.get_filename_path("dfg.abstract", output_directory)
        abstract_dfg = discovery.get_dfg(
            image_filename, dfg_filename, abstract_filename
        )

        # Store DFG as json
        transformer = DFGTransformer()
        transformer.dfg_pm4py_to_json(
            dfg_filename,
            fn.get_filename_path("dfg.json", output_directory)
        )

        if performance_dfg_enabled:
            performance_image_filename = fn.get_filename_path("dfg.performance_image", output_directory)
            discovery.get_performance_dfg(performance_image_filename)

    if bpmn_enabled:
        logger.info("Discovering BPMN...")
        image_filename = fn.get_filename_path("bpmn.image", output_directory)
        discovery.get_bpmn(image_filename)

    if temporal_profile_enabled:
        logger.info("Discovering temporal profile...")
        filename = os.path.join(output_directory, "temporal_profile.csv")
        abstract_filename = os.path.join(output_directory, "abstract-temporal_profile.txt")
        
        temporal_profile, abstract_tp = discovery.get_temporal_profile(
            filename, abstract_filename
        )

    # LLM
    logger.info("Starting LLM analysis...")
    llm_instance = Llm()
    
    if petri_net_enabled and llm_config['petri_net']['enabled']:
        logger.debug("LLM analysis for Petri net...")
        filename = os.path.join(output_directory, "petri_net-analysis.txt")
        llm_instance.analyze_petri_net(abstract_pn, filename)
    if dfg_enabled and llm_config['dfg']['enabled']:
        logger.debug("LLM analysis for DFG...")
        filename = os.path.join(output_directory, "dfg-analysis.txt")
        llm_instance.analyze_dfg(abstract_dfg, filename)

    if temporal_profile_enabled and llm_config['temporal_profile']['enabled']:
        logger.debug("LLM analysis for Temporal profile...")
        filename = os.path.join(output_directory, "temporal_profile-analysis.txt")
        llm_instance.analyze_temporal_profile(abstract_tp, filename)
    return {
        "message": "PM analysis completed",
        "output_directory": output_directory
    }