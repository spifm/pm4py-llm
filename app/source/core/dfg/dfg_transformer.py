from source.Config import Config
import logging
import json

logger = logging.getLogger(__name__)

class DFGTransformer:
    def __init__(self):
        self.config = self._load_config()


    def _load_config(self):
        """
        Initializes and returns the configuration instance.
        """
        config_instance = Config()
        config_instance.initialize()
        return config_instance.get()


    def dfg_pm4py_to_json(self, dfg_path: str, json_output_path: str) -> None:
        """
        Converts a PM4Py DFG file into a JSON representation using activity *names*.

        Output JSON structure:
        {
        "start_activities": [
            { "activity": "<name>", "freq": <int> },
            ...
        ],
        "end_activities": [
            { "activity": "<name>", "freq": <int> },
            ...
        ],
        "transitions": [
            { "src": "<name>", "tgt": "<name>", "freq": <int> },
            ...
        ]
        }
        """
        with open(dfg_path, 'r', encoding='utf-8') as f:
            # 1) Activities
            num_activities = int(f.readline().strip())
            activities = []
            for _ in range(num_activities):
                label = f.readline().rstrip("\n")
                activities.append(label)

            # 2) Start activities
            start_activities = []
            num_start = int(f.readline().strip())
            for _ in range(num_start):
                line = f.readline().strip()   # e.g. "28x21"
                if not line:
                    continue
                idx_str, freq_str = line.split("x")
                idx = int(idx_str)
                freq = int(freq_str)
                start_activities.append({
                    "activity": activities[idx],
                    "freq": freq
                })

            # 3) End activities
            end_activities = []
            num_end = int(f.readline().strip())
            for _ in range(num_end):
                line = f.readline().strip()   # e.g. "28x9"
                if not line:
                    continue
                idx_str, freq_str = line.split("x")
                idx = int(idx_str)
                freq = int(freq_str)
                end_activities.append({
                    "activity": activities[idx],
                    "freq": freq
                })

            # 4) Transitions
            transitions = []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # format: "28>41x2154"
                src_dest, freq_str = line.split("x")
                src_str, dst_str = src_dest.split(">")
                src_idx = int(src_str)
                dst_idx = int(dst_str)
                freq = int(freq_str)
                transitions.append({
                    "src": activities[src_idx],
                    "tgt": activities[dst_idx],
                    "freq": freq
                })

        dfg_json = {
            "start_activities": start_activities,
            "end_activities": end_activities,
            "transitions": transitions
        }

        with open(json_output_path, 'w', encoding='utf-8') as out:
            json.dump(dfg_json, out, ensure_ascii=False, indent=2)

        logger.info(f"PM4Py DFG converted to JSON and saved at {json_output_path}")

    

    def dfg_json_replace_activities_with_generics(self, 
                                            input_json_path: str,
                                            output_json_path: str,
                                            mapping_output_path: str,
                                            prefix: str = "ACT_") -> None:
        """
        Reads a DFG JSON (with activity names) and produces:
        - a new JSON where activities are replaced by generic IDs (ACT_0, ACT_1, ...)
        - a mapping JSON file: { "ACT_0": "<original_name>", ... }

        Input JSON (simplified):
        {
        "start_activities": [ { "activity": "<name>", "freq": int }, ... ],
        "end_activities":   [ { "activity": "<name>", "freq": int }, ... ],
        "transitions":      [ { "src": "<name>", "tgt": "<name>", "freq": int }, ... ]
        }

        Output JSON:
        same structure, but "activity", "src" and "tgt" use ACT_x IDs instead of names.
        """
        with open(input_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 1) Recolectar todos los nombres de actividad
        activity_names = set()

        for entry in data.get("start_activities", []):
            activity_names.add(entry["activity"])

        for entry in data.get("end_activities", []):
            activity_names.add(entry["activity"])

        for t in data.get("transitions", []):
            activity_names.add(t["src"])
            activity_names.add(t["tgt"])

        # 2) Crear mapping determinista nombre -> ACT_x (ordenado por nombre)
        sorted_names = sorted(activity_names)
        name_to_id = {}
        id_to_name = {}

        for idx, name in enumerate(sorted_names):
            act_id = f"{prefix}{idx}"
            name_to_id[name] = act_id
            id_to_name[act_id] = name

        # 3) Construir nuevo JSON con IDs
        new_start = []
        for entry in data.get("start_activities", []):
            new_start.append({
                "activity": name_to_id[entry["activity"]],
                "freq": entry["freq"]
            })

        new_end = []
        for entry in data.get("end_activities", []):
            new_end.append({
                "activity": name_to_id[entry["activity"]],
                "freq": entry["freq"]
            })

        new_transitions = []
        for t in data.get("transitions", []):
            new_transitions.append({
                "src": name_to_id[t["src"]],
                "tgt": name_to_id[t["tgt"]],
                "freq": t["freq"]
            })

        new_data = {
            "start_activities": new_start,
            "end_activities": new_end,
            "transitions": new_transitions
        }

        # 4) Guardar JSON con IDs
        with open(output_json_path, 'w', encoding='utf-8') as out:
            json.dump(new_data, out, ensure_ascii=False, indent=2)

        # 5) Guardar mapping ACT_x -> nombre original
        with open(mapping_output_path, 'w', encoding='utf-8') as map_out:
            json.dump(id_to_name, map_out, ensure_ascii=False, indent=2)



    def dfg_json_restore_activity_names(self,
                                        act_json_path: str,
                                        mapping_path: str,
                                        output_json_path: str,
                                        add_activity_numbers: bool = False) -> None:
        """
        Restores original activity names in a JSON DFG that uses IDs (ACT_0, ACT_1, ...),
        using a JSON mapping file of the form:
        { "ACT_0": "<original_name>", "ACT_1": "<original_name>", ... }

        Input JSON (act_json_path):
        {
            "start_activities": [ { "activity": "ACT_0", "freq": int }, ... ],
            "end_activities":   [ { "activity": "ACT_3", "freq": int }, ... ],
            "transitions":      [ { "src": "ACT_0", "tgt": "ACT_1", "freq": int }, ... ]
        }

        Output JSON (output_json_path):
        Same structure, but with original names instead of ACT_x.
        If add_activity_numbers is True, activity names are prefixed with a
        human-friendly number in first-appearance order, e.g. "[1] Activity".
        """

        # 1) Load JSON DFG with ACT_x
        with open(act_json_path, 'r', encoding='utf-8') as f:
            dfg_data = json.load(f)

        # 2) Load mapping ACT_x -> original name
        with open(mapping_path, 'r', encoding='utf-8') as f_map:
            id_to_name = json.load(f_map)

        # Helper to map an ID or leave it as is if not in the mapping
        def map_id(act_id: str) -> str:
            return id_to_name.get(act_id, act_id)

        activity_numbers = {}

        def add_number(activity_name: str) -> str:
            if not add_activity_numbers:
                return activity_name

            if activity_name not in activity_numbers:
                activity_numbers[activity_name] = len(activity_numbers) + 1

            return f"[{activity_numbers[activity_name]}] {activity_name}"
        
        # 3) Restore names in start_activities
        restored_start = []
        for entry in dfg_data.get("start_activities", []):
            activity = map_id(entry["activity"])
            restored_start.append({
                "activity": add_number(activity),
                "freq": int(entry["freq"])
            })


        # 4) Restore names in end_activities
        restored_end = []
        for entry in dfg_data.get("end_activities", []):
            activity = map_id(entry["activity"])
            restored_end.append({
                "activity": add_number(activity),
                "freq": int(entry["freq"])
            })


        # 5) Restore names in transitions
        try:
            restored_transitions = []
            for t in dfg_data.get("transitions", []):
                if t["src"] not in id_to_name:
                    logger.error(f"Source ID {t['src']} not found in mapping")
                if t["tgt"] not in id_to_name:
                    logger.error(f"Target ID {t['tgt']} not found in mapping")
                src = map_id(t["src"])
                tgt = map_id(t["tgt"])
                restored_transitions.append({
                    "src":  add_number(src),
                    "tgt":  add_number(tgt),
                    "freq": int(t["freq"])
                })
        except Exception as e:
            logger.error(f"Error while checking transition IDs against mapping: {e}")
            raise
        

        restored_data = {
            "start_activities": restored_start,
            "end_activities": restored_end,
            "transitions": restored_transitions
        }


        # 6) Save restored JSON
        with open(output_json_path, 'w', encoding='utf-8') as out:
            json.dump(restored_data, out, ensure_ascii=False, indent=2)


    def dfg_named_json_to_pm4py(self,
                                named_json_path: str,
                                dfg_output_path: str) -> None:
        """
        Converts a DFG in JSON format (with activity names) to the
        PM4Py DFG format.

        Input (named_json_path):
        {
            "start_activities": [
            { "activity": "<name>", "freq": int }, ...
            ],
            "end_activities": [
            { "activity": "<name>", "freq": int }, ...
            ],
            "transitions": [
            { "src": "<name>", "tgt": "<name>", "freq": int }, ...
            ]
        }

        Output (dfg_output_path): text file in pm4py format:
        <num_activities>
        <activity_0>
        <activity_1>
        ...
        <num_start_activities>
        <idx>x<freq>
        ...
        <num_end_activities>
        <idx>x<freq>
        ...
        <src_idx>><tgt_idx>x<freq>
        ...
        """

        # 1) Load JSON
        with open(named_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        start_activities = data.get("start_activities", [])
        end_activities = data.get("end_activities", [])
        transitions = data.get("transitions", [])

        # 2) Collect all distinct activities
        activity_names = set()

        for entry in start_activities:
            activity_names.add(entry["activity"])

        for entry in end_activities:
            activity_names.add(entry["activity"])

        for t in transitions:
            activity_names.add(t["src"])
            activity_names.add(t["tgt"])

        # 3) Create sorted list and name -> index mapping
        #    (sorting alphabetically gives reproducibility)
        activities_list = sorted(activity_names)
        activity_to_idx = {name: idx for idx, name in enumerate(activities_list)}

        # 4) Write the file in pm4py format
        with open(dfg_output_path, 'w', encoding='utf-8') as out:
            # Number of activities
            out.write(f"{len(activities_list)}\n")
            # List of activities
            for name in activities_list:
                out.write(f"{name}\n")

            # Start activities
            out.write(f"{len(start_activities)}\n")
            for entry in start_activities:
                name = entry["activity"]
                freq = int(entry["freq"])
                idx = activity_to_idx[name]
                out.write(f"{idx}x{freq}\n")

            # End activities
            out.write(f"{len(end_activities)}\n")
            for entry in end_activities:
                name = entry["activity"]
                freq = int(entry["freq"])
                idx = activity_to_idx[name]
                out.write(f"{idx}x{freq}\n")

            # Transitions
            for t in transitions:
                src_name = t["src"]
                tgt_name = t["tgt"]
                freq = int(t["freq"])
                src_idx = activity_to_idx[src_name]
                tgt_idx = activity_to_idx[tgt_name]
                out.write(f"{src_idx}>{tgt_idx}x{freq}\n")
