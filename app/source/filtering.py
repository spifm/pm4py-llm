from config.constants import *
import pm4py
import pandas as pd
from pm4py.algo.filtering.log.attributes import attributes_filter
from config.constants import *
from source.Config import Config


def get_config():
    return Config().get()

# Filter log
def filter_log(log, filter_attr, filter_level):

    # Check if the filter level is valid
    if filter_level == 'trace' and not filter_attr.startswith("case:"):
        filter_attr = 'case:' + filter_attr

    # Check if the attribute is a string or numeric
    is_numeric = pd.api.types.is_numeric_dtype(log[filter_attr])

    if is_numeric:
        filtered_dataframe, filtered_info_str = filter_by_numeric_attribute(log, filter_attr, filter_level)
    else:
        filtered_dataframe, filtered_info_str = filter_by_string_attribute(log, filter_attr, filter_level)

    return filtered_dataframe.copy(), filtered_info_str

# Filter log by string attribute
def filter_by_string_attribute(log, filter_attr, filter_level):

    config = get_config()

    print(f"Available values for '{filter_attr}':")
    print(log[filter_attr].unique())

    input_value = input("Insert the string value for the attribute (" + filter_level + " -> " + filter_attr + "): ")
    
    print(f"Filtering log by '{filter_attr}' with value '{input_value}'")

    if filter_level == 'case':
        filtered_dataframe = pm4py.filter_trace_attribute_values(
            log,
            filter_attr,
            [input_value],
            case_id_key=config['dataset']['columns']['case_id']
        )
    elif filter_level == 'event':
        filtered_dataframe = pm4py.filter_event_attribute_values(
            log,
            filter_attr,
            [input_value],
            'case',
            case_id_key=config['dataset']['columns']['case_id']
        )
    else:
        raise ValueError("Invalid filter level. Use 'case' or 'event'.")

    # Replace problematic characters in the filtered info string
    return filtered_dataframe, filter_attr.replace(":", "_")

# Filter log by numeric attribute
def filter_by_numeric_attribute(log, filter_attr, filter_level):
    min_msg_input = "Insert the MINIMUM value for the attribute (" + filter_level + " -> " + filter_attr + "): "
    max_msg_input = "Insert the MAXIMUM value for the attribute (" + filter_level + " -> " + filter_attr + "): "
    min = float(input(min_msg_input))
    max = float(input(max_msg_input))

    filtered_log = attributes_filter.apply_numeric_events(
        log, min, max,
        parameters={constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY: filter_attr}
    )

    # Replace problematic characters in the filtered info string    
    return filtered_log, filter_attr.replace(":", "_") + "-" + str(min) + "-" + str(max)

# Export filtered log
def export_filtered_log(filtered_log, file_name, export_format):
    if export_format == "csv":
        export_filtered_log_as_csv(filtered_log, file_name)
    elif export_format == "xes":
        export_filtered_log_as_xes(filtered_log, file_name)

# Export filtered log as CSV
def export_filtered_log_as_csv(filtered_log, file_name):
    df = pm4py.convert_to_dataframe(filtered_log)
    df.to_csv(file_name, sep=',')

# Export filtered log as XES
def export_filtered_log_as_xes(filtered_log, file_name):
    pm4py.write_xes(filtered_log, file_name)