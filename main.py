import pandas
import pm4py
import time
from pm4py.util import constants
from pm4py.algo.filtering.log.attributes import attributes_filter

debug = 1
filter_game_result = 0
filter_exam_result = 1
bpmn = 0
dfg = 0
temporal_profile = 1

saved_models_path = "saved_models"
constants.SHOW_EVENT_LOG_DEPRECATION = False

####### FILTER FUNCTIONS #######

# Filter log by game result
def filter_log_by_game_outcome(log):
    filter_param = "game_outcome"
    min_msg_input = "Introduzca la nota MÍNIMA obtenida en el juego para aplicar el filtro: "
    max_msg_input = "Introduzca la nota MÁXIMA obtenida en el juego para aplicar el filtro: "
    return filter_param, filter_log(log, filter_param, min_msg_input, max_msg_input)

# Filter log by final exercise result
def filter_log_by_exam_result(log):
    filter_param = "grade_final"
    min_msg_input = "Introduzca la nota MÍNIMA obtenida en el examen: "
    max_msg_input = "Introduzca la nota MÁXIMA obtenida en el examen: "
    return filter_param, filter_log(log, filter_param, min_msg_input, max_msg_input)

# Filter log
def filter_log(log, filter_param, min_msg_input, max_msg_input):
    min = float(input(min_msg_input))
    max = float(input(max_msg_input))
    return attributes_filter.apply_numeric_events(log, min, max, parameters={constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY: filter_param})


####### DISCOVERY FUNCTIONS #######

# BPMN: Discover and save model
def get_bpmn(filtered_log):
    noise_threshold = 0.0
    noise_threshold = float(input("Introduzca el porcentaje de caminos poco frecuentes a filtrar: "))
    bpmn_model = pm4py.discover_bpmn_inductive(filtered_log, noise_threshold/100)
    pm4py.save_vis_bpmn(bpmn_model, "{}/bpmn_{}.png".format(saved_models_path, int(time.time())))

# Directly-Follows Graph (DFG): Discover and save model
def get_dfg(filtered_log):
    dfg, start_activities, end_activities = pm4py.discover_dfg(filtered_log, case_id_key='case_id', activity_key='concept:name', timestamp_key='time:timestamp')
    pm4py.save_vis_dfg(dfg, start_activities, end_activities, "{}/dfg_{}.png".format(saved_models_path, int(time.time())))


####### MAIN #######

if __name__ == "__main__":

    # Convert the CSV event log to XES
    log = pm4py.format_dataframe(pandas.read_csv('dataset/anon.csv', sep=','), case_id='case_id',activity_key='concept:name', timestamp_key='time:timestamp')

    # Filter by game result
    if filter_game_result > 0:
        filter_param, filtered_log = filter_log_by_game_outcome(log)
   
    # Filter by exam result
    if filter_exam_result > 0:
        filter_param, filtered_log = filter_log_by_exam_result(log)

    # Show attributes if debug
    if debug > 0:
        event_values = pm4py.stats.get_event_attribute_values(filtered_log, filter_param)
        print("Event values ({}): {}\n".format(filter_param, event_values))
        case_values = pm4py.stats.get_trace_attribute_values(filtered_log, 'case_id')
        print("Case IDs: {}\n".format(case_values))

    # Discover and save models
    if bpmn > 0:
        get_bpmn(filtered_log)
    
    if dfg > 0:
        get_dfg(filtered_log)

    if temporal_profile > 0:
        temporal_profile = pm4py.discover_temporal_profile(filtered_log, activity_key='concept:name', case_id_key='case_id', timestamp_key='time:timestamp')
        print("Temporal profile:\n")
        for key, value in temporal_profile.items():
            value_as_list = list(value)
            value_as_list[0] = value_as_list[0] / 1000
            value_as_list[1] = value_as_list[1] / 1000
            converted_value = tuple(value_as_list)
            print(f"Clave: {key}, Tiempo en segundos (avg, std): {converted_value}")
            # Lista original --> print("{}: {}\n".format(key, value))

            