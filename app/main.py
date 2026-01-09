import pandas
import pm4py
import time
import os
import json
import argparse
from config.constants import *
from lib.Config import Config
from lib.Filename import Filename
import lib.filtering as filtering
import lib.Discovery as Discovery
import lib.DFGTransformer as DFGTransformer
import lib.llm as llm
from lib.Preprocessor import Preprocessor


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-path")
    parser.add_argument("--dataset-csv_delimiter")
    parser.add_argument("--output_path")
    parser.add_argument("--debug")
    return parser.parse_args()

if __name__ == "__main__":

    # Load configuration parameters
    fn = Filename()
    configInstance = Config()
    configInstance.initialize(parse_args())
    config = configInstance.get()

    dataset_path = config['dataset']['path']
    dataset_columns = config['dataset']['columns']
    case_id=dataset_columns['case_id']
    activity_key=dataset_columns['activity']
    timestamp_key=dataset_columns['timestamp']
    debug = config['debug']
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
        print("Unsupported file extension, please provide a .xes or .csv file")
        exit(1)

    if debug:
        print("Columns of the log:\n", log.columns.tolist())
        print("First row of the log:\n", log.iloc[0])


    # Create output directory
    if config['output_path'] != "":
        outputDirectory = OUTPUT_PATH + "/" + config['output_path']
    else:
        outputDirectory = OUTPUT_PATH + "/" + str(int(time.time()))

    try:
        os.makedirs(outputDirectory, exist_ok=True)
    except Exception as e:
        print(f"Error creating output directory '{outputDirectory}': {e}")
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
            filename = os.path.join(outputDirectory, filename + "." + export_format)
            filtering.export_filtered_log(filtered_log, filename, export_format)

    # Show info if debug is enabled
    if debug:
        if filter_enabled and filter_level == "event":
            event_values = pm4py.stats.get_event_attribute_values(filtered_log, filter_attr)
            print("\nEvent values ({}): {}".format(filter_attr, event_values))
        elif filter_enabled and filter_level == "trace":
            trace_values = pm4py.stats.get_trace_attribute_values(filtered_log, 'case:' + filter_attr)
            print("\nTrace values ({}): {}".format(filter_attr, trace_values))
        print("Case IDs: {}".format(case_values))
        print("Number of cases: {}\n".format(number_of_cases))

    # Preprocess log
    if config['preprocess']['enabled']:
        print("Preprocessing log...")
        mapping_activity_json_path = config.get("preprocess", {}).get("mapping_activity_json_path", "")
        with open(mapping_activity_json_path, 'r', encoding='utf-8') as f:
            mapping_json = json.load(f)
        preprocessor = Preprocessor(mapping_activity_json=mapping_json, col_to_map=activity_key)
        filtered_log = preprocessor.map_activities(filtered_log)

    # Create text file with information about the analysis
    with open(outputDirectory + '/info.txt', 'a') as f:
        f.write("Dataset path: {}\n".format(dataset_path))
        f.write("Dataset extension: {}\n".format(file_extension))
        f.write("Number of cases: {}\n".format(str(number_of_cases)))
        f.write("Filter information: {}\n".format(filtered_info_str))
        if config['preprocess']['enabled']:
            f.write("Preprocessing. Using activity mapping from: {}\n".format(mapping_activity_json_path))

    # Discover and save models
    discovery = Discovery.Discovery(filtered_log)

    if petri_net_enabled:
        print("Discovering Petri net...")

        image_filename = fn.get_filename_path(outputDirectory, "petri_net.image")
        abstract_filename = fn.get_filename_path(outputDirectory, "petri_net.abstract")
        pn_filename = fn.get_filename_path(outputDirectory, "petri_net.raw")

        abstract_pn, net, im, fm = discovery.get_petri_net(
            image_filename, abstract_filename, pn_filename
        )

    if dfg_enabled:
        print("Discovering DFG...")
        image_filename = fn.get_filename_path("dfg.image", outputDirectory)
        dfg_filename = fn.get_filename_path("dfg.raw", outputDirectory)
        abstract_filename = fn.get_filename_path("dfg.abstract", outputDirectory)
        abstract_dfg = discovery.get_dfg(
            image_filename, dfg_filename, abstract_filename
        )

        # Store DFG as json
        transformer = DFGTransformer.DFGTransformer()
        transformer.dfg_pm4py_to_json(
            dfg_filename,
            fn.get_filename_path("dfg.json", outputDirectory)
        )

        if performance_dfg_enabled:
            performance_image_filename = fn.get_filename_path("dfg.performance_image", outputDirectory)
            discovery.get_performance_dfg(performance_image_filename)

    if bpmn_enabled:
        print("Discovering BPMN...")
        image_filename = fn.get_filename_path("bpmn.image", outputDirectory)
        discovery.get_bpmn(image_filename)

    if temporal_profile_enabled:
        print("Discovering temporal profile...")
        filename = os.path.join(outputDirectory, "temporal_profile.csv")
        abstract_filename = os.path.join(outputDirectory, "abstract-temporal_profile.txt")
        
        temporal_profile, abstract_tp = discovery.get_temporal_profile(
            filename, abstract_filename
        )

    # LLM
    if petri_net_enabled and llm_config['petri_net']['enabled']:
        filename = os.path.join(outputDirectory, "petri_net-analysis.txt")
        llm.analyze_petri_net(abstract_pn, filename)

    if dfg_enabled and llm_config['dfg']['enabled']:
        filename = os.path.join(outputDirectory, "dfg-analysis.txt")
        llm.analyze_dfg(abstract_dfg, filename)

    if temporal_profile_enabled and llm_config['temporal_profile']['enabled']:
        filename = os.path.join(outputDirectory, "temporal_profile-analysis.txt")
        llm.analyze_temporal_profile(abstract_tp, filename)