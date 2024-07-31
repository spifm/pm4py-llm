import pm4py
import csv
import lib.config_loader as config_loader

config = config_loader.load_config()
dataset_columns = config['dataset']['columns']

# Petri Net: Discover and save model
def get_petri_net(filtered_log, file_name, pn_filename):
    noise_threshold = 0.0
    noise_threshold = float(input("Petri Net: Insert the ratio (0-100) to filter infrequent paths: "))
    net, im, fm = pm4py.discover_petri_net_inductive(filtered_log, noise_threshold/100, case_id_key=dataset_columns['case_id'], activity_key=dataset_columns['activity'], timestamp_key=dataset_columns['timestamp'])
    pm4py.write_pnml(net, im, fm, pn_filename)
    pm4py.save_vis_petri_net(net, im, fm, file_name)
    return net, im, fm

# Directly-Follows Graph (DFG): Discover and save model
def get_dfg(filtered_log, file_name):
    dfg, start_activities, end_activities = pm4py.discover_dfg(filtered_log, case_id_key=dataset_columns['case_id'], activity_key=dataset_columns['activity'], timestamp_key=dataset_columns['timestamp'])
    pm4py.save_vis_dfg(dfg, start_activities, end_activities, file_name)

# BPMN: Discover and save model
def get_bpmn(filtered_log, file_name):
    noise_threshold = 0.0
    noise_threshold = float(input("BPMN: Insert the ratio (0-100) to filter infrequent paths: "))
    bpmn_model = pm4py.discover_bpmn_inductive(filtered_log, noise_threshold/100)
    pm4py.save_vis_bpmn(bpmn_model, file_name)

# Temporal profile: Discover and create csv file
# Implements the approach described in: Stertz, Florian, Jürgen Mangler, and Stefanie Rinderle-Ma.
# “Temporal Conformance Checking at Runtime based on Time-infused Process Models.” arXiv preprint arXiv:2008.07262 (2020).
def get_temporal_profile(filtered_log, file_name, debug = 0):
    temporal_profile = pm4py.discover_temporal_profile(filtered_log, activity_key=dataset_columns['activity'], case_id_key=dataset_columns['case_id'], timestamp_key=dataset_columns['timestamp'])

    if debug > 0:
        print("Temporal profile:\n")

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

            if debug > 0:
                print(f"Key: {key}, Time (avg, std): {converted_value}")
                # Source list --> print("{}: {}\n".format(key, value))

            writer.writerow([key, value_as_list[0], value_as_list[1]])

    return temporal_profile
