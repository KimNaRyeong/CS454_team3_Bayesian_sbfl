import os
import json
import networkx as nx

def calculate_failure_probability(spectrum_data):
    """
    Calculates the failure probability for each method.
    :param spectrum_data: Dictionary containing spectrum data.
    :return: Dictionary of failure probabilities.
    """
    failure_probabilities = {}
    for method, data in spectrum_data.items():
        e_p = data.get("e_p", 0)
        n_p = data.get("n_p", 0)
        e_f = data.get("e_f", 0)
        n_f = data.get("n_f", 0)
        total = e_f + n_f
        if total > 0:
            failure_probabilities[method] = e_f / total
        else:
            failure_probabilities[method] = 0.0  # If no data, probability is 0
    return failure_probabilities

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

def create_bayesian_network(pdg, failure_probabilities):
    """
    Creates a Bayesian Network using the given PDG and failure probabilities.
    :param pdg: NetworkX DiGraph representing the PDG.
    :param failure_probabilities: Dictionary of failure probabilities for each method.
    :return: Bayesian Network as a NetworkX DiGraph.
    """
    bayesian_network = nx.DiGraph()
    for node in pdg.nodes:
        if node in failure_probabilities:
            # Add node with its failure probability as an attribute
            bayesian_network.add_node(node, failure_probability=failure_probabilities[node])
    for source, target in pdg.edges:
        if source in failure_probabilities and target in failure_probabilities:
            # Add edge if both nodes are in the failure probabilities
            bayesian_network.add_edge(source, target)
    return bayesian_network

def save_bayesian_network(bn, output_file):
    """
    Saves the Bayesian Network in .dot format.
    :param bn: Bayesian Network as a NetworkX DiGraph.
    :param output_file: Path to save the .dot file.
    """
    with open(output_file, 'w') as file:
        file.write("digraph G {\n")
        for node, attrs in bn.nodes(data=True):
            label = f'{node}\\nP(Fail|Node)={attrs["failure_probability"]:.2f}'
            file.write(f'  "{node}" [label="{label}"];\n')
        for source, target in bn.edges:
            file.write(f'  "{source}" -> "{target}";\n')
        file.write("}\n")

# Paths
filtered_pdg_folder = '/root/workspace/CS454_team3_Bayesian_sbfl/sootDAG_filtered'
spectrum_file = '/root/workspace/CS454_team3_Bayesian_sbfl/method_level_spectrums.json'
output_folder = '/root/workspace/CS454_team3_Bayesian_sbfl/bayesian_networks'

# Load method level spectrums
with open(spectrum_file, 'r') as file:
    spectrum_data = json.load(file)

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Get all files in the filtered PDG folder as lowercase
files_in_filtered_pdg = {f: f for f in os.listdir(filtered_pdg_folder)}

# Iterate through spectrum data and generate Bayesian Networks
for chart_key, methods in spectrum_data.items():
    # Calculate failure probabilities
    failure_probabilities = calculate_failure_probability(methods)

    # Match the corresponding filtered PDG
    chart_index = chart_key.split("-")[1]
    expected_file_name = f"Chart{chart_index}_dependency_graph.dot"

    # Check for case-insensitive match
    actual_file_name = files_in_filtered_pdg.get(expected_file_name)
    if not actual_file_name:
        print(f"PDG file {expected_file_name} does not exist. Skipping.")
        continue

    pdg_file = os.path.join(filtered_pdg_folder, actual_file_name)

    # Read the PDG
    pdg = read_pdg(pdg_file)

    # Create Bayesian Network
    bayesian_network = create_bayesian_network(pdg, failure_probabilities)

    # Save the Bayesian Network
    output_file = os.path.join(output_folder, f"Chart{chart_index}_bayesian_network.dot")
    if os.path.exists(output_file):
        print(f"Output file {output_file} already exists. Skipping.")
        continue
    save_bayesian_network(bayesian_network, output_file)

    print(f"Processed Bayesian Network for {chart_key} and saved to {output_file}")
