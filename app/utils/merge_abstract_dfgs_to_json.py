import os
import json

print("This script reads abstract DFG models from a directory structure,")
print("extracts user IDs and grades from folder names, and combines them")
print("into a single JSON file for later processing.\n")

# Ask user for the base directory
base_dir = input("Enter the path to the base directory (e.g., /output/my-dfg-folder): ").strip()

if not os.path.isdir(base_dir):
    print(f"Error: Directory not found: {base_dir}")
    exit(1)

dfg_data = []

for folder_name in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, folder_name)
    if os.path.isdir(folder_path):
        # Extract user_id and grade from folder name (e.g., userid-1968-grade-31.25)
        try:
            parts = folder_name.split('-')
            user_id_index = parts.index("userid") + 1
            grade_index = parts.index("grade") + 1
            user_id = parts[user_id_index]
            grade = float(parts[grade_index])
        except (ValueError, IndexError):
            print(f"Skipping folder with unexpected name format: {folder_name}")
            continue

        # Find a file starting with "abstract-dfg" and ending with ".txt"
        dfg_file = None
        for f in os.listdir(folder_path):
            if f.startswith("abstract-dfg") and f.endswith(".txt"):
                dfg_file = os.path.join(folder_path, f)
                break

        if dfg_file and os.path.exists(dfg_file):
            with open(dfg_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Remove the first line if it matches the header
            header = "If I have a process with flow:"
            if content.lstrip().startswith(header):
                content = content.lstrip()[len(header):].strip()

            dfg_data.append({
                "user_id": user_id,
                "grade": grade,
                "dfg": content
            })
        else:
            print(f"No valid DFG file found in folder: {folder_name}")

# Prepare output path
folder_name = os.path.basename(os.path.normpath(base_dir))
output_dir = "/output"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, f"output_dfg_{folder_name}.json")

# Write to JSON
with open(output_file, "w", encoding="utf-8") as json_file:
    json.dump(dfg_data, json_file, indent=4, ensure_ascii=False)

print(f"\nProcessed {len(dfg_data)} DFG models. Saved to '{output_file}'.")
