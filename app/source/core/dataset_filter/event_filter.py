import os
import csv
import pandas as pd
import pm4py

class EventFilter:

    def __init__(self, case_id_key, activity_key, timestamp_key):
            self.case_id_key = case_id_key
            self.activity_key = activity_key
            self.timestamp_key = timestamp_key

    def filter_events(self, log, events_to_filter):
        log_df = log.copy() if isinstance(log, pd.DataFrame) else pm4py.convert_to_dataframe(log)

        events = {
            str(event).strip()
            for event in (events_to_filter or [])
            if event is not None and str(event).strip()
        }

        if events:
            log_df = log_df[~log_df[self.activity_key].isin(events)].copy()

        return log_df


    def export_filtered_log(self, filtered_log, output_directory, export_formats):
        normalized_formats = []

        for export_format in export_formats or []:
            normalized_format = str(export_format).strip().lower()
            if normalized_format in {"csv", "xes"} and normalized_format not in normalized_formats:
                normalized_formats.append(normalized_format)

        exported_files = []

        for export_format in normalized_formats:
            output_path = os.path.join(output_directory, f"event-filtered-log.{export_format}")
            if export_format == "csv":
                filtered_log.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)
            else:
                pm4py.write_xes(filtered_log, output_path)
            exported_files.append(output_path)

        return exported_files
