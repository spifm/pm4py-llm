import pandas
import pm4py
from config.constants import *
import lib.config_loader as config_loader
import lib.filter as filter
import lib.discovery as discovery

if __name__ == "__main__":

    # Load configuration parameters
    config = config_loader.load_config()
    debug = config['debug']
    filter_game_result = config['filter']['game_result']
    filter_exam_result = config['filter']['exam_result']
    bpmn = config['discovery']['bpmn']
    dfg = config['discovery']['dfg']
    temporal_profile = config['discovery']['temporal_profile']

    # Convert the CSV event log to XES
    log = pm4py.format_dataframe(pandas.read_csv('dataset/anon.csv', sep=','), case_id='case_id',activity_key='concept:name', timestamp_key='time:timestamp')

    # Filter by game result
    if filter_game_result > 0:
        filter_param, filtered_log = filter.filter_log_by_game_outcome(log)
   
    # Filter by exam result
    if filter_exam_result > 0:
        filter_param, filtered_log = filter.filter_log_by_exam_result(log)

    # Show attributes if debug
    if debug > 0:
        event_values = pm4py.stats.get_event_attribute_values(filtered_log, filter_param)
        print("Event values ({}): {}\n".format(filter_param, event_values))
        case_values = pm4py.stats.get_trace_attribute_values(filtered_log, 'case_id')
        print("Case IDs: {}\n".format(case_values))

    # Discover and save models
    if bpmn > 0:
        discovery.get_bpmn(filtered_log)
    
    if dfg > 0:
        discovery.get_dfg(filtered_log)

    if temporal_profile > 0:
        discovery.get_temporal_profile(filtered_log)

            