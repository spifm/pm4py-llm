import pm4py
import csv
import pandas as pd
from lib.Config import Config


def get_config():
    return Config().get()

# Petri Net: Discover and save model
def get_petri_net(filtered_log, image_file_name, abstract_file_name, pn_filename):

    config = get_config()
    dataset_columns = config['dataset']['columns']

    noise_threshold = 0.0
    noise_threshold = float(input("Petri Net: Insert the ratio (0-100) to filter infrequent paths: "))
    net, im, fm = pm4py.discover_petri_net_inductive(filtered_log, noise_threshold/100, case_id_key=dataset_columns['case_id'], activity_key=dataset_columns['activity'], timestamp_key=dataset_columns['timestamp'])
    pm4py.write_pnml(net, im, fm, pn_filename)
    pm4py.save_vis_petri_net(net, im, fm, image_file_name)

    abstract_petri_net = pm4py.llm.abstract_petri_net(net, im, fm)
    save_abstract_model(abstract_petri_net, abstract_file_name)
    return abstract_petri_net, net, im, fm

# Directly-Follows Graph (DFG): Discover and save model
def get_dfg(filtered_log, image_file_name, full_dfg_filename, abstract_file_name):

    config = get_config()
    dataset_columns = config['dataset']['columns']

    dfg, start_activities, end_activities = pm4py.discover_dfg(
        filtered_log,
        case_id_key=dataset_columns['case_id'],
        activity_key=dataset_columns['activity'],
        timestamp_key=dataset_columns['timestamp']
    )

    pm4py.save_vis_dfg(dfg, start_activities, end_activities, image_file_name)

    pm4py.write_dfg(dfg, start_activities, end_activities, full_dfg_filename)

    filtered_log = filtered_log.sort_values(
        by=[dataset_columns['case_id'],
            dataset_columns['timestamp']
        ]
    )
    dfg_description = pm4py.llm.abstract_dfg(
        log_obj=filtered_log,
        case_id_key=dataset_columns['case_id'],
        activity_key=dataset_columns['activity'],
        timestamp_key=dataset_columns['timestamp'],
        include_performance = True,
        secondary_performance_aggregation = 'stdev',
        max_len = 100000
    )
    save_abstract_model(dfg_description, abstract_file_name)
    return dfg_description

# Performance Directly-Follows Graph (DFG): Discover and save model
def get_performance_dfg(filtered_log, image_file_name):

    config = get_config()
    dataset_columns = config['dataset']['columns']

    pdfg, start_activities, end_activities = pm4py.discover_performance_dfg(filtered_log, case_id_key=dataset_columns['case_id'], activity_key=dataset_columns['activity'], timestamp_key=dataset_columns['timestamp'])
    pm4py.save_vis_performance_dfg(pdfg, start_activities, end_activities, image_file_name)

# BPMN: Discover and save model
def get_bpmn(filtered_log, image_file_name):
    noise_threshold = 0.0
    noise_threshold = float(input("BPMN: Insert the ratio (0-100) to filter infrequent paths: "))
    bpmn_model = pm4py.discover_bpmn_inductive(filtered_log, noise_threshold/100)
    pm4py.save_vis_bpmn(bpmn_model, image_file_name)

# Temporal profile: Discover and create csv file
# Implements the approach described in: Stertz, Florian, Jürgen Mangler, and Stefanie Rinderle-Ma.
# “Temporal Conformance Checking at Runtime based on Time-infused Process Models.” arXiv preprint arXiv:2008.07262 (2020).
def get_temporal_profile(filtered_log, file_name, abstract_model_file_name):

    config = get_config()
    dataset_columns = config['dataset']['columns']

    temporal_profile = pm4py.discover_temporal_profile(filtered_log, activity_key=dataset_columns['activity'], case_id_key=dataset_columns['case_id'], timestamp_key=dataset_columns['timestamp'])

    fields = ["Activities", "AVG time", "STD"]

    with open(file_name, 'w', newline = '') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames = fields, delimiter = ';')
        writer.writeheader()
        writer = csv.writer(csv_file, delimiter = ';')

        for key, value in temporal_profile.items():
            value_as_list = list(value)

            for i in range(0, len(value_as_list)):
                value_as_list[i] = round((value_as_list[i]), 3)
                value_as_list[i] = str(value_as_list[i]).replace('.', ',')

            converted_value = tuple(value_as_list)

            #if debug > 0:
                # Print model --> print(f"Key: {key}, Time (avg, std): {converted_value}")
                # Source list --> print("{}: {}\n".format(key, value))

            writer.writerow([key, value_as_list[0], value_as_list[1]])

    abstract_model = pm4py.llm.abstract_temporal_profile(temporal_profile, include_header=True)
    save_abstract_model(abstract_model, abstract_model_file_name)

    return temporal_profile, abstract_model


# Save abstract model
def save_abstract_model(abstract_model, output_file):
    with open(output_file, 'a') as f:
        f.write(abstract_model)
        f.write("\n\n")