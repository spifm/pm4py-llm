import pandas
import pm4py
import time
import os
from source.helpers.make_dir import MakeOutputDir
import json
from config.constants import *
from source.Config import Config
from source.Filename import Filename
import source.filtering as filtering
from source.Discovery import Discovery
from source.dfg.dfg_transformer import DFGTransformer
from source.Llm import Llm
from source.Preprocessor import Preprocessor
import logging
from typing import Any
from source.helpers.info_writer import InfoWriter


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


    def _filter_log(self, log: Any, output_directory: str):
        """
        Filters the event log based on configuration parameters.
        Returns the filtered log and a string with filtering information.
        """
        filter_level = self.config['filter']['level']
        filter_attr = self.config['filter']['attr']
        export_formats = self.config['filter']['export_formats']

        # Filter log by config parameters
        filtered_log, filtered_info_str = filtering.filter_log(log, filter_attr, filter_level)
        case_values = pm4py.stats.get_trace_attribute_values(filtered_log, self.config['dataset']['columns']['case_id'])

        # Export filtered log if enabled
        if export_formats:
            for export_format in export_formats:
                filename = "filtered_log" + "-numcases_" + str(len(case_values)) + "-" + filtered_info_str
                filename = os.path.join(output_directory, filename + "." + export_format)
                filtering.export_filtered_log(filtered_log, filename, export_format)

        # Show info in log
        if filter_level == "event":
            event_values = pm4py.stats.get_event_attribute_values(filtered_log, filter_attr)
            logger.debug("\nEvent values ({}): {}".format(filter_attr, event_values))
        elif filter_level == "trace":
            trace_values = pm4py.stats.get_trace_attribute_values(filtered_log, 'case:' + filter_attr)
            logger.debug("\nTrace values ({}): {}".format(filter_attr, trace_values))

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
        output_directory = MakeOutputDir.make_unique_dir(self.output_path)

        # Filter log by config parameters if enabled
        try:
            if self.config['filter']['enabled']:
                log, filtered_info_str = self._filter_log(raw_log, output_directory)
            else:
                log, filtered_info_str = raw_log, ''
        except Exception as e:
            raise ValueError(f"Error filtering log: {e}")

        # Log case IDs and number of cases
        case_values = pm4py.stats.get_trace_attribute_values(log, case_id)
        number_of_cases = len(case_values)
        
        logger.info("Case IDs: {}".format(case_values))
        logger.info("Number of cases: {}\n".format(number_of_cases))

        # Preprocess log
        if self.config['preprocess']['enabled']:
            logger.info("Preprocessing log...")
            mapping_activity_json_path = self.config.get("preprocess", {}).get("mapping_activity_json_path", "")
            with open(mapping_activity_json_path, 'r', encoding='utf-8') as f:
                mapping_json = json.load(f)
            preprocessor = Preprocessor(mapping_activity_json=mapping_json, col_to_map=activity_key)
            log = preprocessor.map_activities(log)

        # Create text file with information about the analysis
        info_writer = InfoWriter(output_directory)
        info_writer.write("Analysis Date and Time: {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        info_writer.write("Dataset path: {}\n".format(self.dataset_path))
        info_writer.write("Dataset extension: {}\n".format(file_extension))
        info_writer.write("Number of cases: {}\n".format(str(number_of_cases)))
        info_writer.write("Filter information: {}\n".format(filtered_info_str))
        if self.config['preprocess']['enabled']:
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
            image_filename = self.fn.get_filename_path("dfg.image", output_directory)
            dfg_filename = self.fn.get_filename_path("dfg.raw", output_directory)
            abstract_filename = self.fn.get_filename_path("dfg.abstract", output_directory)
            abstract_dfg = discovery.get_dfg(
                image_filename, dfg_filename, abstract_filename
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
            filename = os.path.join(output_directory, "petri_net-analysis.txt")
            llm_instance.analyze_petri_net(abstract_pn, filename)
        if self.config['discovery']['dfg']['enabled'] and self.config['llm']['dfg']['enabled']:
            logger.debug("LLM analysis for DFG...")
            filename = os.path.join(output_directory, "dfg-analysis.txt")
            llm_instance.analyze_dfg(abstract_dfg, filename)

        if self.config['discovery']['temporal_profile']['enabled'] and self.config['llm']['temporal_profile']['enabled']:
            logger.debug("LLM analysis for Temporal profile...")
            filename = os.path.join(output_directory, "temporal_profile-analysis.txt")
            llm_instance.analyze_temporal_profile(abstract_tp, filename)
        return {
            "message": "PM analysis completed",
            "output_directory": output_directory
        }