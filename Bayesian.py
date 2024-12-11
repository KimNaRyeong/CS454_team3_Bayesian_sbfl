import os
import json
import networkx as nx
import pandas as pd
import numpy as np


all_bugs = [
    os.path.splitext(fname)[0]
    for fname in sorted(os.listdir("./bug_data"))
    if fname.endswith(".json")
]

total_bugs = len(all_bugs)
# test_file = "./method_test_list_Math-2.json"

# with open(test_file, 'r') as file:
#     all_test = json.load(file)

# total_test = len(all_test)

# def calculate_failure_probability(spectrum_data):
#     """
#     Calculates the failure probability for each method.
#     :param spectrum_data: Dictionary containing spectrum data.
#     :return: Dictionary of failure probabilities.
#     """
#     failure_probabilities = {}
#     for method, data in spectrum_data.items():
#         e_p = data.get("e_p", 0)
#         n_p = data.get("n_p", 0)
#         e_f = data.get("e_f", 0)
#         n_f = data.get("n_f", 0)
#         total = e_f + n_f
#         if total > 0:
#             failure_probabilities[method] = e_f / total
#         else:
#             failure_probabilities[method] = 0.0  # If no data, probability is 0
#     return failure_probabilities

def read_pdg(file_path):
    """
    Reads a PDG from a .dot file and creates a NetworkX graph.
    :param file_path: Path to the .dot file.
    :return: NetworkX DiGraph.
    """
    graph = nx.DiGraph()
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if '->' in line:
                nodes = line.split('->')
                source = nodes[0].strip().strip('"')
                target = nodes[1].strip().strip('";')
                graph.add_edge(source, target)
    return graph

def create_bayesian_network(pdg, coverage_df, failing_tests):
    # if not isinstance(coverage_df, pd.DataFrame):
    #     raise TypeError("coverage_df must be a pandas DataFrame")
    X = coverage_df.to_numpy().transpose()

    # is_failing = np.array([test in failing_tests for test in coverage_df.columns]) 
    is_failing = [
    idx for idx, test in enumerate(coverage_df.columns) if test in failing_tests]
    total_test = len(coverage_df.columns)
    bayesian_network = nx.DiGraph()
    # print(coverage_df)
    for node in pdg.nodes:
        if node not in coverage_df.index:
            bayesian_network.add_node(node, failure_probability=0.0)
            continue
        successors = list(pdg.successors(node))
        if len(successors) == 0: # 고립된 노드
            prob = 0
            a = np.sum(X[is_failing, :][:, [node_index]].any(axis=1))
            prob = a / total_test
            bayesian_network.add_node(node, failure_probability = prob)
            continue
        
        # 연결된 노드
        line_indices = [coverage_df.index.get_loc(line) for line in successors if line in coverage_df.index]
        node_index = coverage_df.index.get_loc(node)
        b = total_test - np.sum(X[is_failing, :][:, line_indices].any(axis=1)) # 자식 노드들에서 실패하지 않은 테스트 케이스의 수
        a = np.sum(X[is_failing, :][:, [node_index] + line_indices].any(axis=1)) - np.sum(X[is_failing, :][:, line_indices].any(axis=1))

        # a=0
        # b=0
        # for key, value in all_test.items():
        #     if not isinstance(value, set):
        #         value = set(value)
        #     if value.isdisjoint(successors) or key not in failing_tests:
        #         b += 1

        # for key, value in all_test.items():
        #     if not isinstance(value, set):
        #         value = set(value)
        #     if value.isdisjoint(successors) and key in failing_tests and node in value:
        #         a += 1

        # total_test - np.sum(X[is_failing, :][:, line_indices].any(axis=1)) - np.sum(~X[is_failing, :][:, node_index])
        # 자식 노드들에서 실패하지 않고, 현재 노드에서 실패한 테스트 케이스의 수 
        # print(p, q)
        # d = total_test - np.sum(X[~is_failing, :][:, line_indices].any(axis=1)) # 자식 노드들에서 성공하지 않은 테스트 케이스의 수
        # c = np.sum(X[~is_failing, :][:, [node_index] + line_indices].any(axis=1)) - np.sum(X[~is_failing, :][:, line_indices].any(axis=1))
        # total_test - np.sum(X[is_failing, :][:, line_indices].any(axis=1)) - np.sum(~X[is_failing, :][:, node_index])
        # 자식 노드들에서 성공하지 않고, 현재 노드에서 성공한 테스트 케이스의 수 
        # print(p, q)
        prob = 0
        if b != 0:
            prob = a / b

        bayesian_network.add_node(node, failure_probability=prob)

    for source, target in pdg.edges:
        bayesian_network.add_edge(source, target)

    return bayesian_network

def save_bayesian_network(bn, output_file):
    with open(output_file, 'w') as file:
        file.write("digraph G {\n")
        for node, attrs in bn.nodes(data=True):
            failure_prob = attrs.get("failure_probability")
            label = f'{node}\\nP(Fail|Node)={failure_prob:.2f}'
            file.write(f'  "{node}" [label="{label}"];\n')
        for source, target in bn.edges:
            file.write(f'  "{source}" -> "{target}";\n')
        file.write("}\n")

# Paths
filtered_pdg_folder = './sootDAG_filtered'
spectrum_file = './method_level_spectrums.json'
output_folder = './bayesian_networks'

# Load method level spectrums
with open(spectrum_file, 'r') as file:
    spectrum_data = json.load(file)

os.makedirs(output_folder, exist_ok=True)

files_in_filtered_pdg = {f: f for f in os.listdir(filtered_pdg_folder)}

for chart_key, methods in spectrum_data.items():
    expected_file_name = f"{chart_key}_dependency_graph.dot"
    actual_file_name = files_in_filtered_pdg.get(expected_file_name)
    if not actual_file_name:
        print(f"PDG file {expected_file_name} does not exist. Skipping.")
        continue

    pdg_file = os.path.join(filtered_pdg_folder, actual_file_name)

    pdg = read_pdg(pdg_file)
    bug_info_path = os.path.join(f"./bug_data/{chart_key}.json") 
    coverage_path = os.path.join(f"./bug_data/{chart_key}-cov.pkl")
    with open(bug_info_path, "r") as f:
        bug_info = json.load(f)

    coverage = pd.read_pickle(coverage_path)
    # print(coverage.dtypes) 

    coverage.index = coverage.index.str.split(":").str[0]

    coverage_bool = coverage.astype(bool)

    unique_indices = coverage_bool.index.unique()

    grouped_coverage = {}
    for index in unique_indices:
        subset = coverage_bool[coverage_bool.index == index]
        result = subset.any(axis=0)
        grouped_coverage[index] = result

    grouped_coverage_df = pd.DataFrame.from_dict(grouped_coverage, orient="index")

    grouped_coverage_df.index.name = "method"
    grouped_coverage_df.columns.name = "tests"

    # Create Bayesian Network
    bayesian_network = create_bayesian_network(pdg, grouped_coverage_df, bug_info["failing_tests"])

    # Save the Bayesian Network
    output_file = os.path.join(output_folder, f"{chart_key}_bayesian_network.dot")
    if os.path.exists(output_file):
        print(f"Output file {output_file} already exists. Skipping.")
        continue
    save_bayesian_network(bayesian_network, output_file)

    print(f"Processed Bayesian Network for {chart_key} and saved to {output_file}")
