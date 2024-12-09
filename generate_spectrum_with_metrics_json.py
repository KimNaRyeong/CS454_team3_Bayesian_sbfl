import json
import os
import math

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


    # Naryoung


    # Donghan


    # Jihun metric (Custom metric based on user's original formula)
    # 주의: 이 공식이 의도한 대로 동작하는지 검증 필요
    suspiciousness_jihun = ((n_f - n_p) - n_p) + (((e_p + (n_p - (e_f + n_p))) * 70) * e_f)

    return {
        "tarantula": tarantula,
        "ochiai": ochiai,
        "jaccard": jaccard,
        "jihun": suspiciousness_jihun,

    }

def add_metrics_to_spectrum_separately(input_file, output_dir):
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

        "jihun": {},
    }

    # Iterate over each chart and its methods
    for chart, methods in spectrum_data.items():
        metrics_data["tarantula"][chart] = {}
        metrics_data["ochiai"][chart] = {}
        metrics_data["jaccard"][chart] = {}

        metrics_data["jihun"][chart] = {}


        for method, data in methods.items():
            # Calculate all metrics
            metrics = calculate_metrics(data)
            # Assign each metric to its respective dictionary
            metrics_data["tarantula"][chart][method] = metrics["tarantula"]
            metrics_data["ochiai"][chart][method] = metrics["ochiai"]
            metrics_data["jaccard"][chart][method] = metrics["jaccard"]

            metrics_data["jihun"][chart][method] = metrics["jihun"]


    # Define file names for each metric
    output_files = {
        "tarantula": os.path.join(output_dir, 'method_level_spectrums_with_tarantula.json'),
        "ochiai": os.path.join(output_dir, 'method_level_spectrums_with_ochiai.json'),
        "jaccard": os.path.join(output_dir, 'method_level_spectrums_with_jaccard.json'),

        "jihun": os.path.join(output_dir, 'method_level_spectrums_with_jihun.json'),
    }

    # Save each metric data to its respective file
    for metric, file_path in output_files.items():
        with open(file_path, 'w') as file:
            json.dump(metrics_data[metric], file, indent=4)
        print(f"{metric.capitalize()} metrics saved to {file_path}")

# File paths
input_file = './method_level_spectrums.json'
output_dir = './metric_value_json_output'  # Directory to store individual metric files

# Add metrics to the spectrum data and save to separate files
add_metrics_to_spectrum_separately(input_file, output_dir)