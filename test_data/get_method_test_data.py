import os
import json
import pandas as pd
import numpy as np
from tqdm import tqdm


def get_method_test_dict(bug_id):
    method_test_dict = {}

    bug_info_path = os.path.join(f"./bug_data/{bug_id}.json") 
    coverage_path = os.path.join(f"./bug_data/{bug_id}-cov.pkl")

    with open(bug_info_path, "r") as f:
        bug_info = json.load(f)

    coverage = pd.read_pickle(coverage_path)
    coverage.index = coverage.index.str.split(":").str[0]
    
    grouped_coverage = coverage.groupby(coverage.index).any()

    for method, coverage in grouped_coverage.iterrows():
        covering_tests = grouped_coverage.columns[coverage].tolist()

        method_test_dict[method] = covering_tests
    
    return method_test_dict 

all_bugs = [
    os.path.splitext(fname)[0]
    for fname in sorted(os.listdir("./bug_data"))
    if fname.endswith(".json")
]

total_bugs = len(all_bugs)

method_level_spectrums = dict()
all_bugs = ['Math-2']
for bug_id in tqdm(all_bugs):
    method_level_spectrums[bug_id] = get_method_test_dict(bug_id)

spectrum_file = './method_test_list_Math-2.json'



with open(spectrum_file, 'w') as f:
    json.dump(method_level_spectrums, f, indent=4)


