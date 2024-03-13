from config.constants import *
from pm4py.algo.filtering.log.attributes import attributes_filter

# Filter log
def filter_log(log, filter_attr, filter_level):
    filter_param = 'case:' + filter_attr if filter_level == 'trace' else filter_attr
    min_msg_input = "Insert the MINIMUM value for the attribute (" + filter_level + " -> " + filter_param + "): "
    max_msg_input = "Insert the MAXIMUM value for the attribute (" + filter_level + " -> " + filter_param + "): "
    min = float(input(min_msg_input))
    max = float(input(max_msg_input))
    return attributes_filter.apply_numeric_events(log, min, max, parameters={constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY: filter_param}), min, max
