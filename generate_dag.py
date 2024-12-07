import os
import networkx as nx
import re

def parse_node_format(node):
    """
    Parses the node to adjust to the format:
    org.jfree.chart.annotations.XYTextAnnotation -> org.jfree.chart$annotations.XYTextAnnotation#method()
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
        method_name = method_part.split()[-1].replace(">", "").strip()  # method()

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
            edges.append((target, source))  # Reverse edges
    return edges

def create_dag(edges):
    """
    Creates a DAG using Spanning Tree approach by removing cycles.
    :param edges: List of (source, target) edges
    :return: A DAG (NetworkX DiGraph)
    """
    graph = nx.DiGraph()
    graph.add_edges_from(edges)

    dag = nx.DiGraph()
    visited = set()
    stack = set()

    def dfs(node):
        if node in stack:  # Cycle detected
            return
        if node in visited:
            return

        visited.add(node)
        stack.add(node)

        for neighbor in graph.successors(node):
            if neighbor not in visited:
                dag.add_edge(node, neighbor)
                dfs(neighbor)

        stack.remove(node)

    for node in graph.nodes:
        if node not in visited:
            dfs(node)

    return dag

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

# Process all .dot files in /root/workspace/prev_graphs and save to /root/workspace/processed_graph
input_folder = '/root/workspace/CS454_team3_Bayesian_sbfl/sootOutput'
output_folder = '/root/workspace/CS454_team3_Bayesian_sbfl/sootDAG'

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Iterate through all .dot files in the input folder
for file_name in os.listdir(input_folder):
    if file_name.endswith('.dot'):
        input_file = os.path.join(input_folder, file_name)
        output_file = os.path.join(output_folder, file_name)

        # Read edges from the .dot file
        edges = read_dot_file(input_file)

        # Create a DAG from the edges
        dag = create_dag(edges)

        # Save the DAG to the output folder
        save_dag_to_dot(dag, output_file)

        print(f"Processed {file_name} and saved to {output_file}")
