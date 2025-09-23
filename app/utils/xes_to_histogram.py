import pm4py
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import numpy as np
import os
from datetime import datetime


dataset = "dataset/jla_union.xes"
column_name = "grade_er"
label_name = "Grade"
title_name = "Distribution of Grades by Student"
bins = 6 # number of bins in histogram
apply_filter = False # whether to filter out specific traces known to contain shot traces

log = pm4py.read_xes(dataset)
df = pm4py.convert_to_dataframe(log)


# Filter out specific traces (if needed)
if not apply_filter:
    print("No filtering applied.")
else:
    print("Filtering applied.")
    # (these traces have been identified to contain shot traces)
    traces_to_exclude = ['u77175935-1583836757', 'u52418164-1583833381', 'uaaa461495', 'u20072366-1583826485', 'u49567531-1583826151', 'u49567917-1583826142', 'u49615598-1583826100', 'u49618799-1583826046']
    df = df[~df["case:concept:name"].isin(traces_to_exclude)]


####### Print basic statistics
print("Number of events in the log:", len(df))
print("Number of distinct cases (traces):", df["case:concept:name"].nunique())
print("Available columns in dataset:", df.columns)
print("Available values in column", column_name, ":", df[column_name].unique())



####### Plot histogram of a specific column
if column_name in df.columns:

    # Create output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("output", f"histogram-{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    # Group by case and get the relevant column
    # Take the first value per trace (assuming it's consistent within a trace)
    column_per_trace = (
        df.groupby("case:concept:name")[column_name]
        .first()
    )

    removed_traces = column_per_trace[column_per_trace.isna()]

    print("Number of removed traces:", len(removed_traces))
    print("IDs of removed traces:")
    print(removed_traces.index.tolist())

    # Filter all events belonging to those traces
    removed_events = df[df["case:concept:name"].isin(removed_traces.index)]
    print("Number of events in removed traces:", len(removed_events))
    print(removed_events)
    removed_events.to_csv(os.path.join(output_dir, "removed_traces.csv"), index=False)


    # Convert the column to numeric, removing non-numeric entries
    column_per_trace = pd.to_numeric(column_per_trace, errors="coerce").dropna()

    print("Number of students (valid traces after conversion):", len(column_per_trace))
    print("Available values after conversion:", column_per_trace.unique())


    # === Histogram of Absolute Values ===
    plt.figure(figsize=(8,6))
    column_per_trace.hist(bins=bins, edgecolor="black")
    plt.xlabel(label_name)
    plt.ylabel("Number of Students")
    plt.title(title_name + " (Absolute)")
    plt.grid(axis="y", alpha=0.75)
    plt.savefig(os.path.join(output_dir, "histogram_absolute.png"))
    plt.close()


    # === Histogram of Percentages ===
    weights = [1/len(column_per_trace)] * len(column_per_trace)

    plt.figure(figsize=(8,6))
    plt.hist(column_per_trace, bins=bins, edgecolor="black", weights=weights)
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1.0))  # show in %
    plt.xlabel(label_name)
    plt.ylabel("Percentage of Students")
    plt.title(title_name + " (%)")
    plt.grid(axis="y", alpha=0.75)
    plt.savefig(os.path.join(output_dir, "histogram_percent.png"))
    plt.close()


    # === Export Histogram Data ===
    counts, bin_edges = np.histogram(column_per_trace, bins=bins)

    # Construct a DataFrame with the intervals and absolute frequencies
    hist_data = pd.DataFrame({
        "bin_left": bin_edges[:-1],
        "bin_right": bin_edges[1:],
        "frequency": counts,
        "percentage": counts / counts.sum() * 100
    })

    # Store in CSV
    hist_data.to_csv(os.path.join(output_dir, "histogram_data.csv"), index=False)

else:
    print(column_name, ": Column not found in the log. Please check the exact attribute name.")
