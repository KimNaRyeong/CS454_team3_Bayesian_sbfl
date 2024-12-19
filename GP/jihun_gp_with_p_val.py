import os
import json
import numpy as np
import random
import copy
import math

class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

def safe_div(x, y):
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    out = np.ones_like(x, dtype=float)
    mask = (y != 0)
    out[mask] = x[mask] / y[mask]
    return out

def generate_random_tree(depth):
    if depth == 0 or (depth > 0 and random.random() < 0.4):
        # p를 포함한 터미널 노드
        terminals = ["ep", "ef", "np", "nf", "p", str(random.randint(1, 10))]
        return Node(random.choice(terminals))
    else:
        operators = ["+", "-", "*", "/"]
        left = generate_random_tree(depth - 1)
        right = generate_random_tree(depth - 1)
        return Node(random.choice(operators), left, right)

def random_node(node):
    nodes = []
    def traverse(current_node):
        nodes.append(current_node)
        if current_node.left:
            traverse(current_node.left)
        if current_node.right:
            traverse(current_node.right)
    traverse(node)
    return random.choice(nodes)

def evaluate_formula(tree, ep, ef, np_, nf, p):
    """Evaluate formula tree vectorized over methods."""
    ep = np.array(ep, dtype=float)
    ef = np.array(ef, dtype=float)
    np_ = np.array(np_, dtype=float)
    nf = np.array(nf, dtype=float)
    p = np.array(p, dtype=float)

    def eval_node(node, ep, ef, np_, nf, p):
        if node.left is None and node.right is None:
            if node.value == "ep":
                return ep
            elif node.value == "ef":
                return ef
            elif node.value == "np":
                return np_
            elif node.value == "nf":
                return nf
            elif node.value == "p":
                return p
            else:
                return float(node.value)*np.ones_like(ep)
        else:
            left = eval_node(node.left, ep, ef, np_, nf, p)
            right = eval_node(node.right, ep, ef, np_, nf, p)
            if node.value == "+":
                return left + right
            elif node.value == "-":
                return left - right
            elif node.value == "*":
                return left * right
            elif node.value == "/":
                return safe_div(left, right)

    return eval_node(tree, ep, ef, np_, nf, p)

def mutate(node, mutation_rate=0.1):
    if random.random() < mutation_rate:
        return generate_random_tree(depth=2)
    else:
        if node.left:
            node.left = mutate(node.left, mutation_rate)
        if node.right:
            node.right = mutate(node.right, mutation_rate)
        return node

def crossover(parent1, parent2):
    child1 = copy.deepcopy(parent1)
    child2 = copy.deepcopy(parent2)

    node1 = random_node(child1)
    node2 = random_node(child2)

    node1.value, node2.value = node2.value, node1.value
    node1.left, node2.left = node2.left, node1.left
    node1.right, node2.right = node2.right, node1.right

    return child1

def tournament_selection(population, fitnesses, tournament_size=3):
    participants = random.sample(list(zip(population, fitnesses)), tournament_size)
    participants.sort(key=lambda x: x[1])
    return participants[0][0]

def tree_to_formula(node):
    if node.left is None and node.right is None:
        return node.value
    else:
        left_str = tree_to_formula(node.left)
        right_str = tree_to_formula(node.right)
        return f'({left_str} {node.value} {right_str})'

def load_bug_info(bug_id, data_dir="./bug_data"):
    bug_info_path = os.path.join(data_dir, f"{bug_id}.json")
    with open(bug_info_path, "r") as f:
        bug_info = json.load(f)
    return bug_info

def run_gp(training_data, generations=200, population_size=50, elitism_rate=0.2):
    population = [generate_random_tree(depth=4) for _ in range(population_size)]
    best_individual = None
    best_fitness_ever = math.inf

    for generation in range(generations):
        fitness_scores = []
        for individual in population:
            total_fitness = 0
            for data in training_data:
                try:
                    scores = evaluate_formula(
                        individual,
                        data['e_p'],
                        data['e_f'],
                        data['n_p'],
                        data['n_f'],
                        data['p']
                    )

                    methods = data['methods']
                    sbfl_scores = list(zip(methods, scores))
                    sbfl_scores.sort(key=lambda x: x[1], reverse=True)

                    ranks = {m: i+1 for i, (m, _) in enumerate(sbfl_scores)}
                    buggy_ranks = [ranks[m] for m in data['buggy_methods'] if m in ranks]

                    if buggy_ranks:
                        fitness = min(buggy_ranks)
                    else:
                        fitness = len(methods) + 1
                    total_fitness += fitness
                except Exception:
                    total_fitness += len(data['methods']) + 1

            avg_fitness = total_fitness / len(training_data)
            fitness_scores.append(avg_fitness)

        best_fitness = min(fitness_scores)
        if best_fitness < best_fitness_ever:
            best_fitness_ever = best_fitness
            best_index = fitness_scores.index(best_fitness)
            best_individual = copy.deepcopy(population[best_index])

        # print(f"Generation {generation + 1}/{generations}: Best Fitness: {best_fitness}, Best Ever: {best_fitness_ever}")

        # Elitism
        elite_size = int(population_size * elitism_rate)
        sorted_pop = [p for p, f in sorted(zip(population, fitness_scores), key=lambda x: x[1])]
        new_population = sorted_pop[:elite_size]

        while len(new_population) < population_size:
            parent1 = tournament_selection(population, fitness_scores)
            parent2 = tournament_selection(population, fitness_scores)
            child = crossover(parent1, parent2)
            child = mutate(child, mutation_rate=0.1)
            new_population.append(child)

        population = new_population

    return best_individual


def evaluate_on_all_bugs(best_formula_tree, training_data):
    total_acc1 = 0
    total_wef = 0
    project_results = {}

    for data in training_data:
        methods = data['methods']
        e_p = data['e_p']
        e_f = data['e_f']
        n_p = data['n_p']
        n_f = data['n_f']
        p = data['p']
        buggy_methods = data['buggy_methods']
        bug_id = data['bug_id']

        scores = evaluate_formula(best_formula_tree, e_p, e_f, n_p, n_f, p)
        sbfl_scores = list(zip(methods, scores))
        sbfl_scores.sort(key=lambda x: x[1], reverse=True)
        ranks = {m: i+1 for i, (m, _) in enumerate(sbfl_scores)}
        buggy_ranks = [ranks[m] for m in buggy_methods if m in ranks]

        if buggy_ranks:
            rank = min(buggy_ranks)
            total_wef += rank
            acc1 = 1 if rank == 1 else 0
            total_acc1 += acc1

            project_name = bug_id.split('-')[0]
            if project_name not in project_results:
                project_results[project_name] = {'acc1': 0, 'wef': 0, 'bugs': 0}
            project_results[project_name]['acc1'] += acc1
            project_results[project_name]['wef'] += rank
            project_results[project_name]['bugs'] += 1
        else:
            total_wef += len(methods)

    return total_acc1, total_wef, project_results

def report_results(best_formula_str, overall_acc1, overall_wef, project_results):
    print(f"Best Formula: {best_formula_str}")
    print(f"Overall acc@1: {overall_acc1}")
    print(f"Overall Wasted Effort (WEF): {overall_wef}")
    print("Per-project results:")
    for project, data in project_results.items():
        print(f"{project}: acc@1 = {data['acc1']}, WEF = {data['wef']}")


if __name__ == "__main__":
    # new_spectrum.json 로드
    with open("new_spectrum.json", "r") as f:
        method_level_spectrum = json.load(f)

    data_dir = "./bug_data"
    bug_ids = list(method_level_spectrum.keys())

    training_data = []
    for bug_id in bug_ids:
        bug_info = load_bug_info(bug_id, data_dir=data_dir)
        spectrum = method_level_spectrum[bug_id]
        methods = list(spectrum.keys())

        e_p = [spectrum[m]['e_p'] for m in methods]
        n_p = [spectrum[m]['n_p'] for m in methods]
        e_f = [spectrum[m]['e_f'] for m in methods]
        n_f = [spectrum[m]['n_f'] for m in methods]
        p = [spectrum[m]['p'] for m in methods]  # p값 추가

        buggy_methods = [bl.split(':')[0] for bl in bug_info['buggy_lines']]

        training_data.append({
            'bug_id': bug_id,
            'methods': methods,
            'e_p': e_p,
            'n_p': n_p,
            'e_f': e_f,
            'n_f': n_f,
            'p': p,
            'buggy_methods': buggy_methods
        })

    # GP 실행
    best_formula_tree = run_gp(training_data, generations=100, population_size=40)

    best_formula_str = tree_to_formula(best_formula_tree)
    print(f"Best Evolved Formula: {best_formula_str}")

    # with open('best.py', 'w') as f:
    #     f.write("def sbfl(ep, ef, np, nf, p):\n")
    #     f.write(f"    suspiciousness = {best_formula_str}\n")
    #     f.write("    return suspiciousness\n")

    # 모든 버그에 대한 평가
    overall_acc1, overall_wef, project_results = evaluate_on_all_bugs(best_formula_tree, training_data)
    report_results(best_formula_str, overall_acc1, overall_wef, project_results)