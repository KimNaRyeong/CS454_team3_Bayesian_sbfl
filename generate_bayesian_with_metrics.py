import json
import os
import math
import networkx as nx
import tqdm

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

# Safe divide function to avoid division by zero
def safe_divide(a, b):
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

    # Tarantula metric
    numerator_tarantula = safe_divide(e_f, e_f + n_f)
    denominator_tarantula = safe_divide(e_p, e_p + n_p) + safe_divide(e_f, e_f + n_f)
    tarantula = safe_divide(numerator_tarantula, denominator_tarantula)

    # Ochiai metric
    denominator_ochiai = (e_f + n_f) * (e_f + e_p)
    ochiai = safe_divide(e_f, math.sqrt(denominator_ochiai))

    # Jaccard metric
    jaccard = safe_divide(e_f, e_f + e_p + n_f)

    # Sunwoo metric
    x = 0.0 if (e_f + n_f) == 0 else safe_divide(e_f, (e_f + n_f))
    y = 0.0 if (e_p + n_p) == 0 else safe_divide(e_p, (e_p + n_p))
    
    suspiciousness_sunwoo = math.sqrt(safe_divide(math.sqrt(math.sqrt(x)) , (1.0 + math.sqrt(y))))

    # Naryoung
    suspiciousness_naryoung = e_f * (1 if e_p == 0 else safe_divide(e_f, e_p))

    # Donghan
    suspiciousness_donghan = (1 if 1 == 0 else ((1 if e_f == 0 else safe_divide(n_p * e_f, e_f)) * n_p) / 1) - ((n_f + e_p) + e_f)

    # Jihun
    suspiciousness_jihun = (e_p - safe_divide(e_p, (n_f + 31))) - (safe_divide(30 + e_f, e_f))

    return {
        "tarantula": tarantula,
        "ochiai": ochiai,
        "jaccard": jaccard,

        "sunwoo": suspiciousness_sunwoo,
        "naryoung": suspiciousness_naryoung,
        "donghan": suspiciousness_donghan,
        "jihun": suspiciousness_jihun,
    }

def add_metrics_to_spectrum_separately(input_file, output_dir, bayesian_networks_folder):
    """
    Reads the spectrum JSON file, calculates metrics for each method, 
    and saves each metric to separate JSON files.
    :param input_file: Path to the input method level spectrum JSON file.
    :param output_dir: Directory to save the updated JSON files for each metric.
    """
    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' does not exist.")
        return

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    with open(input_file, 'r') as file:
        try:
            spectrum_data = json.load(file)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return

    # Initialize dictionaries for each metric
    metrics_data = {
        "tarantula": {},
        "ochiai": {},
        "jaccard": {},

        "sunwoo": {},
        "naryoung": {},
        "donghan": {},
        "jihun": {},
        "bayesian": {},
    }



    # Iterate over each chart and its methods
    for chart, methods in spectrum_data.items():
        file_name = f"{chart}_bayesian_network.dot"
        bn_file_path = os.path.join(bayesian_networks_folder, file_name)
        # bn = load_bayesian_network(bn_file_path)

        metrics_data["tarantula"][chart] = {}
        metrics_data["ochiai"][chart] = {}
        metrics_data["jaccard"][chart] = {}

        metrics_data["sunwoo"][chart] = {}
        metrics_data["naryoung"][chart] = {}
        metrics_data["donghan"][chart] = {}
        metrics_data["jihun"][chart] = {}
        metrics_data["bayesian"][chart] = {}

        for method, data in methods.items():
            # Calculate all metrics
            metrics = calculate_metrics(data)
            # Assign each metric to its respective dictionary
            metrics_data["tarantula"][chart][method] = metrics["tarantula"]
            metrics_data["ochiai"][chart][method] = metrics["ochiai"]
            metrics_data["jaccard"][chart][method] = metrics["jaccard"]

            metrics_data["sunwoo"][chart][method] = metrics["sunwoo"]
            metrics_data["naryoung"][chart][method] = metrics["naryoung"]
            metrics_data["donghan"][chart][method] = metrics["donghan"]
            metrics_data["jihun"][chart][method] = metrics["jihun"]
            metrics_data["bayesian"][chart][method] = 0.3
        
        if os.path.isfile(bn_file_path):
            # print("hello")
            bn = load_bayesian_network(bn_file_path)
            for method, data in methods.items():
                # Calculate all metrics
                metrics = calculate_metrics(data)
                # Assign each metric to its respective dictionary
                if method in bn.nodes:
                    node_data = bn.nodes[method]
                    failure_probability = node_data.get("p(fail|node)", 0.0)
                    metrics_data["tarantula"][chart][method] = metrics["tarantula"]*(1 - 0.7*failure_probability)
                    metrics_data["ochiai"][chart][method] = metrics["ochiai"]*(1 - 0.7*failure_probability)
                    metrics_data["jaccard"][chart][method] = metrics["jaccard"]*(1 - 0.7*failure_probability)

                    metrics_data["sunwoo"][chart][method] = metrics["sunwoo"]*(1 - 0.7*failure_probability)
                    metrics_data["naryoung"][chart][method] = metrics["naryoung"]*(1 - 0.7*failure_probability)
                    metrics_data["donghan"][chart][method] = metrics["donghan"]*(1 - 0.7*failure_probability)
                    metrics_data["jihun"][chart][method] = metrics["jihun"]*(1 - 0.7*failure_probability)
                    metrics_data["bayesian"][chart][method] = (1 - 0.7*failure_probability)
        

    output_files = {
        "tarantula": os.path.join(output_dir, 'bayesian_with_tarantula.json'),
        "ochiai": os.path.join(output_dir, 'bayesian_with_ochiai.json'),
        "jaccard": os.path.join(output_dir, 'bayesian_with_jaccard.json'),

        "sunwoo": os.path.join(output_dir, 'bayesian_with_sunwoo.json'),
        "naryoung": os.path.join(output_dir, 'bayesian_with_naryoung.json'),
        "donghan": os.path.join(output_dir, 'bayesian_with_donghan.json'),
        "jihun": os.path.join(output_dir, 'bayesian_with_jihun.json'),
        "bayesian": os.path.join(output_dir, 'bayesian.json'),
    }

    # Save each metric data to its respective file
    for metric, file_path in output_files.items():
        with open(file_path, 'w') as file:
            json.dump(metrics_data[metric], file, indent=4)
        print(f"{metric.capitalize()} metrics saved to {file_path}")

# File paths
input_file = './method_level_spectrums.json'
output_dir = './metric_value_json_output'  # Directory to store individual metric files
bayesian_networks_folder = './bayesian_networks_old'
# Add metrics to the spectrum data and save to separate files
add_metrics_to_spectrum_separately(input_file, output_dir, bayesian_networks_folder)