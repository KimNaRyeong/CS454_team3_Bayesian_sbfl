import os, json
import math

def safe_divide(a, b):
    return a / b if b != 0 else 0

def evaluate_formula(formula):
    method_level_spectrum_with_p_file = './new_spectrum.json'
    with open(method_level_spectrum_with_p_file, 'r') as f:
        spectrum_with_p = json.load(f)
    
    acc1 = 0
    acc3 = 0
    acc5 = 0
    acc10 = 0
    wefs = []

    all_bugs = [file.split('_')[0] for file in os.listdir('sootDAG_filtered')]
    for bug in all_bugs:
        with open(f"./bug_data/{bug}.json", 'r') as f:
            bug_info = json.load(f)
        
        spectrum = spectrum_with_p[bug]
        sbfl_scores = {}
        buggy_methods = [buggy_lines.split(':')[0] for buggy_lines in bug_info["buggy_lines"]]
        for method, spectra in spectrum.items():
            sbfl_scores[method] = eval(str(formula), {"safe_divide": safe_divide, "math": math}, spectra)

            
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
    method_level_spectrum_with_p_file = './new_spectrum.json'

    
    with open(method_level_spectrum_with_p_file, 'r') as f:
        spectrum_with_p = json.load(f)


    
    acc1 = 0
    acc3 = 0
    acc5 = 0
    acc10 = 0
    wefs = []

    all_bugs = [file.split('_')[0] for file in os.listdir('sootDAG_filtered')]
    for bug in all_bugs:
        with open(f"./bug_data/{bug}.json", 'r') as f:
            bug_info = json.load(f)
        
        spectrum = spectrum_with_p[bug]
        weighted_sbfl_scores = {}
        buggy_methods = [buggy_lines.split(':')[0] for buggy_lines in bug_info["buggy_lines"]]
        for method, spectra in spectrum.items():
            sbfl_score = eval(str(formula), {"safe_divide": safe_divide, "math": math}, spectra)
            weight = spectra["p"]
            weighted_sbfl_scores[method] = sbfl_score*(1-weight*0.7)

            
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
naryeong = "(1 if e_f==0 else (n_p*e_f)/e_f)"
sunwoo = "(safe_divide(math.sqrt(0.95 * 0.0 if (e_p + n_p) == 0 else safe_divide(e_p, (e_p + n_p))), (p + math.sqrt(0.0 if (e_p + n_p) == 0 else safe_divide(e_p, (e_p + n_p))))) * safe_divide((0.0 if (e_f + n_f) == 0 else safe_divide(e_f, (e_f + n_f)) * (0.0 if (e_f + n_f) == 0 else safe_divide(e_f, (e_f + n_f)) + 0.21)), 0.0 if (e_p + n_p) == 0 else safe_divide(e_p, (e_p + n_p))))"
donghan = "(1 if 1 == 0 else ((1 if e_f == 0 else safe_divide(n_p * e_f, e_f)) * n_p) / 1) - ((n_f + e_p) + e_f)"
jihun = "(safe_divide(n_f, e_p) * safe_divide((e_p * e_f), e_p)) * e_f"

trantula_acc1, trantula_acc3, trantula_acc5, trantula_acc10, trantula_wef = evaluate_formula(trantula)
ochiai_acc1, ochiai_acc3, ochiai_acc5, ochiai_acc10, ochiai_wef = evaluate_formula(ochiai)
jaccard_acc1, jaccard_acc3, jaccard_acc5, jaccard_acc10, jaccard_wef = evaluate_formula(jaccard)
naryeong_acc1, naryeong_acc3, naryeong_acc5, naryeong_acc10, naryeong_wef = evaluate_formula(naryeong)
sunwoo_acc1, sunwoo_acc3, sunwoo_acc5, sunwoo_acc10, sunwoo_wef = evaluate_formula(sunwoo)
donghan_acc1, donghan_acc3, donghan_acc5, donghan_acc10, donghan_wef = evaluate_formula(donghan)
jihun_acc1, jihun_acc3, jihun_acc5, jihun_acc10, jihun_wef = evaluate_formula(jihun)

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
print("jihun")
print(jihun_acc1, jihun_acc3, jihun_acc5, jihun_acc10, jihun_wef)
print("-----------------Our Approach--------------------------------------")

weighted_trantula_acc1, weighted_trantula_acc3, weighted_trantula_acc5, weighted_trantula_acc10, weighted_trantula_wef = evaluate_weighted_formula(trantula)
weighted_ochiai_acc1, weighted_ochiai_acc3, weighted_ochiai_acc5, weighted_ochiai_acc10, weighted_ochiai_wef = evaluate_weighted_formula(ochiai)
weighted_jaccard_acc1, weighted_jaccard_acc3, weighted_jaccard_acc5, weighted_jaccard_acc10, weighted_jaccard_wef = evaluate_weighted_formula(jaccard)
weighted_naryeong_acc1, weighted_naryeong_acc3, weighted_naryeong_acc5, weighted_naryeong_acc10, weighted_naryeong_wef = evaluate_weighted_formula(naryeong)
weighted_sunwoo_acc1, weighted_sunwoo_acc3, weighted_sunwoo_acc5, weighted_sunwoo_acc10, weighted_sunwoo_wef = evaluate_weighted_formula(sunwoo)
weighted_donghan_acc1, weighted_donghan_acc3, weighted_donghan_acc5, weighted_donghan_acc10, weighted_donghan_wef = evaluate_weighted_formula(donghan)
weighted_jihun_acc1, weighted_jihun_acc3, weighted_jihun_acc5, weighted_jihun_acc10, weighted_jihun_wef = evaluate_weighted_formula(jihun)
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
print("jihun")
print(weighted_jihun_acc1, weighted_jihun_acc3, weighted_jihun_acc5, weighted_jihun_acc10, weighted_jihun_wef)


bayesian_nr = "(1 if e_f == 0 else ((n_p * p) + e_f)/e_f)"
bayesian_sw = "((math.sqrt((0.0 if (e_f + n_f) == 0 else safe_divide(e_f, (e_f + n_f)) + p)) - ((0.0 if (e_p + n_p) == 0 else safe_divide(e_p, (e_p + n_p)) + p) + math.sqrt(0.0 if (e_p + n_p) == 0 else safe_divide(e_p, (e_p + n_p))))) + ((0.82 - (0.76 * p)) * 0.0 if (e_f + n_f) == 0 else safe_divide(e_f, (e_f + n_f))))"
bayesian_dh = "((((e_f + ((n_f + 0.7) * e_f)) + n_p) * e_f) + (((1 + n_p) + e_f) + (((1 + n_p) * e_f) - (1 * p))))"
bayesian_jh = "((safe_divide(e_f, (safe_divide((e_f * (e_p + safe_divide(e_p, (n_f * p)))), p) + safe_divide(e_f, e_p))) + safe_divide(e_p, n_p)) * safe_divide(e_f, e_p))"

bnr_acc1, bnr_acc3, bnr_acc5, bnr_acc10, bnr_wef = evaluate_formula(bayesian_nr)
bsw_acc1, bsw_acc3, bsw_acc5, bsw_acc10, bsw_wef = evaluate_formula(bayesian_sw)
bdh_acc1, bdh_acc3, bdh_acc5, bdh_acc10, bdh_wef = evaluate_formula(bayesian_dh)
bjh_acc1, bjh_acc3, bjh_acc5, bjh_acc10, bjh_wef = evaluate_formula(bayesian_jh)

print("----------------------------------GP version-----------------------------------------")
# print(bnr_acc1, bnr_acc3, bnr_acc5, bnr_acc10, bnr_wef)
print("Sunwoo")
print(bsw_acc1, bsw_acc3, bsw_acc5, bsw_acc10, bsw_wef)
# print(bdh_acc1, bdh_acc3, bdh_acc5, bdh_acc10, bdh_wef)
print("jihun")
print(bjh_acc1, bjh_acc3, bjh_acc5, bjh_acc10, bjh_wef)

