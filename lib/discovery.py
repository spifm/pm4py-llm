import pm4py
import time
import csv
from config.constants import *

# BPMN: Discover and save model
def get_bpmn(filtered_log):
    noise_threshold = 0.0
    noise_threshold = float(input("Insert the ratio (0-100) to filter infrequent paths: "))
    bpmn_model = pm4py.discover_bpmn_inductive(filtered_log, noise_threshold/100)
    pm4py.save_vis_bpmn(bpmn_model, "{}/bpmn_{}.png".format(outputs_path, int(time.time())))

# Directly-Follows Graph (DFG): Discover and save model
def get_dfg(filtered_log):
    dfg, start_activities, end_activities = pm4py.discover_dfg(filtered_log, case_id_key='case_id', activity_key='concept:name', timestamp_key='time:timestamp')
    pm4py.save_vis_dfg(dfg, start_activities, end_activities, "{}/dfg_{}.png".format(outputs_path, int(time.time())))

# Temporal profile: Discover and create csv file
def get_temporal_profile(filtered_log, debug = 0):
    temporal_profile = pm4py.discover_temporal_profile(filtered_log, activity_key='concept:name', case_id_key='case_id', timestamp_key='time:timestamp')

    if debug > 0:
        print("Temporal profile:\n")

    filePath = "{}/temporal_profile_{}.csv".format(outputs_path, int(time.time()))

    fields = ["Activities", "AVG time (seconds)", "STD (seconds)"]

    with open(filePath, 'w', newline = '') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames = fields)
        writer.writeheader()
        writer = csv.writer(csv_file)

        for key, value in temporal_profile.items():
            value_as_list = list(value)
            value_as_list[0] = value_as_list[0] / 1000
            value_as_list[1] = value_as_list[1] / 1000
            converted_value = tuple(value_as_list)

            if debug > 0:
                print(f"Key: {key}, Time in secs. (avg, std): {converted_value}")
                # Source list --> print("{}: {}\n".format(key, value))

            writer.writerow([key, value_as_list[0], value_as_list[1]])