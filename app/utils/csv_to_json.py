import csv
import json
import os

def convert_value(value):
    # Convert the value to int or float if possible, otherwise keep it as a string.
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        return value

def csv_to_custom_json(csv_path, filename):
    # Convert a CSV file to a custom JSON format.
    filename = os.path.basename(os.path.splitext(filename)[0] + ".csv")
    columns = {}

    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            for key, value in row.items():
                value = convert_value(value)
                columns.setdefault(key, []).append(value)

    return {
        "filename": os.path.basename(filename),
        "data": columns
    }

if __name__ == "__main__":
    # Path to the CSV file
    csv_file = "/data/dataset/bd-all-events-grades-p25-22students-30711.csv"

    # Path to save the JSON file
    json_file = "/data/dataset/bd-p25.json"

    # Convert CSV to JSON and save it
    result = csv_to_custom_json(csv_file, json_file)
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"JSON stored in: {json_file}")
