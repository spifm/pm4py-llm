from config.constants import *
from pm4py.algo.filtering.log.attributes import attributes_filter

# Filter log by game result
def filter_log_by_game_outcome(log):
    filter_param = "game_outcome"
    min_msg_input = "Insert the MINIMUM grade obtained in the game to apply the filter: "
    max_msg_input = "Insert the MAXIMUM grade obtained in the game to apply the filter: "
    min, max, filtered_log = filter_log(log, filter_param, min_msg_input, max_msg_input)
    return filter_param, min, max, filtered_log

# Filter log by final exercise result
def filter_log_by_exam_result(log):
    filter_param = "grade_final"
    min_msg_input = "Insert the MINIMUM grade obtained in the exam to apply the filter: "
    max_msg_input = "Insert the MAXIMUM grade obtained in the exam to apply the filter: "
    min, max, filtered_log = filter_log(log, filter_param, min_msg_input, max_msg_input)
    return filter_param, min, max, filtered_log

# Filter log
def filter_log(log, filter_param, min_msg_input, max_msg_input):
    min = float(input(min_msg_input))
    max = float(input(max_msg_input))
    return min, max, attributes_filter.apply_numeric_events(log, min, max, parameters={constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY: filter_param})
