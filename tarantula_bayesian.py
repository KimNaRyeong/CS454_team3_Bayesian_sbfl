import os
import json
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

def adjust_tarantula_values(bn, spectrum_data):
    """
    Adjusts tarantula values in the Bayesian Network using failure probabilities.
    Only modifies the values for nodes present in the Bayesian Network.
    :param bn: NetworkX DiGraph representing the Bayesian Network.
    :param spectrum_data: Spectrum data containing tarantula values.
    :return: Adjusted spectrum data.
    """
    adjusted_data = spectrum_data.copy()  # Start with original spectrum data

    # Adjust tarantula values for nodes in the Bayesian Network
    for node in bn.nodes:
        # Extract tarantula value and failure probability
        node_data = bn.nodes[node]
        failure_probability = node_data.get("p(fail|node)", 0.0)
        # tarantula = adjusted_data.get("tarantula", 0.0)  # Default to 0.0 if missing
        # failure_probability = node_data.get("p(fail|node)", 0.0)

        # # Apply adjustment to child nodes
        # for child in bn.successors(node):
        #     if child in bn.nodes:
        #         child_data = bn.nodes[child]
        #         adjustment = 0.5 * failure_probability
        #         child_tarantula = child_data.get("tarantula", 0.0)  # Default to 0.0 if missing
        #         child_data["tarantula"] = max(0.0, child_tarantula - adjustment)  # Ensure non-negative
        # # Update adjusted tarantula value in the spectrum data

        if node in spectrum_data:
            tarantula = spectrum_data[node]["tarantula"]
            adjusted_data[node]["tarantula"] = tarantula*(1 - failure_probability)

    return adjusted_data

def save_adjusted_spectrum(adjusted_data, output_file):
    """
    Saves the adjusted spectrum data to a JSON file.
    :param adjusted_data: Adjusted spectrum data.
    :param output_file: Path to save the JSON file.
    """
    with open(output_file, 'w') as file:
        json.dump(adjusted_data, file, indent=4)

# Paths
bayesian_networks_folder = './bayesian_networks'
spectrum_file = './method_level_spectrums_with_tarantula.json'
output_file = './adjusted_spectrum.json'

# Load method level spectrum data
with open(spectrum_file, 'r') as file:
    spectrum_data = json.load(file)

# Iterate through Bayesian Networks and adjust tarantula values
adjusted_spectrum = spectrum_data.copy()  # Start with original spectrum data
for file_name in os.listdir(bayesian_networks_folder):
    if file_name.endswith('.dot'):
        bn_file_path = os.path.join(bayesian_networks_folder, file_name)
        chart_key = file_name.split('_')[0]  # Extract chart key (e.g., Chart-1)
        
        # Load Bayesian Network
        bn = load_bayesian_network(bn_file_path)

        # Get the spectrum data for the chart
        chart_spectrum = spectrum_data.get(chart_key, {})

        # Adjust tarantula values for this chart
        adjusted_chart_data = adjust_tarantula_values(bn, chart_spectrum)
        adjusted_spectrum[chart_key] = adjusted_chart_data

# Save adjusted spectrum to JSON
save_adjusted_spectrum(adjusted_spectrum, output_file)

print(f"Adjusted spectrum saved to {output_file}")
