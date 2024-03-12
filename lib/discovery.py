import pm4py
import time
import csv
from config.constants import *

# BPMN: Discover and save model
def get_bpmn(filtered_log, file_name):
    noise_threshold = 0.0
    noise_threshold = float(input("Insert the ratio (0-100) to filter infrequent paths: "))
    bpmn_model = pm4py.discover_bpmn_inductive(filtered_log, noise_threshold/100)
    pm4py.save_vis_bpmn(bpmn_model, file_name)

# Directly-Follows Graph (DFG): Discover and save model
def get_dfg(filtered_log, file_name):
    dfg, start_activities, end_activities = pm4py.discover_dfg(filtered_log, case_id_key='case_id', activity_key='concept:name', timestamp_key='time:timestamp')
    pm4py.save_vis_dfg(dfg, start_activities, end_activities, file_name)

# Temporal profile: Discover and create csv file
def get_temporal_profile(filtered_log, file_name, debug = 0):
    temporal_profile = pm4py.discover_temporal_profile(filtered_log, activity_key='concept:name', case_id_key='case_id', timestamp_key='time:timestamp')

    if debug > 0:
        print("Temporal profile:\n")

    fields = ["Activities", "AVG time (seconds)", "STD (seconds)"]

    with open(file_name, 'w', newline = '') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames = fields, delimiter = ';')
        writer.writeheader()
        writer = csv.writer(csv_file, delimiter = ';')

        for key, value in temporal_profile.items():
            value_as_list = list(value)

            for i in range(0, len(value_as_list)):
                value_as_list[i] = round((value_as_list[i] / 1000), 3)
                value_as_list[i] = str(value_as_list[i]).replace('.', ',')

            converted_value = tuple(value_as_list)

            if debug > 0:
                print(f"Key: {key}, Time in secs. (avg, std): {converted_value}")
                # Source list --> print("{}: {}\n".format(key, value))

            writer.writerow([key, value_as_list[0], value_as_list[1]])

# Build file name
def build_file_name(model_type, number_of_cases, filter_param, min, max, file_extension):
    file_name_base = model_type + "-numcases_" + str(number_of_cases) + "-" + filter_param + "-" + str(min) + "-" + str(max)
    return outputs_path + "/" + file_name_base + "." + file_extension

# Build file name with timestamp
def build_file_name_with_timestamp(model_type, number_of_cases, file_extension):
    return "{}/{}-numcases_{}_{}.{}".format(outputs_path, model_type, number_of_cases, int(time.time()), file_extension)