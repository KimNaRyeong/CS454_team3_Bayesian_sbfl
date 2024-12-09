import json
import os

def calculate_tarantula(data):
    """
    Calculates the Tarantula metric for each method.
    :param data: Dictionary containing spectrum data for a method.
    :return: Tarantula value.
    """
    e_p = data.get("e_p", 0)  # Passed tests that execute the method
    n_p = data.get("n_p", 0)  # Passed tests that do not execute the method
    e_f = data.get("e_f", 0)  # Failed tests that execute the method
    n_f = data.get("n_f", 0)  # Failed tests that do not execute the method

    # Calculate individual components
    numerator = e_f / (e_f + n_f) if (e_f + n_f) > 0 else 0
    denominator_part1 = e_p / (e_p + n_p) if (e_p + n_p) > 0 else 0
    denominator_part2 = e_f / (e_f + n_f) if (e_f + n_f) > 0 else 0

    # Avoid division by zero
    denominator = denominator_part1 + denominator_part2
    # suspiciousness = e_f * (1 if e_p == 0 else e_f/e_p)
    # return suspiciousness
    if denominator == 0:
        return 0.0

    # Calculate Tarantula metric
    tarantula = numerator / denominator
    return tarantula

def add_tarantula_to_spectrum(input_file, output_file):
    """
    Reads the spectrum JSON file, calculates Tarantula for each method, 
    and saves the updated data to a new file.
    :param input_file: Path to the input method level spectrum JSON file.
    :param output_file: Path to save the updated JSON file.
    """
    with open(input_file, 'r') as file:
        spectrum_data = json.load(file)

    # Iterate over each chart and its methods
    updated_data = {}
    for chart, methods in spectrum_data.items():
        updated_methods = {}
        for method, data in methods.items():
            # Calculate Tarantula metric
            tarantula_value = calculate_tarantula(data)
            # Add Tarantula value to the method's data
            updated_methods[method] = {**data, "tarantula": tarantula_value}
        updated_data[chart] = updated_methods

    # Save the updated spectrum data to the new file
    with open(output_file, 'w') as file:
        json.dump(updated_data, file, indent=4)

# File paths
input_file = '/root/workspace/CS454_team3_Bayesian_sbfl/method_level_spectrums.json'
output_file = '/root/workspace/CS454_team3_Bayesian_sbfl/method_level_spectrums_with_tarantula.json'

# Add Tarantula metric to the spectrum data and save to a new file
add_tarantula_to_spectrum(input_file, output_file)

print(f"Tarantula metrics saved to {output_file}")
