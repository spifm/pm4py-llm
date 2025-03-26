import os

file_path = "/usr/local/lib/python3.12/site-packages/pm4py/util/constants.py"

# Leer el contenido del archivo asegurándonos de no mezclar indentaciones
with open(file_path, "r") as f:
    lines = f.readlines()

# Reescribir el contenido asegurándonos de que la indentación es correcta
with open(file_path, "w") as f:
    for line in lines:
        if "parent_name = str(psutil.Process(parent_pid).name())" in line:
            f.write("    try:\n")
            f.write("        parent_name = str(psutil.Process(parent_pid).name())\n")
            f.write("    except psutil.NoSuchProcess:\n")
            f.write("        parent_name = \"unknown\"\n")
        else:
            # Convertimos cualquier tabulación en espacios para mantener consistencia
            clean_line = line.replace("\t", "    ")
            f.write(clean_line)

print("Patch applied successfully to constants.py")
