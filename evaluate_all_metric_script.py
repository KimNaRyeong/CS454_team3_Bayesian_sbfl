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
        wef_dict = {'Math': [], 'Lang': [], 'Time': [], 'Chart': []}

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

            for method, spectra in spectrum.items():
                score = spectra.get(metric_name, None)
                if score is not None:
                    sbfl_scores[method] = score
                else:
                    print(f"Method '{method}' does not have a score for metric '{metric_name}'. Skipping this method.")

            if not sbfl_scores:
                print(f"No SBFL scores found for bug '{bug}' with metric '{metric_name}'. Skipping this bug.")
                continue

            sorted_sbfl_scores = sorted(sbfl_scores.items(), key=lambda x: x[1], reverse=True)
            ranks = {method: rank+1 for rank, (method, _) in enumerate(sorted_sbfl_scores)}
            buggy_methods_ranks = [ranks.get(buggy_method, len(sbfl_scores)+1) for buggy_method in buggy_methods]
            ranking = min(buggy_methods_ranks)

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
        wef_Math = safe_divide(sum(wef_dict['Math']), len(wef_dict['Math'])) if wef_dict['Math'] else 0
        wef_Lang = safe_divide(sum(wef_dict['Lang']), len(wef_dict['Lang'])) if wef_dict['Lang'] else 0
        wef_Time = safe_divide(sum(wef_dict['Time']), len(wef_dict['Time'])) if wef_dict['Time'] else 0
        wef_Chart = safe_divide(sum(wef_dict['Chart']), len(wef_dict['Chart'])) if wef_dict['Chart'] else 0

        # Append the results for this metric
        results.append({
            "metric": metric_name,
            "acc@1": acc1,
            "acc@3": acc3,
            "acc@5": acc5,
            "WEF_avg": average_wef,
            "WEF_Math": wef_Math,
            "WEF_Lang": wef_Lang,
            "WEF_Time": wef_Time,
            "WEF_Chart": wef_Chart
        })

        print(f"Completed evaluation for metric: {metric_name}")

    # Write all results to a CSV file
    with open(results_output_file, 'w', newline='') as csvfile:
        fieldnames = ["metric", "acc@1", "acc@3", "acc@5", "WEF_avg", "WEF_Math", "WEF_Lang", "WEF_Time", "WEF_Chart"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for result in results:
            writer.writerow(result)

    print(f"All evaluation results have been saved to '{results_output_file}'.")

# Define output_files with all metrics
output_files = {
    "tarantula": os.path.join('./metrics_output', 'method_level_spectrums_with_tarantula.json'),
    "ochiai": os.path.join('./metrics_output', 'method_level_spectrums_with_ochiai.json'),
    "jaccard": os.path.join('./metrics_output', 'method_level_spectrums_with_jaccard.json'),
    "sunwoo": os.path.join('./metrics_output', 'method_level_spectrums_with_sunwoo.json'),
    "naryoung": os.path.join('./metrics_output', 'method_level_spectrums_with_naryoung.json'),
    "donghan": os.path.join('./metrics_output', 'method_level_spectrums_with_donghan.json'),
    "jihun": os.path.join('./metrics_output', 'method_level_spectrums_with_jihun.json'),
}

# Directory containing bug data JSON files
bug_data_dir = './bug_data'

# Output results file
results_output_file = './evaluation_results.csv'

# Evaluate all metrics and save the results
evaluate_metrics_for_all_files(output_files, bug_data_dir, results_output_file)