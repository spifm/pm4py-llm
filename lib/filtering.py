from config.constants import *
import pm4py
from pm4py.algo.filtering.log.attributes import attributes_filter

# Filter log
def filter_log(log, filter_attr, filter_level):
    filter_param = 'case:' + filter_attr if filter_level == 'trace' else filter_attr
    min_msg_input = "Insert the MINIMUM value for the attribute (" + filter_level + " -> " + filter_param + "): "
    max_msg_input = "Insert the MAXIMUM value for the attribute (" + filter_level + " -> " + filter_param + "): "
    min = float(input(min_msg_input))
    max = float(input(max_msg_input))
    return attributes_filter.apply_numeric_events(log, min, max, parameters={constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY: filter_param}), min, max

# Export filtered log
def export_filtered_log(filtered_log, file_name, export_format):
    if export_format == "csv":
        export_filtered_log_as_csv(filtered_log, file_name)
    elif export_format == "xes":
        export_filtered_log_as_xes(filtered_log, file_name)

# Export filtered log as CSV
def export_filtered_log_as_csv(filtered_log, file_name):
    df = pm4py.convert_to_dataframe(filtered_log)
    df.to_csv(file_name, sep=';')

# Export filtered log as XES
def export_filtered_log_as_xes(filtered_log, file_name):
    pm4py.write_xes(filtered_log, file_name)