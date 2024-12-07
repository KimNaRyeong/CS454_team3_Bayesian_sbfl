import os
import json
import networkx as nx
import re

def parse_node_format(node):
    """
    Parses the node to adjust to the format:
    org.jfree.chart$annotations.XYTextAnnotation -> org.jfree.chart$annotations.XYTextAnnotation#method()
    :param node: Original node string
    :return: Formatted node string
    """
    if "<" in node and ">" in node:
        # Remove only the outermost < and >
        node = re.sub(r"^<+|>+$", "", node)

        # Split the node into parts by ':' or '#'
        if ":" in node:
            class_part, method_part = node.split(":", 1)
        elif "#" in node:
            class_part, method_part = node.split("#", 1)
        else:
            class_part, method_part = node, ""

        # Extract the method name (last word)
        method_name = method_part.split()[-1].strip()  # Remove spaces

        # Replace the third '.' with '$'
        parts = class_part.split(".")
        if len(parts) > 3:
            # Join the first 3 parts with '.', then append the rest with '$' inserted
            formatted_class = ".".join(parts[:3]) + "$" + ".".join(parts[3:])
        else:
            formatted_class = class_part  # If less than 3 parts, no change

        # Construct the formatted node
        formatted_node = f"{formatted_class}#{method_name}"
        return formatted_node
    return node


def read_dot_file(file_path):
    """
    Reads a .dot file and extracts edges as a list of tuples with formatted nodes.
    :param file_path: Path to the .dot file
    :return: List of formatted edges
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()

    edges = []
    for line in lines:
        line = line.strip()
        if '->' in line:
            nodes = line.split('->')
            source = parse_node_format(nodes[0].strip().strip('"'))
            target = parse_node_format(nodes[1].strip().strip('";'))
            edges.append((source, target))
    return edges

def create_filtered_dag(edges, valid_nodes):
    """
    Creates a filtered DAG based on valid nodes in the method level spectrums.
    Includes edges only where both source and target are in valid_nodes,
    skipping intermediate nodes.
    :param edges: List of (source, target) edges
    :param valid_nodes: Set of valid method names from method level spectrum
    :return: Filtered DAG
    """
    # Build the original graph
    graph = nx.DiGraph()
    graph.add_edges_from(edges)

    # Create a new DAG containing only valid nodes
    filtered_dag = nx.DiGraph()

    # Iterate through all pairs of valid nodes
    for source in valid_nodes:
        for target in valid_nodes:
            if source != target:  # Avoid self-loops
                # Ensure both source and target are in the graph
                if source in graph and target in graph:
                    # Check if a path exists between source and target in the original graph
                    if nx.has_path(graph, source, target):
                        # If a path exists, add a direct edge between source and target
                        filtered_dag.add_edge(target, source)

    return filtered_dag

def save_dag_to_dot(dag, output_file):
    """
    Saves the DAG in .dot format with formatted nodes.
    :param dag: NetworkX DiGraph
    :param output_file: Path to save the .dot file
    """
    with open(output_file, 'w') as file:
        file.write("digraph G {\n")
        for source, target in dag.edges:
            file.write(f'  "{source}" -> "{target}";\n')
        file.write("}\n")

# Paths
input_folder = '/root/workspace/CS454_team3_Bayesian_sbfl/sootOutput'
output_folder = '/root/workspace/CS454_team3_Bayesian_sbfl/sootDAG_filtered'
spectrum_file = '/root/workspace/CS454_team3_Bayesian_sbfl/method_level_spectrums.json'

# Load method level spectrums
with open(spectrum_file, 'r') as file:
    spectrum_data = json.load(file)

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Get all files in the input folder as lowercase
files_in_input_folder = {f.lower(): f for f in os.listdir(input_folder)}

# Iterate through all charts in the spectrum data
for chart_key, methods in spectrum_data.items():
    # Map Chart-1 to chart1_dependency_graph.dot
    chart_index = chart_key.split("-")[1]
    expected_file_name = f"Chart{chart_index}_dependency_graph.dot".lower()

    # Check for case-insensitive match
    actual_file_name = files_in_input_folder.get(expected_file_name)
    if not actual_file_name:
        print(f"Input file {expected_file_name} does not exist in folder. Skipping.")
        continue

    input_file = os.path.join(input_folder, actual_file_name)
    output_file = os.path.join(output_folder, actual_file_name)

    if os.path.exists(output_file):
        print(f"Output file {output_file} already exists. Skipping.")
        continue
    # Read edges from the .dot file
    edges = read_dot_file(input_file)

    # Extract valid nodes for this chart
    valid_nodes = set(methods.keys())

    # Create a filtered DAG based on valid nodes
    filtered_dag = create_filtered_dag(edges, valid_nodes)

    # Save the filtered DAG to the output folder
    save_dag_to_dot(filtered_dag, output_file)

    print(f"Processed {actual_file_name} and saved to {output_file}")
