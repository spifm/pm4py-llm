import pm4py
from pandas import DataFrame
import logging

logger = logging.getLogger(__name__)

class Preprocessor:
    def __init__(self, mapping_activity_json, col_to_map):
        self.col_to_map = col_to_map
        self.mapping_activity_json = mapping_activity_json
    
    def map_activities(self, log: DataFrame) -> DataFrame:
        """
        Maps activities in the event log based on the loaded mapping JSON.
        """
        log[self.col_to_map] = (
            log[self.col_to_map]
            .astype(str)
            .map(self.mapping_activity_json)
            .fillna(log[self.col_to_map]))

        return log