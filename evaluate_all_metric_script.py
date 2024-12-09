import os
import json
import csv

def safe_divide(a, b):
    return a / b if b != 0 else 0

def evaluate_metrics_for_all_files(output_files, bug_data_dir, results_output_file):
    """
    Evaluates all SBFL metrics and records the results into a single file.
    :param output_files: Dictionary mapping metric names to their JSON file paths.
    :param bug_data_dir: Directory containing bug data JSON files.
    :param results_output_file: Path to the output results file (CSV format).
    """
    # Initialize the results list
    results = []

    # Define the projects to categorize WEFs
    projects = ['Math', 'Lang', 'Time', 'Chart']

    # Iterate over each metric and its corresponding file
    for metric_name, metric_file in output_files.items():
        print(f"Evaluating metric: {metric_name}")

        if not os.path.exists(metric_file):
            print(f"Metric file '{metric_file}' does not exist. Skipping.")
            continue

        with open(metric_file, 'r') as f:
            try:
                method_level_spectrum = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from '{metric_file}': {e}. Skipping.")
                continue

        acc1 = 0
        acc3 = 0
        acc5 = 0
        wefs = []
        wef_dict = {project: [] for project in projects}

        for bug, spectrum in method_level_spectrum.items():
            bug_file_path = os.path.join(bug_data_dir, f"{bug}.json")
            if not os.path.exists(bug_file_path):
                print(f"Bug data file '{bug_file_path}' does not exist. Skipping this bug.")
                continue

            with open(bug_file_path, 'r') as bf:
                try:
                    bug_info = json.load(bf)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from '{bug_file_path}': {e}. Skipping this bug.")
                    continue

            sbfl_scores = {}
            buggy_methods = [buggy_line.split(':')[0] for buggy_line in bug_info.get("buggy_lines", [])]

            for method, score in spectrum.items():
                if isinstance(score, dict):
                    # If the score is a dictionary, attempt to get the metric value
                    score_value = score.get(metric_name, None)
                else:
                    # If the score is a float, use it directly
                    score_value = score

                if score_value is not None:
                    sbfl_scores[method] = score_value
                else:
                    print(f"Method '{method}' does not have a score for metric '{metric_name}'. Skipping this method.")

            if not sbfl_scores:
                print(f"No SBFL scores found for bug '{bug}' with metric '{metric_name}'. Skipping this bug.")
                continue

            # Sort methods by their SBFL scores in descending order
            sorted_sbfl_scores = sorted(sbfl_scores.items(), key=lambda x: x[1], reverse=True)
            ranks = {method: rank+1 for rank, (method, _) in enumerate(sorted_sbfl_scores)}

            # Get ranks for all buggy methods
            buggy_methods_ranks = [ranks.get(buggy_method, len(sbfl_scores)+1) for buggy_method in buggy_methods]
            ranking = min(buggy_methods_ranks)  # Best rank among buggy methods

            # Accumulate accuracy metrics
            for rank in buggy_methods_ranks:
                if rank <= 1:
                    acc1 += 1
                if rank <= 3:
                    acc3 += 1
                if rank <= 5:
                    acc5 += 1

            wefs.append(ranking)

            # Per-project WEF
            project = bug.split('-')[0]
            if project in wef_dict:
                wef_dict[project].append(ranking)
            else:
                print(f"Unknown project '{project}' for bug '{bug}'. Skipping per-project WEF.")

        # Calculate average WEF
        average_wef = safe_divide(sum(wefs), len(wefs)) if wefs else 0

        # Calculate per-project WEF
        per_project_wef = {}
        for project in projects:
            per_project_wef[f"WEF_{project}"] = safe_divide(
                sum(wef_dict[project]), 
                len(wef_dict[project])
            ) if wef_dict[project] else 0

        # Append the results for this metric
        result_entry = {
            "metric": metric_name,
            "acc@1": acc1,
            "acc@3": acc3,
            "acc@5": acc5,
            "WEF_avg": average_wef
        }
        result_entry.update(per_project_wef)
        results.append(result_entry)

        print(f"Completed evaluation for metric: {metric_name}")

    # Define CSV fieldnames
    fieldnames = ["metric", "acc@1", "acc@3", "acc@5", "WEF_avg"] + [f"WEF_{project}" for project in projects]

    # Write all results to a CSV file
    with open(results_output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)

    print(f"All evaluation results have been saved to '{results_output_file}'.")

# Define output_files with all metrics
output_files = {
    "tarantula": os.path.join('./metric_value_json_output', 'method_level_spectrums_with_tarantula.json'),
    "ochiai": os.path.join('./metric_value_json_output', 'method_level_spectrums_with_ochiai.json'),
    "jaccard": os.path.join('./metric_value_json_output', 'method_level_spectrums_with_jaccard.json'),
    "sunwoo": os.path.join('./metric_value_json_output', 'method_level_spectrums_with_sunwoo.json'),
    "naryoung": os.path.join('./metric_value_json_output', 'method_level_spectrums_with_naryoung.json'),
    "donghan": os.path.join('./metric_value_json_output', 'method_level_spectrums_with_donghan.json'),
    "jihun": os.path.join('./metric_value_json_output', 'method_level_spectrums_with_jihun.json'),
}

# Directory containing bug data JSON files
bug_data_dir = './bug_data'

# Output results file
results_output_file = './evaluation_results.csv'

# Evaluate all metrics and save the results
evaluate_metrics_for_all_files(output_files, bug_data_dir, results_output_file)