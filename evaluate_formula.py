import os
import json
import random

# spectrum_file = './adjusted_spectrum.json'
spectrum_file = './method_level_spectrums_with_tarantula.json'
spectrum_file = './method_level_spectrums_nar.json'
# spectrum_file = './method_level_spectrums_dong.json'

with open(spectrum_file, 'r') as f:
    method_level_spectrum = json.load(f)

all_bugs = list(method_level_spectrum.keys())


def evaluate_formula():
    acc1 = 0
    acc3 = 0
    acc5 = 0
    wefs = []

    for bug, spectrum in method_level_spectrum.items():
        with open(f"./bug_data/{bug}.json", 'r') as f:
            bug_info = json.load(f)
        
        sbfl_scores = {}
        buggy_methods = [buggy_lines.split(':')[0] for buggy_lines in bug_info["buggy_lines"]]
        for method, spectra in spectrum.items():
            try:
                sbfl_scores[method] = spectra["tarantula"]
            except:
                print("wrong")

            
        sorted_sbfl_scores = sorted(sbfl_scores.items(), key=lambda x: x[1], reverse=True)
        ranks = {method: rank+1 for rank, (method, _) in enumerate(sorted_sbfl_scores)}
        buggy_methods_ranks = [ranks[buggy_method] for buggy_method in buggy_methods]
        ranking = min(buggy_methods_ranks)
        # print(ranking)
        for rank in buggy_methods_ranks:
            if rank <= 1:
                acc1 += 1
            if rank <= 3:
                acc3 += 1
            if rank <= 5:
                acc5 += 1

        # if ranking == 1:
        #     acc1 += 1
        wefs.append(ranking)
    
    return acc1, acc3, acc5, sum(wefs) / len(wefs)

def evaluate_formula_per_project():
    wef_dict = {'Math': [], 'Lang': [], 'Time': [], 'Chart': []}
    for bug, spectrum in method_level_spectrum.items():
        with open(f"./bug_data/{bug}.json", 'r') as f:
            bug_info = json.load(f)

        sbfl_scores = {}
        buggy_methods = [buggy_lines.split(':')[0] for buggy_lines in bug_info["buggy_lines"]]
        project = bug.split('-')[0]
        # print(project)
        for method, spectra in spectrum.items():
            sbfl_scores[method] = spectra["tarantula"]

        sorted_sbfl_scores = sorted(sbfl_scores.items(), key=lambda x: x[1], reverse=True)
        ranks = {method: rank+1 for rank, (method, _) in enumerate(sorted_sbfl_scores)}
        buggy_methods_ranks = [ranks[buggy_method] for buggy_method in buggy_methods]
        ranking = min(buggy_methods_ranks)

        wef_dict[project].append(ranking)
    return wef_dict

baseline = evaluate_formula()
print(baseline)

wef_dict = evaluate_formula_per_project()
wef_Math = sum(wef_dict['Math']) / len(wef_dict['Math'])
wef_Lang = sum(wef_dict['Lang']) / len(wef_dict['Lang'])
wef_Time = sum(wef_dict['Time']) / len(wef_dict['Time'])
wef_Chart = sum(wef_dict['Chart']) / len(wef_dict['Chart'])

print('Math, Lang, Time, Chart')
print(wef_Math, wef_Lang, wef_Time, wef_Chart)