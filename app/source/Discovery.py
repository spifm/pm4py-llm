import pm4py
import csv
from source.Config import Config

class Discovery:
    def __init__(self, filtered_log):
        self.config = Config().get()
        self.dataset_columns = self.config['dataset']['columns']
        self.case_id_key=self.dataset_columns['case_id']
        self.activity_key=self.dataset_columns['activity']
        self.timestamp_key=self.dataset_columns['timestamp']

        self.filtered_log = filtered_log

    def get_petri_net(self, image_file_name, abstract_file_name, pn_filename):
        """ Discover and save a Petri net model from the filtered log.
        Args:
            image_file_name (str): Path to save the Petri net visualization.
            abstract_file_name (str): Path to save the abstract model description.
            pn_filename (str): Path to save the Petri net in PNML format.
        Returns:
            tuple: A tuple containing the abstract Petri net, the Petri net, initial marking, and final marking.
        """
        noise_threshold = self.config['discovery']['petri_net']['infrequent_ratio']

        net, im, fm = pm4py.discover_petri_net_inductive(
            self.filtered_log,
            noise_threshold / 100,
            case_id_key=self.case_id_key,
            activity_key=self.activity_key,
            timestamp_key=self.timestamp_key
        )
        pm4py.write_pnml(net, im, fm, pn_filename)
        pm4py.save_vis_petri_net(net, im, fm, image_file_name)

        abstract_petri_net = pm4py.llm.abstract_petri_net(net, im, fm)
        self._save_abstract_model(abstract_petri_net, abstract_file_name)
        return abstract_petri_net, net, im, fm

    def get_dfg(self, image_file_names, full_dfg_filename, abstract_file_name):
        """ Discover and save a Directly-Follows Graph (DFG) from the filtered log.
        Args:
            image_file_names (str | list[str]): Paths to save the DFG visualizations.
            full_dfg_filename (str): Path to save the DFG in DFG format.
            abstract_file_name (str): Path to save the abstract model description.
        Returns:
            str: The abstract description of the DFG.
        """
        dfg, start_activities, end_activities = pm4py.discover_dfg(
            self.filtered_log,
            case_id_key=self.case_id_key,
            activity_key=self.activity_key,
            timestamp_key=self.timestamp_key
        )

        if isinstance(image_file_names, str):
            image_file_names = [image_file_names]

        for image_file_name in image_file_names:
            pm4py.save_vis_dfg(dfg, start_activities, end_activities, image_file_name)
        pm4py.write_dfg(dfg, start_activities, end_activities, full_dfg_filename)

        sorted_log = self.filtered_log.sort_values(
            by=[self.case_id_key, self.timestamp_key]
        )
        dfg_description = pm4py.llm.abstract_dfg(
            log_obj=sorted_log,
            case_id_key=self.case_id_key,
            activity_key=self.activity_key,
            timestamp_key=self.timestamp_key,
            include_performance=True,
            secondary_performance_aggregation='stdev',
            max_len=100000
        )
        self._save_abstract_model(dfg_description, abstract_file_name)
        return dfg_description

    def get_performance_dfg(self, image_file_name):
        """ Discover and save a Performance Directly-Follows Graph (DFG) from the filtered log.
        Args:
            image_file_name (str): Path to save the Performance DFG visualization.
        Returns:
            None
        """
        pdfg, start_activities, end_activities = pm4py.discover_performance_dfg(
            self.filtered_log,
            case_id_key=self.case_id_key,
            activity_key=self.activity_key,
            timestamp_key=self.timestamp_key
        )
        pm4py.save_vis_performance_dfg(pdfg, start_activities, end_activities, image_file_name)

    def get_bpmn(self, image_file_name):
        """ Discover and save a BPMN model from the filtered log.
        Args:
            image_file_name (str): Path to save the BPMN visualization.
        Returns:
            None
        """
        noise_threshold = self.config['discovery']['bpmn']['infrequent_ratio']
        bpmn_model = pm4py.discover_bpmn_inductive(self.filtered_log, noise_threshold / 100)
        pm4py.save_vis_bpmn(bpmn_model, image_file_name)

    def get_temporal_profile(self, file_name, abstract_model_file_name):
        """ Discover and save the temporal profile of the filtered log: Discover and create csv file
            Implements the approach described in: Stertz, Florian, Jürgen Mangler, and Stefanie Rinderle-Ma.
            Temporal Conformance Checking at Runtime based on Time-infused Process Models. arXiv preprint arXiv:2008.07262 (2020).
        Args:
            file_name (str): Path to save the temporal profile as a CSV file.
            abstract_model_file_name (str): Path to save the abstract model description.
        Returns:
            tuple: A tuple containing the temporal profile and its abstract model.
        """
        temporal_profile = pm4py.discover_temporal_profile(
            self.filtered_log,
            case_id_key=self.case_id_key,
            activity_key=self.activity_key,
            timestamp_key=self.timestamp_key
        )

        fields = ["Activities", "AVG time", "STD"]
        with open(file_name, 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fields, delimiter=';')
            writer.writeheader()
            writer = csv.writer(csv_file, delimiter=';')

            for key, value in temporal_profile.items():
                value_as_list = [str(round(v, 3)).replace('.', ',') for v in value]
                writer.writerow([key] + value_as_list)

        abstract_model = pm4py.llm.abstract_temporal_profile(temporal_profile, include_header=True)
        self._save_abstract_model(abstract_model, abstract_model_file_name)

        return temporal_profile, abstract_model

    def _save_abstract_model(self, abstract_model, output_file):
        """ Save the abstract model to a file."""
        with open(output_file, 'a') as f:
            f.write(abstract_model)
            f.write("\n\n")
