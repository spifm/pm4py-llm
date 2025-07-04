from lib.Config import Config
import lib.llm as llm

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
        return f"{prompt_template}\n\n{dfg}"

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