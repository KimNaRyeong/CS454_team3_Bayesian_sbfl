import json
import os
import math
import networkx as nx

def load_bayesian_network(file_path):
    """
    Loads a Bayesian Network from a .dot file.
    :param file_path: Path to the Bayesian Network .dot file.
    :return: NetworkX DiGraph representing the Bayesian Network.
    """
    graph = nx.DiGraph()
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if '->' in line:
                source, target = line.split('->')
                graph.add_edge(source.strip().strip('"'), target.strip().strip('";'))
            elif '[' in line and 'label=' in line:
                # Extract node attributes from the label
                node = line.split('[')[0].strip().strip('"')
                label_content = line.split('label=')[1].strip().strip('"')
                attrs = {}
                for item in label_content.split('\\n'):
                    if '=' in item:
                        key, value = item.split('=')
                        clean_value = value.strip().rstrip('"];')  # Remove unwanted characters
                        attrs[key.strip().lower()] = float(clean_value)
                graph.add_node(node, **attrs)
    return graph

def safe_divide(a, b):
    """Safe divide function to avoid division by zero."""
    return a / b if b != 0 else 0

def calculate_metrics(data):
    """
    Calculates various SBFL metrics for a method.
    :param data: Dictionary containing spectrum data for a method.
    :return: Dictionary with metric values.
    """
    e_p = data.get("e_p", 0)  # Passed tests that execute the method
    n_p = data.get("n_p", 0)  # Passed tests that do not execute the method
    e_f = data.get("e_f", 0)  # Failed tests that execute the method
    n_f = data.get("n_f", 0)  # Failed tests that do not execute the method

    return {
        "e_p": e_p,
        "n_p": n_p,
        "e_f": e_f,
        "n_f": n_f,
        "p": 1.0,  # Placeholder for probability
    }

def add_metrics_to_spectrum_separately(input_file, output_file, bayesian_networks_folder):
    """
    Reads the spectrum JSON file, calculates metrics for each method, 
    and saves the updated JSON with all metrics.
    :param input_file: Path to the input method level spectrum JSON file.
    :param output_file: Path to save the updated JSON file.
    :param bayesian_networks_folder: Directory containing Bayesian network files.
    """
    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' does not exist.")
        return

    with open(input_file, 'r') as file:
        try:
            spectrum_data = json.load(file)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return

    updated_spectrum = {}

    for chart, methods in spectrum_data.items():
        updated_spectrum[chart] = {}
        file_name = f"{chart}_bayesian_network.dot"
        bn_file_path = os.path.join(bayesian_networks_folder, file_name)

        # If Bayesian Network exists, load it
        bn = None
        if os.path.isfile(bn_file_path):
            bn = load_bayesian_network(bn_file_path)

        for method, data in methods.items():
            # Calculate metrics for the method
            metrics = calculate_metrics(data)

            # Update failure probability if Bayesian Network is available
            if bn and method in bn.nodes:
                node_data = bn.nodes[method]
                failure_probability = node_data.get("p(fail|node)", 0.0)
                metrics["p"] = failure_probability

            # Add the metrics to the updated spectrum
            updated_spectrum[chart][method] = metrics

    # Save the updated spectrum to the output file
    with open(output_file, 'w') as file:
        json.dump(updated_spectrum, file, indent=4)
    print(f"Updated spectrum saved to {output_file}")

# File paths
input_file = './method_level_spectrums.json'
output_file = './new_spectrum.json'
bayesian_networks_folder = './bayesian_networks'

# Add metrics to the spectrum data and save to the output file
add_metrics_to_spectrum_separately(input_file, output_file, bayesian_networks_folder)