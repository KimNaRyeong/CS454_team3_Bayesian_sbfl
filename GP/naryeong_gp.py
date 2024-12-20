import os
import json
import random
from tqdm import tqdm


NUM_POPULATIONS = 40
NUM_GENERATIONS = 100
NUM_ELITES = 8
NUM_SAMPLE_BUGS = 50

# NUM_POPULATIONS = 5
# NUM_GENERATIONS = 1
# NUM_ELITES = 2
# NUM_SAMPLE_BUGS = 5
spectrum_with_p_file = '../new_spectrum.json'

with open(spectrum_with_p_file, 'r') as f:
    method_level_spectrum = json.load(f)


class Node:
    def __init__(self, name):
        self.name = name
        self.parent = None
        self.fitness = 0

    def set_parent(self, node):
        self.parent = node

    def evaluate(self, spectra): # comment?
        self.fitness = compute_fitness(self)

class Variable(Node):
    def __init__(self, name):
        super().__init__(name)

    def __str__(self):
        return self.name

    def copy(self):
        return Variable(self.name)

    def get_cut_points(self):
        return [self]

class BinaryOp(Node):
    def __init__(self, name):
        super().__init__(name)
        self.left = None
        self.right = None

    def set_left(self, left):
        self.left = left
        self.left.set_parent(self)

    def set_right(self, right):
        self.right = right
        self.right.set_parent(self)

    def __str__(self):
        return f"({str(self.left)} {self.name} {str(self.right)})"

    def get_cut_points(self):
        return [self] + self.left.get_cut_points() + self.right.get_cut_points()

    def copy(self):
        new_root = get_nonterminal(self.name)
        new_root.set_left(self.left.copy())
        new_root.set_right(self.right.copy())
        return new_root

# Specific binary operations
class PlusOp(BinaryOp):
    def __init__(self):
        super().__init__("+")

class MinusOp(BinaryOp):
    def __init__(self):
        super().__init__("-")

class MultOp(BinaryOp):
    def __init__(self):
        super().__init__("*")

class DivOp(BinaryOp):
    def __init__(self):
        super().__init__("/")

    def __str__(self):
        return f"(1 if {self.right} == 0 else {self.left}/{self.right})"


# Utility functions for creating nodes
def get_nonterminal(op_name=None):
    if op_name:
        return {"+": PlusOp, "-": MinusOp, "*": MultOp, "/": DivOp}[op_name]()
    
    return random.choice([PlusOp(), MinusOp(), MultOp(), DivOp()])

def get_terminal():
    return random.choice([Variable("p"), Variable("e_f"), Variable("e_p"), Variable("n_f"), Variable("n_p"), Variable("1")])

def full_tree(max_height):
    root = get_nonterminal()
    height = 1
    need_children = [root]
    while height < max_height:
        new_parents = []
        for parent in need_children:
            if height == max_height - 1:
                parent.set_left(get_terminal())
                parent.set_right(get_terminal())
            else:
                parent.set_left(get_nonterminal())
                parent.set_right(get_nonterminal())
                new_parents.extend([parent.left, parent.right])
        height += 1
        need_children = new_parents
    return root

def grow_tree(max_height):

    root = get_nonterminal()  # Start with a non-terminal root node.
    height = 1
    need_children = [root]

    while height < max_height:
        new_parents = []
        for parent in need_children:
            if height == max_height - 1 or random.random() < 0.5:
                # Create terminal nodes as children if max height reached or by probability
                parent.set_left(get_terminal())
                parent.set_right(get_terminal())
            else:
                # Create non-terminal nodes
                parent.set_left(get_nonterminal())
                parent.set_right(get_nonterminal())
                new_parents.extend([parent.left, parent.right])
        height += 1
        need_children = new_parents

    return root



def crossover(parents):
    parent1, parent2 = parents

    def select_cut_point(nodes):
        leaf_nodes = [node for node in nodes if isinstance(node, Variable)]
        non_leaf_nodes = [node for node in nodes if not isinstance(node, Variable)]
        if random.random() < 0.2 and leaf_nodes:
            return random.choice(leaf_nodes)
        elif non_leaf_nodes:
            return random.choice(non_leaf_nodes)
        return random.choice(nodes)

    def validate_depth(node, max_depth):
        """Ensure the depth of the resulting trees does not exceed max_depth."""
        def get_depth(n):
            if not isinstance(n, BinaryOp):
                return 1
            return 1 + max(get_depth(n.left), get_depth(n.right))
        return get_depth(node) <= max_depth

    cparent1, cparent2 = parent1.copy(), parent2.copy()
    cut_points1 = cparent1.get_cut_points()
    cut_points2 = cparent2.get_cut_points()
    if not cut_points1 or not cut_points2:
        return cparent1, cparent2

    cut1 = select_cut_point(cut_points1)
    cut2 = select_cut_point(cut_points2)

    # print(str(cut1))
    # print(str(cut2))

    if cut1.parent:
        if cut1.parent.left == cut1:
            cut1.parent.set_left(cut2.copy())
        else:
            cut1.parent.set_right(cut2.copy())

    if cut2.parent:
        if cut2.parent.left == cut2:
            cut2.parent.set_left(cut1.copy())
        else:
            cut2.parent.set_right(cut1.copy())
    
    if validate_depth(cparent1, 4):
        # Ensure depth limit
        if validate_depth(cparent2, 4):
            return cparent1, cparent2
        else:
            return cparent1, mutate(parent2, 0.8)
    else:
        if validate_depth(parent2, 4):
            return mutate(parent1, 0.8), cparent2
        else:
            return mutate(parent1, 0.8), mutate(parent2, 0.8)
    


def mutate(node, p=0.5):
    cnode = node.copy()

    for cut in cnode.get_cut_points():
        if random.random() < p:
            if isinstance(cut, Variable):
                new_node = get_terminal()
            elif isinstance(cut, BinaryOp):
                new_node = get_nonterminal()
                new_node.left = cut.left
                new_node.right = cut.right
            
            if cut.parent:
                if cut.parent.left == cut:
                    cut.parent.left = new_node
                else:
                    cut.parent.right = new_node
    return cnode

def compute_fitness(individual):
    # if individual == None:
    #     print("None....")
    expenses = []
    all_bugs = [file.split('_')[0] for file in os.listdir('../sootDAG_filtered')]
    sample_bugs = random.choices(all_bugs, k=NUM_SAMPLE_BUGS)

    for bug in sample_bugs:
        spectrum = method_level_spectrum[bug]

        with open(f"../bug_data/{bug}.json", 'r') as f:
            bug_info = json.load(f)
        
        sbfl_scores = {}
        buggy_methods = [buggy_lines.split(':')[0] for buggy_lines in bug_info["buggy_lines"]]
        for method, spectra in spectrum.items():
            sbfl_scores[method] = eval(str(individual), {}, spectra)

                
        # print(sbfl_scores)
        sorted_sbfl_scores = sorted(sbfl_scores.items(), key=lambda x: x[1], reverse=True)
        ranks = {method: rank+1 for rank, (method, _) in enumerate(sorted_sbfl_scores)}
        # print(ranks)
        # print(buggy_methods)
        buggy_methods_ranks = [ranks[buggy_method] for buggy_method in buggy_methods]
        ranking = min(buggy_methods_ranks)
        penalty = 10 if ranking != 1 else 0
        expense = (ranking/len(spectrum))*10 + penalty
        expenses.append(expense)
    
    fitness_score = sum(expenses)/len(expenses)

    return fitness_score

        

def genetic_programming():
    populations = []
    for _ in range(NUM_POPULATIONS//2):
        max_height = random.randint(2, 4)
        populations.append(full_tree(max_height))
        populations.append(grow_tree(max_height))
    #     print(max_height)
    # for ind in populations:
    #     print(str(ind))

    for _ in tqdm(range(NUM_GENERATIONS)):
        fitness_scores = [(individual, compute_fitness(individual)) for individual in populations]
        sorted_fitness_scores = sorted(fitness_scores, key=lambda x: x[1])  # Minimize
        elites = [i for i, _ in sorted_fitness_scores[:NUM_ELITES]]
        new_populations = elites[:]

        # for indiv, score in sorted_fitness_scores:
        #         print(str(indiv), score)
        # print('------------------------------')
        # for indiv in elites:
        #     print(str(indiv))

        while len(new_populations) < (NUM_POPULATIONS):
            if random.random() < 0.5:
                mutated = mutate(random.choice(elites))
                new_populations.append(mutated)
            else:
                child1, child2 = crossover(random.choices(elites, k = 2))
                new_populations.append(child1)
                if len(new_populations) < (NUM_POPULATIONS-NUM_ELITES):
                    new_populations.append(child2)
        
        populations = new_populations
        assert len(populations) == NUM_POPULATIONS

    return sorted_fitness_scores

def evaluate_formula(formula):
    acc1 = 0
    wefs = []
    all_bugs = [file.split('_')[0] for file in os.listdir('../sootDAG_filtered')]
    for bug in all_bugs:
        with open(f"../bug_data/{bug}.json", 'r') as f:
            bug_info = json.load(f)
        
        spectrum = method_level_spectrum[bug]
        
        sbfl_scores = {}
        buggy_methods = [buggy_lines.split(':')[0] for buggy_lines in bug_info["buggy_lines"]]
        for method, spectra in spectrum.items():
            sbfl_scores[method] = eval(str(formula), {}, spectra)

            
        sorted_sbfl_scores = sorted(sbfl_scores.items(), key=lambda x: x[1], reverse=True)
        ranks = {method: rank+1 for rank, (method, _) in enumerate(sorted_sbfl_scores)}
        buggy_methods_ranks = [ranks[buggy_method] for buggy_method in buggy_methods]
        ranking = min(buggy_methods_ranks)        
        # print(ranking)

        if ranking == 1:
            acc1 += 1
        wefs.append(ranking)
    
    return acc1, sum(wefs) / len(wefs)

def evaluate_formula_per_project(formula):
    wef_dict = {'Math': [], 'Lang': [], 'Time': [], 'Chart': []}
    for bug, spectrum in method_level_spectrum.items():
        with open(f"./bug_data/{bug}.json", 'r') as f:
            bug_info = json.load(f)

        sbfl_scores = {}
        buggy_methods = [buggy_lines.split(':')[0] for buggy_lines in bug_info["buggy_lines"]]
        project = bug.split('-')[0]
        print(project)
        for method, spectra in spectrum.items():
            sbfl_scores[method] = eval(str(formula), {}, spectra)

        sorted_sbfl_scores = sorted(sbfl_scores.items(), key=lambda x: x[1], reverse=True)
        ranks = {method: rank+1 for rank, (method, _) in enumerate(sorted_sbfl_scores)}
        buggy_methods_ranks = [ranks[buggy_method] for buggy_method in buggy_methods]
        ranking = min(buggy_methods_ranks)

        wef_dict[project].append(ranking)
    return wef_dict


final_formulae = genetic_programming()
for f, s in final_formulae:
    print(str(f), s)
best_formula = str(final_formulae[0][0])

acc1, wef = evaluate_formula(best_formula)

print(acc1, wef)
print(best_formula)


# try1 = "(e_f * (1 if e_p == 0 else e_f/e_p))" # (42, 8.243697478991596)

# baseline = evaluate_formula(try1)
# print(baseline)

# wef_dict = evaluate_formula_per_project(try1)
# wef_Math = sum(wef_dict['Math']) / len(wef_dict['Math'])
# wef_Lang = sum(wef_dict['Lang']) / len(wef_dict['Lang'])
# wef_Time = sum(wef_dict['Time']) / len(wef_dict['Time'])
# wef_Chart = sum(wef_dict['Chart']) / len(wef_dict['Chart'])

# print('Math, Lang, Time, Chart')
# print(wef_Math, wef_Lang, wef_Time, wef_Chart)
