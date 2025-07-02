import pm4py

input_path = "output/TEEM-2025/p100-TEEM-2025/p100-dfg-chatgpt.dfg"
output_path = "output/TEEM-2025/p100-TEEM-2025/p100-dfg-chatgpt_dfg.png"

dfg, start_activities, end_activities = pm4py.read_dfg(input_path)

pm4py.save_vis_dfg(
    dfg,
    start_activities,
    end_activities,
    file_path=output_path,
    bgcolor="white",     # White background
    rankdir="LR"         # Directed graph from left to right
)

print(f"DFG saved as image in: {output_path}")