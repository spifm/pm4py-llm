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
