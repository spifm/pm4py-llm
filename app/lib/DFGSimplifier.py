import pm4py
from lib.Config import Config
import lib.llm as llm
import re
import logging

logger = logging.getLogger(__name__)

class DFGSimplifier:
    def __init__(self):
        self.config = self._load_config()

    def _load_config(self):
        """
        Initializes and returns the configuration instance.
        """
        config_instance = Config()
        config_instance.initialize()
        return config_instance.get()

    def _read_dfg(self, dfg_file):
        """
        Reads the Directly-Follows Graph (DFG) from a file.
        """
        with open(dfg_file, 'r') as file:
            return file.read()

    def _create_prompt(self, dfg):
        """
        Creates a prompt for the LLM based on the DFG and the provided prompt template.
        """
        prompt_template = "\n".join(self.config['llm']['dfg']['simplify_dfg']['prompt'])
        return f"{prompt_template}\n### DFG ###\n{dfg}"

    def simplify(self, dfg_file, output_file):
        """
        Simplifies the Directly-Follows Graph (DFG) using an LLM.
        """
        print("\n\n-------------------\nSimplifying DFG\n-------------------\n\n")

        dfg = self._read_dfg(dfg_file)
        prompt = self._create_prompt(dfg)

        result = llm.exec_prompt(self.config['llm']['dfg'], prompt, output_file)
        return result
    
    def extract_and_save_dfg(self, input_filepath, output_filepath):
        """
        Extracts the simplified DFG from the input file using defined delimiters
        and saves it to a new output file.
        """
        start_marker = "--- DFG BEGIN ---"
        end_marker = "--- DFG END ---"
        in_dfg_block = False
        dfg_lines = []

        with open(input_filepath, "r") as f:
            for line in f:
                if start_marker in line:
                    in_dfg_block = True
                    continue
                elif end_marker in line:
                    break
                elif in_dfg_block:
                    if line.strip():  # Ignore empty lines
                        dfg_lines.append(line.rstrip())

        with open(output_filepath, "w") as f_out:
            f_out.write("\n".join(dfg_lines))

        return "\n".join(dfg_lines)
    

    def _map_activity_labels_to_indices(self, dfg_file_path):
        """
        Read the original DFG file and returns a dictionary mapping
        each activity label to its original index.
        """    
        mapping = {}
        with open(dfg_file_path, 'r') as f:
            num_activities = int(f.readline().strip())
            for idx in range(num_activities):
                label = f.readline().rstrip()
                mapping[label] = idx
        return mapping


    def rewrite_dfg_with_original_indices(self, dfg_file_path, simplified_dfg_path, output_path):
        """
        This function reads the simplified DFG, maps the activity labels to their original indices,
        and rewrites the DFG with the original indices, preserving the structure of start and end activities.
        """

        original_mapping = self._map_activity_labels_to_indices(dfg_file_path)

        logger.debug(f"Original indices: {original_mapping}")

        with open(simplified_dfg_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        # Add a variable to keep track of the number of processed lines in the LLM simplified DFG
        num_of_processed_lines = 0
        
        ### Process the list of activities from the simplified DFG
        # The first line contains the number of activities, followed by the activity labels.
        # But we will not use the first line because the LLM could not have provided the correct number of activities.
        # Rebuild the file using the new indices
        output_lines = []
        num_activities = 0
        output_lines.append(str(num_activities))
        num_of_processed_lines += 1

        logger.debug(f"Processing simplified activity labels")

        for line in lines[1:]:

            logger.debug(f"Line: '{line}'")
            
            if re.compile(r"^\d+x\d+$").match(line.strip()):
                logger.debug("Start activities format 'numberxnumber' found: list of activities finished, breaking the loop")
                break

            num_of_processed_lines += 1

            logger.debug(f"Adding activity")
            num_activities += 1
            output_lines.append(f"{line}")

        # The last added line is the number of start activities, not an activity, so we subtract 1
        num_activities -= 1
        output_lines[0] = str(num_activities)
        logger.debug(f"Number of activities: {num_activities}")
        output_lines.pop(-1) # Remove the last line which is not an activity


        # New mapping: original index -> new index
        simplified_labels = output_lines[1:]  # Skip the first line which is the number of activities
        index_translation = {
            original_mapping.get(label, -1): new_idx
            for new_idx, label in enumerate(simplified_labels)
        }

        logger.debug("Simplified labels: %s", simplified_labels)
        logger.debug("Index translation (original -> new): %s", index_translation)


        ### Process start activities
        num_start_activities_line = num_activities + 2 # +2 because the first line is the number of activities and the second line is the number of start activities
        num_starts = 0
        output_lines.append(str(num_starts))

        logger.debug(f"num_start_activities_line: {num_start_activities_line}, num_of_processed_lines: {num_of_processed_lines}")

        for line in lines[num_of_processed_lines:]:

            line = line.strip()
            logger.debug(f"Line: '{line}'")
            
            if not re.compile(r"^\d+x\d+$").match(line):
                logger.debug("Invalid format 'numberxnumber' for start activities, breaking the loop")
                break

            num_of_processed_lines += 1

            old_idx, freq = line.split("x")
            new_idx = index_translation.get(int(old_idx), -1)
            logger.debug(f"Old activity index: {old_idx}, Frequency: {freq}, New activity index: {new_idx}")

            if new_idx == -1:
                logger.debug(f"Skipping start activity {old_idx} as it is not in the simplified DFG")
                continue

            logger.debug(f"Adding start activity: {new_idx}x{freq}")
            num_starts += 1
            output_lines.append(f"{new_idx}x{freq}")

        # Update the total number of start activities
        output_lines[num_start_activities_line - 1] = str(num_starts)


        ### Process end activities
        total_end_activities_line = num_start_activities_line + num_starts + 1 # +1 because the next line is the number of end activities
        num_ends = 0
        output_lines.append(str(num_ends))
        num_of_processed_lines += 1

        logger.debug(f"total_end_activities_line: {total_end_activities_line}, num ends: {num_ends}, num_of_processed_lines: {num_of_processed_lines}")

        for line in lines[num_of_processed_lines:]:

            line = line.strip()
            logger.debug(f"Line: '{line}'")
            if not re.compile(r"^\d+x\d+$").match(line):
                logger.debug("Invalid format 'numberxnumber' for end activities, breaking the loop")
                break

            num_of_processed_lines += 1

            old_idx, freq = line.split("x")
            new_idx = index_translation.get(int(old_idx), -1)
            logger.debug(f"Old activity index: {old_idx}, Frequency: {freq}, New activity index: {new_idx}")

            if new_idx == -1:
                logger.debug(f"Skipping end activity {old_idx} as it is not in the simplified DFG")
                continue

            logger.debug(f"Adding end activity: {new_idx}x{freq}")
            num_ends += 1
            output_lines.append(f"{new_idx}x{freq}")

        # Update the total number of end activities
        output_lines[total_end_activities_line - 1] = str(num_ends)


        ### Process transitions
        logger.debug(f"Process activity transitions starting from line {num_of_processed_lines} in the LLM simplified DFG file")

        for line in lines[num_of_processed_lines:]:

            line = line.strip()
            logger.debug(f"Line: '{line}'")
            num_of_processed_lines += 1

            if not re.compile(r"^\d+>\d+x\d+$").match(line):
                logger.debug("Invalid format 'source>targetxfrequency' for transitions, skipping line")
                continue

            source, rest = line.split(">")
            target, freq = rest.split("x")
            new_source = index_translation.get(int(source), -1)
            new_target = index_translation.get(int(target), -1)
            logger.debug(f"Source: {source}, Target: {target}, Frequency: {freq}")
            logger.debug(f"New Source: {new_source}, New Target: {new_target}")

            if new_source == -1 or new_target == -1:
                logger.debug(f"Skipping transition from {source} to {target} as one of the activities is not in the simplified DFG")
                continue

            transition = f"{new_source}>{new_target}x{freq}"
            logger.debug(f"Adding transition: {transition}")
            output_lines.append(f"{transition}")

        logger.debug(f"{num_of_processed_lines} lines processed of {len(lines)} lines in the LLM simplified DFG file")

        ### Write the output to the specified file
        with open(output_path, "w") as f_out:
            f_out.write("\n".join(output_lines))
        
        return output_lines


    def convert_dfg_to_image(self, dfg_file, output_path):
        """
        Converts the DFG to a PNG image
        """

        logger.debug(f"Converting DFG from {dfg_file} to image {output_path}")
        
        dfg, start_activities, end_activities = pm4py.read_dfg(dfg_file)

        pm4py.save_vis_dfg(
            dfg,
            start_activities,
            end_activities,
            file_path=output_path,
            bgcolor="white",     # White background
            rankdir="LR"         # Directed graph from left to right
        )