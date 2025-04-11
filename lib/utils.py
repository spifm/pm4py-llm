from config.constants import *

# Build file name
def build_file_name(exec_path, filename, file_extension):
    return outputs_path + "/" + exec_path + "/" + filename + "." + file_extension