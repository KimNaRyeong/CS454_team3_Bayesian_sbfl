import os
import json
import random
from tqdm import tqdm


NUM_POPULATIONS = 40
NUM_GENERATIONS = 100
NUM_ELITES = 8
NUM_SAMPLE_BUGS = 50
MAX_TREE_DEPTH = 4

spectrum_file = './new_spectrum.json'

with open(spectrum_file, 'r') as f:
    method_level_spectrum = json.load(f)

all_bugs = [file.split('_')[0] for file in os.listdir('sootDAG_filtered')]

class Formula:
    def __init__(self, name, expression):
        self.name = name
        self.expression = expression

# Node Classes
class Node:
    def __init__(self, name):
        self.name = name
        self.parent = None

    def set_parent(self, node):
        self.parent = node

    def evaluate(self, spectra):
        raise NotImplementedError

    def copy(self):
        raise NotImplementedError

    def get_cut_points(self):
        return [self]


class Variable(Node):
    def __str__(self):
        return self.name

    def copy(self):
        return Variable(self.name)


class BinaryOp(Node):
    def __init__(self, name):
        super().__init__(name)
        self.left = None
        self.right = None

    def set_left(self, node):
        self.left = node
        self.left.set_parent(self)

    def set_right(self, node):
        self.right = node
        self.right.set_parent(self)

    def __str__(self):
        return f"({self.left} {self.name} {self.right})"

    def copy(self):
        new_node = get_nonterminal(self.name)
        new_node.set_left(self.left.copy())
        new_node.set_right(self.right.copy())
        return new_node

    def get_cut_points(self):
        return [self] + self.left.get_cut_points() + self.right.get_cut_points()


class PlusOp(BinaryOp):
    def __init__(self):
        super().__init__('+')


class MinusOp(BinaryOp):
    def __init__(self):
        super().__init__('-')


class MultOp(BinaryOp):
    def __init__(self):
        super().__init__('*')


class DivOp(BinaryOp):
    def __init__(self):
        super().__init__('/')

    def __str__(self):
        return f"(1 if {self.right} == 0 else {self.left} / {self.right})"

class UnaryOp(Node):
    def __init__(self, name):
        super().__init__(name)
        self.operand = None

    def set_operand(self, node):
        self.operand = node
        self.operand.set_parent(self)

    def __str__(self):
        return f"{self.name}({self.operand})"

    def copy(self):
        new_node = get_nonterminal(self.name)
        new_node.set_operand(self.operand.copy())
        return new_node

    def get_cut_points(self):
        return [self] + self.operand.get_cut_points()


class SquareOp(UnaryOp):
    def __init__(self):
        super().__init__('**2')

    def __str__(self):
        return f"({self.operand} ** 2)" 


class SqrtOp(UnaryOp):
    def __init__(self):
        super().__init__('sqrt')

    def __str__(self):
        return f"(1 if {self.operand} < 0 else sqrt({self.operand}))"

def get_depth(node):
    if not isinstance(node, BinaryOp):
        return 1
    return 1 + max(get_depth(node.left), get_depth(node.right))

def mutate_node(target):
        if isinstance(target, Variable):
            return get_terminal()
        elif isinstance(target, BinaryOp):
            new_node = get_nonterminal(target.name)
            new_node.set_left(target.left.copy() if target.left else None)
            new_node.set_right(target.right.copy() if target.right else None)
            return new_node
        elif isinstance(target, UnaryOp):
            new_node = get_unary(target.name)
            new_node.set_operand(target.operand.copy() if target.operand else None)
            return new_node
        return target

def select_cut_point(nodes):
        leaf_nodes = [node for node in nodes if isinstance(node, Variable)]
        non_leaf_nodes = [node for node in nodes if not isinstance(node, Variable)]

        if random.random() < 0.2 and leaf_nodes:
            return random.choice(leaf_nodes)
        elif non_leaf_nodes:
            return random.choice(non_leaf_nodes)
        return random.choice(nodes)


def get_nonterminal(op_name=None):
    ops = {'+': PlusOp, '-': MinusOp, '*': MultOp, '/': DivOp}
    return ops[op_name]() if op_name else random.choice([PlusOp(), MinusOp(), MultOp(), DivOp()])


def get_terminal():
    return random.choice([Variable("e_f"), Variable("e_p"), Variable("n_f"), Variable("n_p"), Variable("p"), Variable("1"), Variable("0.7")])

def get_unary(op_name=None):
    ops = {'**': SquareOp, 'sqrt': SqrtOp}
    return ops[op_name]() if op_name else random.choice([SquareOp(), SqrtOp()])

def generate_tree(max_height, full=False):
    def create_node(current_height):
        if current_height == max_height or (not full and random.random() < 0.5):
            return get_terminal()
        else:
            node = get_nonterminal()
            node.set_left(create_node(current_height + 1))
            node.set_right(create_node(current_height + 1))
            return node

    return create_node(1)


def crossover(parents):
    parent1, parent2 = parents

    cut_points1 = parent1.get_cut_points()
    cut_points2 = parent2.get_cut_points()

    if not cut_points1 or not cut_points2:
        return parent1.copy(), parent2.copy()

    cut1 = select_cut_point(cut_points1)
    cut2 = select_cut_point(cut_points2)

    if cut1.parent:
        if get_depth(cut2) <= MAX_TREE_DEPTH:
            if cut1.parent.left == cut1:
                cut1.parent.set_left(cut2.copy())
            else:
                cut1.parent.set_right(cut2.copy())

    if cut2.parent:
        if get_depth(cut1) <= MAX_TREE_DEPTH:
            if cut2.parent.left == cut2:
                cut2.parent.set_left(cut1.copy())
            else:
                cut2.parent.set_right(cut1.copy())

    return parent1, parent2


def mutate(node, p=0.08):
    for cut in node.get_cut_points():
        if random.random() < p:
            if cut.parent:
                mutated_subtree = mutate_node(cut)
                if get_depth(mutated_subtree) <= MAX_TREE_DEPTH:
                    if cut.parent.left == cut:
                        cut.parent.set_left(mutated_subtree)
                    else:
                        cut.parent.set_right(mutated_subtree)

    return node.copy()


def compute_fitness(individual):
    # if individual == None:
    #     print("None....")
    expenses = []
    sample_bugs = random.choices(all_bugs, k=NUM_SAMPLE_BUGS)

    for bug in sample_bugs:
        spectrum = method_level_spectrum[bug]

        with open(f"./bug_data/{bug}.json", 'r') as f:
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
    ef = Variable("e_f")
    nf = Variable("n_f")
    ep = Variable("e_p")
    np = Variable("n_p")
    p = Variable("p")

    plus1 = PlusOp()
    plus1.set_left(ef)
    plus1.set_right(nf)

    div1 = DivOp()
    div1.set_left(ef)
    div1.set_right(plus1)

    plus2 = PlusOp()
    plus2.set_left(ep)
    plus2.set_right(np)

    div2 = DivOp()
    div2.set_left(ep)
    div2.set_right(plus2)

    div3 = DivOp()
    div3.set_left(ef)
    div3.set_right(plus1)

    plus3 = PlusOp()
    plus3.set_left(div2)
    plus3.set_right(div3)

    final_div = DivOp()
    final_div.set_left(div1)
    final_div.set_right(plus3)

    leo = MinusOp()
    leo.set_left(Variable("1"))
    leo.set_right(p)

    populations = [final_div, ep, np, nf, p, leo]
    populations += [generate_tree(MAX_TREE_DEPTH, full=(i < NUM_POPULATIONS // 2)) 
                 for i in range(NUM_POPULATIONS - len(populations))]

    for _ in tqdm(range(NUM_GENERATIONS)):
        fitness_scores = [(ind, compute_fitness(ind)) for ind in populations]
        fitness_scores.sort(key=lambda x: x[1])

        elites = [ind for ind, _ in fitness_scores[:NUM_ELITES]]
        new_populations = elites[:]

        while len(new_populations) < NUM_POPULATIONS:
            if random.random() < 0.5:
                new_populations.append(mutate(random.choice(elites)))
            else:
                new_populations.extend(crossover(random.sample(elites, 2)))

        populations = new_populations[:NUM_POPULATIONS]
        final_formula, best_score = min(fitness_scores, key=lambda x: x[1])
        print(f"Best Formula: {final_formula}, Fitness: {best_score}")
        acc1, wef = evaluate_formula(final_formula)
        print(f"Accuracy@1: {acc1}, Wasted Effort: {wef}")

    return min(fitness_scores, key=lambda x: x[1])

def evaluate_formula(formula):
    acc1 = 0
    wefs = []

    for bug, spectrum in method_level_spectrum.items():
        with open(f"./bug_data/{bug}.json", 'r') as f:
            bug_info = json.load(f)
        
        sbfl_scores = {}
        buggy_methods = [buggy_lines.split(':')[0] for buggy_lines in bug_info["buggy_lines"]]
        for method, spectra in spectrum.items():
            try:
                sbfl_scores[method] = eval(str(formula), {}, spectra)
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
        wefs.append(ranking)
    
    return acc1, sum(wefs) / len(wefs)



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
