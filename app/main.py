import pandas
import pm4py
import time
import os
import argparse
from config.constants import *
from lib.Config import Config
import lib.filtering as filtering
import lib.discovery as discovery
import lib.llm as llm

# Build file name
def build_file_name(exec_path, filename, file_extension):
    return OUTPUT_PATH + "/" + exec_path + "/" + filename + "." + file_extension

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-path")
    parser.add_argument("--dataset-csv_delimiter")
    parser.add_argument("--output_path")
    parser.add_argument("--debug")
    return parser.parse_args()

if __name__ == "__main__":

    # Load configuration parameters
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
    petri_net_enabled = config['discovery']['petri_net']
    dfg_enabled = config['discovery']['dfg']
    bpmn_enabled = config['discovery']['bpmn']
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
        exec_path = config['output_path']
    else:
        exec_path = str(int(time.time()))

    try:
        os.makedirs(OUTPUT_PATH + "/" + exec_path, exist_ok=True)
    except Exception as e:
        print(f"Error creating output directory '{OUTPUT_PATH + "/" + exec_path}': {e}")
        exit(1)


    # Filter log by config parameters
    if filter_enabled:
        filtered_log, filtered_info_str = filtering.filter_log(log, filter_attr, filter_level)
    else:
        filtered_log, filtered_info_str = log, ''

    case_values = pm4py.stats.get_trace_attribute_values(filtered_log, case_id)
    number_of_cases = len(case_values)

    # Create text file with information about the analysis
    with open(OUTPUT_PATH + "/" + exec_path + '/info.txt', 'a') as f:
        f.write("Dataset path: {}\n".format(dataset_path))
        f.write("Dataset extension: {}\n".format(file_extension))
        f.write("Number of cases: {}\n".format(str(number_of_cases)))
        f.write("Filter information: {}\n".format(filtered_info_str))

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

    # Export filtered log if enabled
    if export_formats:
        for export_format in export_formats:
            filename = "filtered_log" + "-numcases_" + str(number_of_cases) + "-" + filtered_info_str
            filename = build_file_name(exec_path, filename, export_format)
            filtering.export_filtered_log(filtered_log, filename, export_format)

    # Discover and save models
    if petri_net_enabled:
        print("Discovering Petri net...")
        image_filename = build_file_name(exec_path, "petri_net", "png")
        abstract_filename = build_file_name(exec_path, "abstract-petri_net", "txt")
        pn_filename = build_file_name(exec_path, "petri_net", "pnml")

        abstract_pn, net, im, fm = discovery.get_petri_net(
            filtered_log, image_filename, abstract_filename, pn_filename
        )

    if dfg_enabled:
        print("Discovering DFG...")
        image_filename = build_file_name(exec_path, "dfg", "png")
        dfg_filename = build_file_name(exec_path, "dfg", "dfg")
        abstract_filename = build_file_name(exec_path, "abstract-dfg", "txt")
        abstract_dfg = discovery.get_dfg(
            filtered_log, image_filename, dfg_filename, abstract_filename
        )
        performance_image_filename = build_file_name(exec_path, "performance-dfg", "png")
        discovery.get_performance_dfg(filtered_log, performance_image_filename)

    if bpmn_enabled:
        print("Discovering BPMN...")
        image_filename = build_file_name(exec_path, "bpmn", "png")
        discovery.get_bpmn(filtered_log, image_filename)

    if temporal_profile_enabled:
        print("Discovering temporal profile...")
        filename = build_file_name(exec_path, "temporal_profile", "csv")
        abstract_filename = build_file_name(exec_path, "abstract-temporal_profile", "txt")
        
        temporal_profile, abstract_tp = discovery.get_temporal_profile(
            filtered_log, filename, abstract_filename
        )

    # LLM
    if petri_net_enabled and llm_config['petri_net']['enabled']:
        filename = build_file_name(exec_path, "petri_net-analysis", "txt")
        llm.analyze_petri_net(abstract_pn, filename)

    if dfg_enabled and llm_config['dfg']['enabled']:
        filename = build_file_name(exec_path, "dfg-analysis", "txt")
        llm.analyze_dfg(abstract_dfg, filename)

    if temporal_profile_enabled and llm_config['temporal_profile']['enabled']:
        filename = build_file_name(exec_path, "temporal_profile-analysis", "txt")
        llm.analyze_temporal_profile(abstract_tp, filename)