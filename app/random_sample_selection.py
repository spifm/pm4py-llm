import pandas as pd
from config.constants import *
from lib.Config import Config
import os
import time

configInstance = Config()
configInstance.initialize()
config = configInstance.get()
debug = config['debug']
dataset_path = config['dataset']['path']
case_id = config['dataset']['columns']['case_id']

file_extension = os.path.splitext(dataset_path)[1]

if file_extension != ".csv":
    print("Unsupported file extension, please provide a .csv file")
    exit(1)

# Read the dataset
dataset = pd.read_csv(dataset_path, sep=config['dataset']['csv_delimiter'])

# Input for sample size
sample_size = int(input("Insert the size of the random sample (number of caseid groups): "))

if not (isinstance(sample_size, (int)) and sample_size > 0):
    print("Sample size is not valid")
    exit(1)

# Get unique caseids
unique_caseids = dataset[case_id].unique()

# Select random sample of caseid groups
sampled_caseids = pd.Series(unique_caseids).sample(n=sample_size, random_state=42).values

if debug > 0:
    print(f"Sampled caseids: {sampled_caseids}")

# Filter the dataset to include only the sampled caseids
sample = dataset[dataset[case_id].isin(sampled_caseids)]

# Save the sample
sample.to_csv(f"output/{str(int(time.time()))}-sample_{sample_size}_cases.csv", index=False)

print(f"Sample stored in output/sample_{sample_size}_cases.csv")