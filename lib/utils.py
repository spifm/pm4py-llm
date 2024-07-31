from config.constants import *

# Build file name
def build_file_name(exec_path, model_type, number_of_cases, filter_param, min, max, file_extension):
    file_name_base = model_type + "-numcases_" + str(number_of_cases) + "-" + filter_param + "-" + str(min) + "-" + str(max)
    return outputs_path + "/" + exec_path + "/" + file_name_base + "." + file_extension