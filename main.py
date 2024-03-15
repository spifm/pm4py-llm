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
    filter_level = config['filter']['level']
    filter_attr = config['filter']['attr']
    export_formats = config['filter']['export_formats']
    bpmn = config['discovery']['bpmn']
    dfg = config['discovery']['dfg']
    temporal_profile = config['discovery']['temporal_profile']

    # Convert the CSV event log to XES
    log = pm4py.format_dataframe(pandas.read_csv('dataset/anon.csv', sep=','), case_id='case_id',activity_key='concept:name', timestamp_key='time:timestamp')

    # Filter log by config parameters
    filtered_log, min, max,  = filter.filter_log(log, filter_attr, filter_level)

    # Show info if debug is enabled
    if debug > 0:
        if filter_level == "event":
            event_values = pm4py.stats.get_event_attribute_values(filtered_log, filter_attr)
            print("\nEvent values ({}): {}".format(filter_attr, event_values))
        elif filter_level == "trace":
            trace_values = pm4py.stats.get_trace_attribute_values(filtered_log, 'case:' + filter_attr)
            print("\nTrace values ({}): {}".format(filter_attr, trace_values))
        case_values = pm4py.stats.get_trace_attribute_values(filtered_log, 'case_id')
        print("Case IDs: {}".format(case_values))
        number_of_cases = len(case_values)
        print("Number of cases: {}\n".format(number_of_cases))

    # Export filtered log if enabled
    if export_formats:
        for export_format in export_formats:
            file_name = discovery.build_file_name("filtered_log", number_of_cases, filter_attr, min, max, export_format)
            filter.export_filtered_log(filtered_log, file_name, export_format)

    # Discover and save models
    if bpmn > 0:
        file_name = discovery.build_file_name("bpmn", number_of_cases, filter_attr, min, max, "png")
        discovery.get_bpmn(filtered_log, file_name)
    
    if dfg > 0:
        file_name = discovery.build_file_name("dfg", number_of_cases, filter_attr, min, max, "png")
        discovery.get_dfg(filtered_log, file_name)

    if temporal_profile > 0:
        file_name = discovery.build_file_name("temporal_profile", number_of_cases, filter_attr, min, max, "csv")
        discovery.get_temporal_profile(filtered_log, file_name)

            