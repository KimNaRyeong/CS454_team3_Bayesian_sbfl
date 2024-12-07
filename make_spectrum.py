import os
import json
import pandas as pd
import numpy as np
from tqdm import tqdm

def get_spectrum(coverage_df, failing_tests):

    X = coverage_df.values.transpose()

    is_failing = np.array([test in failing_tests for test in coverage_df.columns])

    e_p = X[~is_failing].sum(axis=0)
    e_f = X[is_failing].sum(axis=0)
    n_p = np.sum(~is_failing) - e_p
    n_f = np.sum(is_failing) - e_f

    return e_p, n_p, e_f, n_f


all_bugs = [
    os.path.splitext(fname)[0]
    for fname in sorted(os.listdir("./bug_data"))
    if fname.endswith(".json")
]

total_bugs = len(all_bugs)


def make_spectrum_dict(bug_id):

    bug_info_path = os.path.join(f"./bug_data/{bug_id}.json") 
    coverage_path = os.path.join(f"./bug_data/{bug_id}-cov.pkl")

    with open(bug_info_path, "r") as f:
        bug_info = json.load(f)

    coverage = pd.read_pickle(coverage_path)
    coverage.index = coverage.index.str.split(":").str[0]
    
    grouped_coverage = coverage.groupby(coverage.index).any()

    e_p, n_p, e_f, n_f = get_spectrum(grouped_coverage, bug_info["failing_tests"])

    spectrum_dict = {}
    for i, method in enumerate(grouped_coverage.index):
        spectrum_dict[method] = {
            'e_p': int(e_p[i]),
            'n_p': int(n_p[i]),
            'e_f': int(e_f[i]),
            'n_f': int(n_f[i]) 
        }
    
    return spectrum_dict 


method_level_spectrums = dict()

for bug_id in tqdm(all_bugs):
    method_level_spectrums[bug_id] = make_spectrum_dict(bug_id)

spectrum_file = './method_level_spectrums.json'

with open(spectrum_file, 'w') as f:
    json.dump(method_level_spectrums, f, indent=4)


