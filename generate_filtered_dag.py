import os
import json
import networkx as nx
import re
import matplotlib.pyplot as plt

def parse_node_format(node):
    """
    Parses the node to adjust to the format:
    org.jfree.chart$annotations.XYTextAnnotation -> org.jfree.chart$annotations.XYTextAnnotation#method()
    :param node: Original node string
    :return: Formatted node string
    """
    
    node = node.strip('<>')
    until_class, method = node.split(": ")

    parsed_until_class = until_class.split('$')
    without_digit_parsed_until_class = []
    for i in parsed_until_class:
        if not i.isdigit():
            without_digit_parsed_until_class.append(i)

    until_class = '$'.join(without_digit_parsed_until_class)

    if method.startswith("void <init>"):
        if '$' in until_class:
            before_dol = until_class.split("$")[0]
            second_class = until_class.split("$")[-1]
            first_class = before_dol.split('.')[-1]
            package = ".".join(before_dol.split('.')[:-1])
            argument = method.split("void <init>")[-1]

            formated_method = package+'$'+first_class+'$'+second_class+'#'+first_class+'$'+second_class+argument
            
        else:
            package = ".".join(until_class.split('.')[:-1])
            class_name = until_class.split('.')[-1]
            argument = method.split("void <init>")[-1]

            formated_method = package + '$' + class_name + '#' + class_name + argument
            
    
    else:
        packages = ".".join(until_class.split(".")[:-1])
        class_name = until_class.split(".")[-1]
        formated_until_class = packages+"$"+class_name

        method = method.split()[-1]
        formated_method = formated_until_class+'#'+method

    return formated_method


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
            source, target = line.split('->')
            # print("----------------------")
            # print(source)
            # print(source.strip().strip('"'))
            source = parse_node_format(source.strip().strip('"'))
            
            # print("-----------------------------")
            # print(target)
            # print(target.strip().strip('";'))
            target = parse_node_format(target.strip().strip('";'))
            edges.append((source, target))
            
            # print("--------------------------")
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
    # graph = nx.DiGraph()
    # graph.add_edges_from(edges)

    # Create a new DAG containing only valid nodes
    filtered_dag = nx.DiGraph()

    # Iterate through all pairs of valid nodes
    for source, target in edges:
        # if source not in valid_nodes:
        #     print(source)
        #     # pass
        # if target not in valid_nodes:
        #     print(target)
        #     # pass
        if source in valid_nodes and target in valid_nodes and source != target:
            # print(source)
            if not filtered_dag.has_edge(source, target):
                filtered_dag.add_edge(source, target)
        
    # nx.draw(filtered_dag, with_labels=True, node_color="lightblue", edge_color="gray", node_size=2000, font_size=15)
    # plt.title("Example Graph Visualization")
    # # plt.show()
    # plt.savefig("./graph.png", format="png", dpi=300)  # 저장 파일명과 포맷 설정
    # plt.close()
    # for source in valid_nodes:
    #     for target in valid_nodes:
    #         if source != target:  # Avoid self-loops
    #             # Ensure both source and target are in the graph
    #             if source in graph and target in graph:
    #                 # Check if a path exists between source and target in the original graph
    #                 if nx.has_path(graph, source, target):
    #                     # If a path exists, add a direct edge between source and target
    #                     filtered_dag.add_edge(target, source)
    #             else:
    #                 print(source)
    #                 print(target)
    #                 print("-----------------")

    
    return filtered_dag

def create_filtered_dag(edges, valid_nodes):
    original = nx.DiGraph()
    original.add_nodes_from(valid_nodes)
    edges = [(u, v) for u, v in edges if u in valid_nodes and v in valid_nodes]

    original.add_edges_from(edges)
    
    path_exists = dict(nx.all_pairs_shortest_path_length(original))

    projected_graph = nx.DiGraph()
    for source in valid_nodes:
        for target in valid_nodes:
            if source != target and target in path_exists.get(source, {}):
                projected_graph.add_edge(source, target)

    return projected_graph


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
# input_folder = '/root/workspace/CS454_team3_Bayesian_sbfl/sootOutput'
# output_folder = '/root/workspace/CS454_team3_Bayesian_sbfl/sootDAG_filtered'
# spectrum_file = '/root/workspace/CS454_team3_Bayesian_sbfl/method_level_spectrums.json'

input_folder = './sootOutput'
output_folder = './sootDAG_filtered'
spectrum_file = './method_level_spectrums.json'

# Load method level spectrums
with open(spectrum_file, 'r') as file:
    spectrum_data = json.load(file)

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Get all files in the input folder as lowercase
files_in_input_folder = {f.lower(): f for f in os.listdir(input_folder)}

# Iterate through all charts in the spectrum data
# for chart_key, methods in spectrum_data.items():
all_bugs = [bug.split('_')[0] for bug in os.listdir('./sootDAG_filtered')]
for project in all_bugs:
    methods = spectrum_data[project]
    # if not chart_key.startswith('Chart'):
    #     continue
    # Map Chart-1 to chart1_dependency_graph.dot
    # if chart_key != "Chart-1":
    #     continue
    pid, vid = project.split("-")
    expected_file_name = f"{pid}{vid}_dependency_graph.dot".lower()
    output_file_name = f"{project}_dependency_graph.dot"

    # Check for case-insensitive match
    actual_file_name = files_in_input_folder.get(expected_file_name)
    if not actual_file_name:
        print(f"Input file {expected_file_name} does not exist in folder. Skipping.")
        continue

    input_file = os.path.join(input_folder, actual_file_name)
    output_file = os.path.join(output_folder, output_file_name)

    if os.path.exists(output_file):
        print(f"Output file {output_file} already exists. Skipping.")
        # continue
    # Read edges from the .dot file
    edges = read_dot_file(input_file)
    # for edge in edges[:10]:
    #     print(edge)
    # print(edges)

    # Extract valid nodes for this chart
    valid_nodes = set(methods.keys())

    # Create a filtered DAG based on valid nodes
    filtered_dag = create_filtered_dag(edges, valid_nodes)
    # if nx.is_directed_acyclic_graph(filtered_dag) and len(filtered_dag.nodes) > 0:
    #     print(pid, vid)
    #     save_dag_to_dot(filtered_dag, output_file)

    #     print(f"Processed {output_file_name} and saved to {output_file}")
    
    
    
    # print(pid, vid)
    # save_dag_to_dot(filtered_dag, output_file)
    # print(f"Processed {output_file_name} and saved to {output_file}")
    
    
    
    
    
    # else:
    #     cycles = list(nx.simple_cycles(filtered_dag))
    #     print("Cycles detected:")
    #     for cycle in cycles:
    #         for edge in cycle:
    #             print(edge)
    #         print("--------------------")
    #     print(len(cycles))
                # print(f"Edge: {edge[0]} -> {edge[1]}")
    # Save the filtered DAG to the output folder
    # save_dag_to_dot(filtered_dag, output_file)

    # print(f"Processed {actual_file_name} and saved to {output_file}")
