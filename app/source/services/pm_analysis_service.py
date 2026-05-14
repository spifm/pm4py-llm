import pandas
import pm4py
import time
import os
from source.helpers.make_dir import MakeOutputDir
import json
from config.constants import *
from source.Config import Config
from source.helpers.filename_getter import Filename
from source.Discovery import Discovery
from source.core.dfg.dfg_transformer import DFGTransformer
from source.Llm import Llm
from source.helpers.preprocessor import Preprocessor
import logging
from typing import Any
from source.helpers.info_writer import InfoWriter
from pathlib import Path
from source.core.dataset_filter.event_filter import EventFilter


logger = logging.getLogger(__name__)

class PmAnalysisService:

    def __init__(self, dataset_path: str, dataset_csv_delimiter: str, output_path: str = ""):
        try:
            self.dataset_path = dataset_path
            self.dataset_csv_delimiter = dataset_csv_delimiter
            self.output_path = output_path
            
            self.fn = Filename()

            config_instance = Config()

            config_instance.initialize(
                dataset_path=dataset_path,
                dataset_csv_delimiter=dataset_csv_delimiter,
                output_path=output_path
            )
            self.config = config_instance.get()

            self.event_filter = EventFilter(
                case_id_key=self.config['dataset']['columns']['case_id'],
                activity_key=self.config['dataset']['columns']['activity'],
                timestamp_key=self.config['dataset']['columns']['timestamp']
            )

        except Exception as e:
            raise ValueError(f"Error initializing PmAnalysisService: {e}")


    def _read_log(self):
        """
        Reads the event log from the dataset path.
        Returns the event log object and file extension.
        """
        case_id=self.config['dataset']['columns']['case_id']
        activity_key=self.config['dataset']['columns']['activity']
        timestamp_key=self.config['dataset']['columns']['timestamp']

        # Read the dataset
        file_extension = os.path.splitext(self.dataset_path)[1]

        if file_extension == ".xes":
            log = pm4py.read_xes(self.dataset_path)
        elif file_extension == ".csv":
            # Convert csv to dataframe
            log_df = pandas.read_csv(self.dataset_path, sep=self.dataset_csv_delimiter)
            # Convert timestamp column to datetime type
            log_df[timestamp_key] = pandas.to_datetime(log_df[timestamp_key], errors='coerce')
            # Convert the CSV event log to XES
            log = pm4py.format_dataframe(log_df,case_id, activity_key,timestamp_key)
            # Convert case_id column to string type
            log[case_id] = log[case_id].astype(str)
        else:
            raise ValueError("Unsupported file extension, please provide a .xes or .csv file")

        logger.debug("Columns of the log:\n%s", log.columns.tolist())
        logger.debug("First row of the log:\n%s", log.iloc[0])

        return log, file_extension
    

    def _write_metadata_info(self, info_writer: InfoWriter) -> None:
        """
        Writes dataset metadata from the sidecar JSON file associated with the analyzed dataset.

        Expected metadata path:
        /path/to/dataset.csv -> /path/to/dataset.meta.json

        If the metadata file does not exist, logs a warning and continues.
        """
        dataset_path = Path(self.dataset_path)
        metadata_path = dataset_path.with_suffix(".meta.json")

        if not metadata_path.exists():
            logger.warning("Metadata file not found for dataset: %s. Continuing analysis.", metadata_path)
            return

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as e:
            logger.warning("Could not read metadata file %s: %s", metadata_path, e)
            return

        info_writer.write("=== Dataset Metadata ===\n\n")

        def write_item(prefix: str, value: Any) -> None:
            if isinstance(value, dict):
                for k, v in value.items():
                    new_prefix = f"{prefix}.{k}" if prefix else str(k)
                    write_item(new_prefix, v)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    new_prefix = f"{prefix}[{i}]"
                    write_item(new_prefix, item)
            else:
                info_writer.write(f"{prefix}: {value}\n")

        for key, value in metadata.items():
            write_item(str(key), value)

        info_writer.write("\n\n")


    def _filter_log(self, log: Any, output_directory: str):
        """
        Filters the event log based on configured event names.
        Returns the filtered log and a string with filtering information.
        """
        events_to_filter = self.config['filter'].get('events', [])
        export_formats = self.config['filter'].get('export_formats', [])

        filtered_log = self.event_filter.filter_events(log, events_to_filter)

        exported_files = self.event_filter.export_filtered_log(filtered_log, output_directory, export_formats)

        filtered_info_str = f"event_filter_removed={events_to_filter}" if events_to_filter else "event_filter_removed=[]"

        logger.info("Configured events filtered out: %s", events_to_filter)
        if exported_files:
            logger.info("Exported filtered log to: %s", exported_files)


        return filtered_log, filtered_info_str
    

    def run_pm_analysis(self):
        """
        Full PM analysis execution.
        Returns a dictionary with relevant information for the API.
        """
        logger.debug(f"Starting PM analysis for dataset: {self.dataset_path}")

        case_id=self.config['dataset']['columns']['case_id']
        activity_key=self.config['dataset']['columns']['activity']

        # Read log
        try:
            raw_log, file_extension = self._read_log()
        except Exception as e:
            logger.exception("Error reading log", exc_info=e)
            raise

        # Create output directory
        output_directory, final_output_name = MakeOutputDir.make_unique_dir(self.output_path)

        # Log case IDs and number of cases
        case_values = pm4py.stats.get_trace_attribute_values(raw_log, case_id)
        number_of_cases = len(case_values)
        
        logger.info("Case IDs: {}".format(case_values))
        logger.info("Number of cases: {}\n".format(number_of_cases))

        # Create text file with information about the dataset and the analysis
        info_writer = InfoWriter(output_directory)
        self._write_metadata_info(info_writer)
        info_writer.write("=== Dataset Info ===\n\n")
        info_writer.write("Analysis Date and Time: {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        info_writer.write("Dataset path: {}\n".format(self.dataset_path))
        info_writer.write("Dataset extension: {}\n".format(file_extension))
        info_writer.write("Number of cases: {}\n".format(str(number_of_cases)))
        info_writer.write("Number of events: {}\n".format(str(len(raw_log))))

        # Filter log by config parameters if enabled
        try:
            if self.config['filter']['enabled']:
                log, filtered_info_str = self._filter_log(raw_log, output_directory)

                # Log case IDs and number of cases
                case_values = pm4py.stats.get_trace_attribute_values(log, case_id)
                number_of_cases = len(case_values)

                logger.info("Case IDs after filtering: {}".format(case_values))
                cases_message = "Number of cases after filtering: {}".format(number_of_cases)
                events_message = "Number of events after filtering: {}".format(str(len(log)))
                logger.info(cases_message)
                logger.info(events_message)
                info_writer.write(cases_message + "\n")
                info_writer.write(events_message + "\n")
                info_writer.write("Filter information: {}\n".format(filtered_info_str))
            else:
                
                log, filtered_info_str = raw_log, ''
        except Exception as e:
            raise ValueError(f"Error filtering log: {e}")

        # Preprocess log
        if self.config['preprocess']['enabled']:
            logger.info("Preprocessing log...")
            mapping_activity_json_path = self.config.get("preprocess", {}).get("mapping_activity_json_path", "")
            with open(mapping_activity_json_path, 'r', encoding='utf-8') as f:
                mapping_json = json.load(f)
            preprocessor = Preprocessor(mapping_activity_json=mapping_json, col_to_map=activity_key)
            log = preprocessor.map_activities(log)

            info_writer.write("Preprocessing. Using activity mapping from: {}\n".format(mapping_activity_json_path))


        # Discover and save models
        discovery = Discovery(log)

        if self.config['discovery']['petri_net']['enabled']:
            logger.info("Discovering Petri net...")

            image_filename = self.fn.get_filename_path(output_directory, "petri_net.image")
            abstract_filename = self.fn.get_filename_path(output_directory, "petri_net.abstract")
            pn_filename = self.fn.get_filename_path(output_directory, "petri_net.raw")

            abstract_pn, net, im, fm = discovery.get_petri_net(
                image_filename, abstract_filename, pn_filename
            )

        if self.config['discovery']['dfg']['enabled']:
            logger.info("Discovering DFG...")
            image_formats = self.config['discovery']['dfg']['image_formats']
            image_filenames = self.fn.get_filename_paths_for_formats("dfg.image", output_directory, image_formats)
            dfg_filename = self.fn.get_filename_path("dfg.raw", output_directory)
            abstract_filename = self.fn.get_filename_path("dfg.abstract", output_directory)
            abstract_dfg = discovery.get_dfg(
                list(image_filenames.values()), dfg_filename, abstract_filename
            )

            # Store DFG as json
            transformer = DFGTransformer()
            transformer.dfg_pm4py_to_json(
                dfg_filename,
                self.fn.get_filename_path("dfg.json", output_directory)
            )

            if self.config['discovery']['dfg']['performance-enabled']:
                performance_image_filename = self.fn.get_filename_path("dfg.performance_image", output_directory)
                discovery.get_performance_dfg(performance_image_filename)

        if self.config['discovery']['bpmn']['enabled']:
            logger.info("Discovering BPMN...")
            image_filename = self.fn.get_filename_path("bpmn.image", output_directory)
            discovery.get_bpmn(image_filename)

        if self.config['discovery']['temporal_profile']['enabled']:
            logger.info("Discovering temporal profile...")
            filename = os.path.join(output_directory, "temporal_profile.csv")
            abstract_filename = os.path.join(output_directory, "abstract-temporal_profile.txt")
            
            temporal_profile, abstract_tp = discovery.get_temporal_profile(
                filename, abstract_filename
            )

        # LLM
        logger.info("Starting LLM analysis...")
        llm_instance = Llm()
        
        if self.config['discovery']['petri_net']['enabled'] and self.config['llm']['petri_net']['enabled']:
            logger.debug("LLM analysis for Petri net...")
            filename = self.fn.get_filename_path("petri_net.analysis", output_directory)
            llm_instance.analyze_petri_net(abstract_pn, filename)
        if self.config['discovery']['dfg']['enabled'] and self.config['llm']['dfg']['enabled']:
            logger.debug("LLM analysis for DFG...")
            filename = self.fn.get_filename_path("dfg.analysis", output_directory)
            llm_instance.analyze_dfg(abstract_dfg, filename)
        else:
            logger.warning("DFG discovery or LLM analysis for DFG is disabled. Skipping LLM analysis for DFG.")

        if self.config['discovery']['temporal_profile']['enabled'] and self.config['llm']['temporal_profile']['enabled']:
            logger.debug("LLM analysis for Temporal profile...")
            filename = self.fn.get_filename_path("temporal_profile.analysis", output_directory)
            llm_instance.analyze_temporal_profile(abstract_tp, filename)
        
        return {
            "message": "PM analysis completed",
            "output_directory": output_directory,
            "output_directory_name": final_output_name
        }
