import pandas
import pm4py
import time
import os
from config.constants import *
import lib.config_loader as config_loader
import lib.filter as filter
import lib.discovery as discovery
import lib.llm_prompt as llm_prompt
from huggingface_hub import InferenceClient

if __name__ == "__main__":

    # Load configuration parameters
    config = config_loader.load_config()
    dataset_path = config['dataset']['path']
    debug = config['debug']
    filter_level = config['filter']['level']
    filter_attr = config['filter']['attr']
    export_formats = config['filter']['export_formats']
    petri_net_enabled = config['discovery']['petri_net']
    dfg_enabled = config['discovery']['dfg']
    bpmn_enabled = config['discovery']['bpmn']
    temporal_profile_enabled = config['discovery']['temporal_profile']
    llm_config = config['llm']


    # Create output directory
    exec_path = str(int(time.time()))
    try:
        os.makedirs(outputs_path + "/" + exec_path, exist_ok=True)
    except Exception as e:
        print(f"Error creating output directory '{exec_path}': {e}")
        exit(1)

    # Read the dataset
    file_extension = os.path.splitext(dataset_path)[1]

    if file_extension == ".xes":
        log = pm4py.read_xes(dataset_path)
    elif file_extension == ".csv":
        # Convert the CSV event log to XES
        log = pm4py.format_dataframe(pandas.read_csv(dataset_path, sep=config['dataset']['csv_delimiter']),case_id='case_id',activity_key='concept:name',timestamp_key='time:timestamp')
    else:
        print("Unsupported file extension, please provide a .xes or .csv file")
        exit(1)

    # Filter log by config parameters
    filtered_log, min, max,  = filter.filter_log(log, filter_attr, filter_level)

    # Show info if debug is enabled
    if debug > 0:
        if filter_level == "event":
            event_values = pm4py.stats.get_event_attribute_values(filtered_log, filter_attr)
            print("\nEvent values ({}): {}".format(filter_attr, event_values))
        elif filter_level == "trace":
            trace_values = pm4py.stats.get_trace_attribute_values(filtered_log, 'case:' + filter_attr)
            print("\nTrace values ({}): {}".format(filter_attr, trace_values))
        case_values = pm4py.stats.get_trace_attribute_values(filtered_log, 'case_id')
        print("Case IDs: {}".format(case_values))
        number_of_cases = len(case_values)
        print("Number of cases: {}\n".format(number_of_cases))

    # Export filtered log if enabled
    if export_formats:
        for export_format in export_formats:
            file_name = discovery.build_file_name(exec_path, "filtered_log", number_of_cases, filter_attr, min, max, export_format)
            filter.export_filtered_log(filtered_log, file_name, export_format)

    # Discover and save models
    if petri_net_enabled > 0:
        file_name = discovery.build_file_name(exec_path, "petri_net", number_of_cases, filter_attr, min, max, "png")
        pn_file_name = discovery.build_file_name(exec_path, "petri_net", number_of_cases, filter_attr, min, max, "pnml")
        net, im, fm = discovery.get_petri_net(filtered_log, file_name, pn_file_name)

    if dfg_enabled  > 0:
        file_name = discovery.build_file_name(exec_path, "dfg", number_of_cases, filter_attr, min, max, "png")
        discovery.get_dfg(filtered_log, file_name)

    if bpmn_enabled  > 0:
        file_name = discovery.build_file_name(exec_path, "bpmn", number_of_cases, filter_attr, min, max, "png")
        discovery.get_bpmn(filtered_log, file_name)

    if temporal_profile_enabled  > 0:
        file_name = discovery.build_file_name(exec_path, "temporal_profile", number_of_cases, filter_attr, min, max, "csv")
        discovery.get_temporal_profile(filtered_log, file_name)


    # LLM
    client = InferenceClient(
        llm_config['model_name'],
        token=llm_config['hugging_face_api_key'],
    )

    if petri_net_enabled > 0 and llm_config['petri_net']['enabled'] > 0:
        file_name = discovery.build_file_name(exec_path, "petri_net_analysis", number_of_cases, filter_attr, min, max, "txt")
        llm_prompt.analyze_petri_net(client, llm_config, net, im, fm, file_name, debug)

    if dfg_enabled > 0 and llm_config['petri_net']['enabled'] > 0:
        file_name = discovery.build_file_name(exec_path, "dfg_analysis", number_of_cases, filter_attr, min, max, "txt")
        llm_prompt.analyze_dfg(client, llm_config, filtered_log, file_name, debug)
