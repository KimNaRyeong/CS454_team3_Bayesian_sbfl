import os, json
import math

def safe_divide(a, b):
    return a / b if b != 0 else 0

def evaluate_formula(formula):
    method_level_spectrum_file = './method_level_spectrums.json'
    with open(method_level_spectrum_file, 'r') as f:
        method_level_spectrum = json.load(f)
    
    acc1 = 0
    acc3 = 0
    acc5 = 0
    acc10 = 0
    wefs = []

    all_bugs = [file.split('_')[0] for file in os.listdir('sootDAG_filtered')]
    for bug in all_bugs:
        with open(f"./bug_data/{bug}.json", 'r') as f:
            bug_info = json.load(f)
        
        spectrum = method_level_spectrum[bug]
        sbfl_scores = {}
        buggy_methods = [buggy_lines.split(':')[0] for buggy_lines in bug_info["buggy_lines"]]
        for method, spectra in spectrum.items():
            try:
                sbfl_scores[method] = eval(str(formula), {"safe_divide": safe_divide, "math": math}, spectra)
            except:
                print(str(formula))
                print("wrong")

            
        sorted_sbfl_scores = sorted(sbfl_scores.items(), key=lambda x: x[1], reverse=True)
        ranks = {method: rank+1 for rank, (method, _) in enumerate(sorted_sbfl_scores)}
        buggy_methods_ranks = [ranks[buggy_method] for buggy_method in buggy_methods]
        ranking = min(buggy_methods_ranks)        
        # print(ranking)

        if ranking == 1:
            acc1 += 1
            acc3 += 1
            acc5 += 1
            acc10 += 1
        elif ranking <= 3:
            acc3 += 1
            acc5 += 1
            acc10 += 1
        elif ranking <= 5:
            acc5 += 1
            acc10 += 1
        elif ranking <= 10:
            acc10 += 1
        wefs.append(ranking)
    
    return acc1, acc3, acc5, acc10, sum(wefs) / len(wefs)

def evaluate_weighted_formula(formula):
    # method_level_spectrum_file = './method_level_spectrums.json'
    method_level_spectrum_file = './new_spectrum.json'
    weight_file = './metric_value_json_output/bayesian.json'

    with open(method_level_spectrum_file, 'r') as f:
        method_level_spectrum = json.load(f)
    with open(weight_file, 'r') as f:
        weights = json.load(f)

    
    acc1 = 0
    acc3 = 0
    acc5 = 0
    acc10 = 0
    wefs = []

    all_bugs = [file.split('_')[0] for file in os.listdir('sootDAG_filtered')]
    for bug in all_bugs:
        with open(f"./bug_data/{bug}.json", 'r') as f:
            bug_info = json.load(f)
        
        spectrum = method_level_spectrum[bug]
        weight_for_bug = weights[bug]
        weighted_sbfl_scores = {}
        buggy_methods = [buggy_lines.split(':')[0] for buggy_lines in bug_info["buggy_lines"]]
        for method, spectra in spectrum.items():
            try:
                sbfl_score = eval(str(formula), {"safe_divide": safe_divide, "math": math}, spectra)
                try:
                    weight = weight_for_bug[method]
                except:
                    weight = 0.3
                # weighted_sbfl_scores[method] = sbfl_score*weight
                weighted_sbfl_scores[method] = sbfl_score
            except:
                print(str(formula))
                print("wrong")

            
        sorted_sbfl_scores = sorted(weighted_sbfl_scores.items(), key=lambda x: x[1], reverse=True)
        ranks = {method: rank+1 for rank, (method, _) in enumerate(sorted_sbfl_scores)}
        buggy_methods_ranks = [ranks[buggy_method] for buggy_method in buggy_methods]
        ranking = min(buggy_methods_ranks)        
        # print(ranking)

        if ranking == 1:
            acc1 += 1
            acc3 += 1
            acc5 += 1
            acc10 += 1
        elif ranking <= 3:
            acc3 += 1
            acc5 += 1
            acc10 += 1
        elif ranking <= 5:
            acc5 += 1
            acc10 += 1
        elif ranking <= 10:
            acc10 += 1
        wefs.append(ranking)
    
    return acc1, acc3, acc5, acc10, sum(wefs) / len(wefs)


trantula = "safe_divide(safe_divide(e_f, (e_f+n_f)), (safe_divide(e_f, (e_f+n_f))+safe_divide(e_p, (e_p+n_p))))"
ochiai = "safe_divide(e_f, ((e_f+e_p)*(e_f+n_f)))"
jaccard = "safe_divide(e_f, (e_f+e_p+n_f))"
naryeong = "(e_f * (1 if e_p == 0 else e_f/e_p))"
sunwoo = "math.sqrt(safe_divide(math.sqrt(math.sqrt(0.0 if (e_f + n_f) == 0 else safe_divide(e_f, (e_f + n_f)))) , (1.0 + math.sqrt(0.0 if (e_p + n_p) == 0 else safe_divide(e_p, (e_p + n_p))))))"
donghan = "(1 if 1 == 0 else ((1 if e_f == 0 else safe_divide(n_p * e_f, e_f)) * n_p) / 1) - ((n_f + e_p) + e_f)"

trantula_acc1, trantula_acc3, trantula_acc5, trantula_acc10, trantula_wef = evaluate_formula(trantula)
ochiai_acc1, ochiai_acc3, ochiai_acc5, ochiai_acc10, ochiai_wef = evaluate_formula(ochiai)
jaccard_acc1, jaccard_acc3, jaccard_acc5, jaccard_acc10, jaccard_wef = evaluate_formula(jaccard)
naryeong_acc1, naryeong_acc3, naryeong_acc5, naryeong_acc10, naryeong_wef = evaluate_formula(naryeong)
sunwoo_acc1, sunwoo_acc3, sunwoo_acc5, sunwoo_acc10, sunwoo_wef = evaluate_formula(sunwoo)
donghan_acc1, donghan_acc3, donghan_acc5, donghan_acc10, donghan_wef = evaluate_formula(donghan)

print(f"Total bugs: {len(os.listdir('sootDAG_filtered'))}")
print("acc@1, acc@3, acc@5, acc@10, wef")
print("--------------------------------------baseline----------------------------------------------")
print("trantula")
print(trantula_acc1, trantula_acc3, trantula_acc5, trantula_acc10, trantula_wef)
print("ochiai")
print(ochiai_acc1, ochiai_acc3, ochiai_acc5, ochiai_acc10, ochiai_wef)
print("jaccard")
print(jaccard_acc1, jaccard_acc3, jaccard_acc5, jaccard_acc10, jaccard_wef)
print("naryeong")
print(naryeong_acc1, naryeong_acc3, naryeong_acc5, naryeong_acc10, naryeong_wef)
print("sunwoo")
print(sunwoo_acc1, sunwoo_acc3, sunwoo_acc5, sunwoo_acc10, sunwoo_wef)
print("donghan")
print(donghan_acc1, donghan_acc3, donghan_acc5, donghan_acc10, donghan_wef)
print("-----------------Our Approach--------------------------------------")

trantula = "safe_divide(safe_divide(e_f, (e_f+n_f)), (safe_divide(e_f, (e_f+n_f))+safe_divide(e_p, (e_p+n_p))))"
ochiai = "safe_divide(e_f, ((e_f+e_p)*(e_f+n_f)))"
jaccard = "safe_divide(e_f, (e_f+e_p+n_f))"
naryeong = "(e_f * (1 if e_p == 0 else e_f/e_p))"
sunwoo = "math.sqrt(safe_divide(math.sqrt(math.sqrt(0.0 if (e_f + n_f) == 0 else safe_divide(e_f, (e_f + n_f)))) , (1.0 + math.sqrt(0.0 if (e_p + n_p) == 0 else safe_divide(e_p, (e_p + n_p))))))"
donghan = "((((e_f + ((n_f + 0.7) * e_f)) + n_p) * e_f) + (((1 + n_p) + e_f) + (((1 + n_p) * e_f) - (1 * p))))"

weighted_trantula_acc1, weighted_trantula_acc3, weighted_trantula_acc5, weighted_trantula_acc10, weighted_trantula_wef = evaluate_weighted_formula(trantula)
weighted_ochiai_acc1, weighted_ochiai_acc3, weighted_ochiai_acc5, weighted_ochiai_acc10, weighted_ochiai_wef = evaluate_weighted_formula(ochiai)
weighted_jaccard_acc1, weighted_jaccard_acc3, weighted_jaccard_acc5, weighted_jaccard_acc10, weighted_jaccard_wef = evaluate_weighted_formula(jaccard)
weighted_naryeong_acc1, weighted_naryeong_acc3, weighted_naryeong_acc5, weighted_naryeong_acc10, weighted_naryeong_wef = evaluate_weighted_formula(naryeong)
weighted_sunwoo_acc1, weighted_sunwoo_acc3, weighted_sunwoo_acc5, weighted_sunwoo_acc10, weighted_sunwoo_wef = evaluate_weighted_formula(sunwoo)
weighted_donghan_acc1, weighted_donghan_acc3, weighted_donghan_acc5, weighted_donghan_acc10, weighted_donghan_wef = evaluate_weighted_formula(donghan)
print("trantula")
print(weighted_trantula_acc1, weighted_trantula_acc3, weighted_trantula_acc5, weighted_trantula_acc10, weighted_trantula_wef)
print("ochiai")
print(weighted_ochiai_acc1, weighted_ochiai_acc3, weighted_ochiai_acc5, weighted_ochiai_acc10, weighted_ochiai_wef)
print("jaccard")
print(weighted_jaccard_acc1, weighted_jaccard_acc3, weighted_jaccard_acc5, weighted_jaccard_acc10, weighted_jaccard_wef)
print("naryeong")
print(weighted_naryeong_acc1, weighted_naryeong_acc3, weighted_naryeong_acc5, weighted_naryeong_acc10, weighted_naryeong_wef)
print("sunsoo")
print(weighted_sunwoo_acc1, weighted_sunwoo_acc3, weighted_sunwoo_acc5, weighted_sunwoo_acc10, weighted_sunwoo_wef)
print("donghan")
print(weighted_donghan_acc1, weighted_donghan_acc3, weighted_donghan_acc5, weighted_donghan_acc10, weighted_donghan_wef)