import os
import json
import pandas as pd
import numpy as np
import random
import math
import warnings
from sklearn.model_selection import KFold

warnings.filterwarnings("ignore")

# 터미널과 연산자를 정의합니다.
TERMINALS = ['x', 'y', 'p']  # x, y, p, const
FUNCTIONS = ['add', 'sub', 'mul', 'div', 'sqrt']  # 제한된 연산자

# 트리의 최대 깊이를 정의합니다.
MAX_DEPTH = 4  # 트리의 최대 깊이

POPULATION_SIZE = 100
NUM_GENERATIONS = 50
TOURNAMENT_SIZE = 2
MUTATION_RATE = 0.1
CROSSOVER_RATE = 0.7
ELITISM = True

K_FOLDS = 20

# new_spectrum.json 파일 로드
# 구조 예시:
# {
#   "Chart-1": {
#       "org.jfree.chart$ChartColor#<clinit>()": {
#           "e_p": 300,
#           "n_p": 1013,
#           "e_f": 1,
#           "n_f": 0,
#           "p": 1.0
#       },
#       ...
#   },
#   ...
# }
with open("new_spectrum.json", "r") as f:
    SPECTRUM_DATA = json.load(f)


def get_all_bug_ids():
    # new_spectrum.json 의 key들이 bug_id 목록
    return list(SPECTRUM_DATA.keys())


def load_bug_info(bug_id):
    bug_info_path = os.path.join(f"./bug_data/{bug_id}.json")
    if not os.path.exists(bug_info_path):
        raise FileNotFoundError(f"Bug info file missing for {bug_id}")

    with open(bug_info_path, "r") as f:
        bug_info = json.load(f)
    return bug_info


def get_labels(method_names, bug_info):
    # bug_info에서 buggy_lines (or buggy_methods) 를 로드
    buggy_methods = bug_info.get("buggy_lines", [])
    parsed_buggy_methods = set([buggy_method.split(":")[0] for buggy_method in buggy_methods])
    # print(f"parsed = {parsed_buggy_methods}")
    # method_names 리스트와 비교
    labels = np.array([1 if m in parsed_buggy_methods else 0 for m in method_names])
    return labels


class Node:
    def __init__(self, value, children=[]):
        self.value = value  # 연산자 또는 터미널 값 또는 상수
        self.children = children  # 하위 노드 리스트

    def evaluate(self, context):
        """현재 노드를 평가합니다."""
        try:
            if self.value == 'x':
                return context['x']
            elif self.value == 'y':
                return context['y']
            elif self.value == 'p':
                return context['p']
            elif isinstance(self.value, float):  # 상수인 경우
                return self.value
            elif self.value == 'add':
                return self.children[0].evaluate(context) + self.children[1].evaluate(context)
            elif self.value == 'sub':
                return self.children[0].evaluate(context) - self.children[1].evaluate(context)
            elif self.value == 'mul':
                return self.children[0].evaluate(context) * self.children[1].evaluate(context)
            elif self.value == 'div':
                denominator = self.children[1].evaluate(context)
                if denominator == 0:
                    return 1.0  # 안전한 나눗셈
                return self.children[0].evaluate(context) / denominator
            elif self.value == 'sqrt':
                operand = self.children[0].evaluate(context)
                return math.sqrt(abs(operand))  # 음수 처리
            else:
                raise Exception(f"Unknown function: {self.value}")
        except:
            return 0.0  # 계산 중 오류 발생 시 0 반환

    def __str__(self):
        """노드를 실행 가능한 Python 코드 형태로 반환합니다."""
        if self.value in ['x', 'y', 'p']:
            return self.value
        elif isinstance(self.value, float):
            return f"{self.value:.2f}"
        elif self.value in FUNCTIONS:
            if self.value == 'sqrt':
                return f"math.sqrt({self.children[0]})"
            elif self.value == 'add':
                return f"({self.children[0]} + {self.children[1]})"
            elif self.value == 'sub':
                return f"({self.children[0]} - {self.children[1]})"
            elif self.value == 'mul':
                return f"({self.children[0]} * {self.children[1]})"
            elif self.value == 'div':
                return f"({self.children[0]} / {self.children[1]})"
        else:
            raise Exception(f"Unknown function: {self.value}")

    def copy(self):
        """노드를 복사합니다."""
        return Node(self.value, [child.copy() for child in self.children])


def random_terminal():
    """x, y, p, 상수 중 하나를 랜덤하게 반환합니다."""
    choices = ['x', 'y', 'p', 'const']
    choice = random.choice(choices)
    if choice in ['x', 'y', 'p']:
        return Node(choice)
    else:
        # 0.01부터 1.00 사이의 값을 균등 분포로 선택
        value = round(random.uniform(0.01, 1.00), 2)
        return Node(value)


def generate_random_tree(depth):
    """
    초기 랜덤 트리 생성:
    - 깊이가 0이거나 일정확률로 터미널 반환
    - 그렇지 않으면 연산자를 선택해 하위 노드 생성
    """
    if depth == 0 or (depth < MAX_DEPTH and random.random() < 0.3):
        return random_terminal()
    else:
        func = random.choice(FUNCTIONS)
        if func == 'sqrt':
            child = generate_random_tree(depth - 1)
            return Node(func, [child])
        else:
            left_child = generate_random_tree(depth - 1)
            right_child = generate_random_tree(depth - 1)
            return Node(func, [left_child, right_child])


def mutate(node, depth):
    """노드의 일부를 랜덤하게 변경하여 변이 트리를 생성합니다."""
    if random.random() < MUTATION_RATE:
        return generate_random_tree(depth)
    else:
        new_node = node.copy()
        if new_node.children:
            new_node.children = [mutate(child, depth - 1) for child in new_node.children]
        return new_node


def crossover(parent1, parent2):
    """부모 트리 두 개를 교차시켜 새로운 자식 트리를 생성합니다."""
    if random.random() < CROSSOVER_RATE:
        return parent2.copy()
    else:
        new_node = parent1.copy()
        if new_node.children and parent2.children:
            idx = random.randrange(len(new_node.children))
            new_node.children[idx] = crossover(new_node.children[idx], random.choice(parent2.children))
        return new_node


def fitness_function(individual, bug_ids):
    total_fitness = 0.0
    num_bug_ids = 0

    for bug_id in bug_ids:
        try:
            # bug_info 로드
            bug_info = load_bug_info(bug_id)
            # new_spectrum.json에서 bug_id에 해당하는 메소드 정보 로드
            if bug_id not in SPECTRUM_DATA:
                # 해당 bug_id에 대한 스펙트럼 정보 없음
                continue
            methods_data = SPECTRUM_DATA[bug_id]
            # print(f"bug-id = {bug_id}, formula = {individual}")
            # 메소드명과 e_p, n_p, e_f, n_f, p 추출
            method_names = list(methods_data.keys())
            labels = get_labels(method_names, bug_info)
            # print(f"labels = {labels}")

            # 각 메소드별로 x, y, p 계산
            # x = e_f/(e_f+n_f), y = e_p/(e_p+n_p), p는 이미 있음
            scores = []
            for i, method in enumerate(method_names):
                m_data = methods_data[method]
                e_p = m_data.get('e_p', 0)
                n_p = m_data.get('n_p', 0)
                e_f = m_data.get('e_f', 0)
                n_f = m_data.get('n_f', 0)
                p_val = m_data.get('p', 0.0)

                x_val = e_f / (e_f + n_f) if (e_f + n_f) > 0 else 0.0
                y_val = e_p / (e_p + n_p) if (e_p + n_p) > 0 else 0.0

                context = {'x': x_val, 'y': y_val, 'p': p_val}
                score = individual.evaluate(context)
                scores.append(score)
                # print(f"method = {method}, context = {context}, score = {score}")

            # 점수로 내림차순 정렬
            methods_list = list(zip(method_names, scores, labels))
            methods_list.sort(key=lambda x: x[1], reverse=True)

            total_methods = len(methods_list)
            buggy_indices = [index for index, (_, _, label) in enumerate(methods_list) if label == 1]
            # print(methods_list)
            # print(buggy_indices)
            if not buggy_indices:
                avg_wef = total_methods
            else:
                avg_wef = sum(buggy_indices) / len(buggy_indices) + 1

            fitness_value = total_methods / avg_wef

            total_fitness += fitness_value
            num_bug_ids += 1

        except Exception as e:
            print(f"Error processing bug {bug_id}: {e}", flush=True)
            continue

    if num_bug_ids == 0:
        return 0.0
    else:
        return total_fitness / num_bug_ids


def fitness_function_with_output(individual, bug_ids):
    """
    엘리트 개체의 적합도 계산 및 그룹별 상위 10개 버그 출력
    """
    total_fitness = 0.0
    num_bug_ids = 0
    bug_fitness_list = []

    group_mapping = {
        "Lang": [],
        "Math": [],
        "Time": [],
        "Chart": []
    }

    for bug_id in bug_ids:
        try:
            bug_info = load_bug_info(bug_id)
            if bug_id not in SPECTRUM_DATA:
                continue
            methods_data = SPECTRUM_DATA[bug_id]
            method_names = list(methods_data.keys())
            labels = get_labels(method_names, bug_info)

            statement_data = []
            for i, method in enumerate(method_names):
                m_data = methods_data[method]
                e_p = m_data.get('e_p', 0)
                n_p = m_data.get('n_p', 0)
                e_f = m_data.get('e_f', 0)
                n_f = m_data.get('n_f', 0)
                p_val = m_data.get('p', 0.0)
                x_val = e_f / (e_f + n_f) if (e_f + n_f) > 0 else 0.0
                y_val = e_p / (e_p + n_p) if (e_p + n_p) > 0 else 0.0

                context = {'x': x_val, 'y': y_val, 'p': p_val}
                score = individual.evaluate(context)
                label = labels[i]
                statement_data.append((method, score, label, e_p, e_f, n_p, n_f, x_val, y_val, p_val))

            # method-level aggregation은 이미 메소드 단위로 되어 있으므로
            # 바로 methods_list 생성
            methods_list = [(m, s, l, {'e_p': ep, 'e_f': ef, 'n_p': np_, 'n_f': nf, 'x': xv, 'y': yv, 'p': pv}) 
                             for (m, s, l, ep, ef, np_, nf, xv, yv, pv) in statement_data]

            methods_list.sort(key=lambda x: x[1], reverse=True)

            total_methods = len(methods_list)
            buggy_indices = [index for index, (_, _, label, _) in enumerate(methods_list) if label == 1]

            if not buggy_indices:
                avg_wef = total_methods
            else:
                avg_wef = sum(buggy_indices) / len(buggy_indices) + 1

            fitness_value = total_methods / avg_wef
            total_fitness += fitness_value
            num_bug_ids += 1

            # 버그의 그룹 식별
            bug_group = None
            for group_name in group_mapping.keys():
                if bug_id.startswith(group_name):
                    bug_group = group_name
                    break

            if bug_group:
                bug_fitness_list.append({
                    "Bug ID": bug_id,
                    "Group": bug_group,
                    "Fitness": fitness_value,
                    "Avg WEF": avg_wef,
                    "Total Methods": total_methods,
                    "Methods List": methods_list
                })

        except Exception as e:
            print(f"Error processing bug {bug_id}: {e}", flush=True)
            continue

    # # 그룹별 상위 10개 출력
    # for group_name in group_mapping.keys():
    #     group_bugs = [bug for bug in bug_fitness_list if bug["Group"] == group_name]
    #     group_bugs.sort(key=lambda x: x["Fitness"], reverse=True)
    #     top_10_bugs = group_bugs[:10]

    #     print(f"\n=== Top 10 Bugs for Group {group_name} ===", flush=True)
    #     for bug in top_10_bugs:
    #         print(f"\nBug ID: {bug['Bug ID']}, Fitness: {bug['Fitness']:.6f}, Avg WEF: {bug['Avg WEF']:.2f}, Total Methods: {bug['Total Methods']}", flush=True)
    #         print(f"{'Method':<70} {'Score':<20} {'Buggy':<10} {'e_p':<5} {'e_f':<5} {'n_p':<5} {'n_f':<5} {'x':<10} {'y':<10} {'p':<10}", flush=True)
    #         top_methods = bug["Methods List"][:10]
    #         for method, score, label, data in top_methods:
    #             buggy_status = 'True' if label == 1 else 'False'
    #             ep = data['e_p']
    #             ef = data['e_f']
    #             np_ = data['n_p']
    #             nf = data['n_f']
    #             xv = data['x']
    #             yv = data['y']
    #             pv = data['p']
    #             print(f"{method:<70} {score:<20.6f} {buggy_status:<10} {ep:<5} {ef:<5} {np_:<5} {nf:<5} {xv:<10.6f} {yv:<10.6f} {pv:<10.6f}", flush=True)

    if num_bug_ids == 0:
        final_fitness = 0.0
    else:
        final_fitness = total_fitness / num_bug_ids

    print(f"\nOverall Fitness (Average over bugs): {final_fitness:.6f}", flush=True)

    return final_fitness


def tournament_selection(population, fitnesses):
    """토너먼트 방식으로 개체를 선택합니다."""
    selected = random.sample(list(zip(population, fitnesses)), TOURNAMENT_SIZE)
    selected.sort(key=lambda x: x[1], reverse=True)
    return selected[0][0]


def evolve(training_data, all_bug_ids):
    population = [generate_random_tree(MAX_DEPTH) for _ in range(POPULATION_SIZE)]
    best_individual = None
    best_fitness = -1
    all_formulas = []

    for generation in range(NUM_GENERATIONS):
        fitnesses = [fitness_function(ind, training_data) for ind in population]
        idx = np.argmax(fitnesses)
        best_individual = population[idx]

        if ELITISM:
            new_population = [best_individual]
        else:
            new_population = []

        while len(new_population) < POPULATION_SIZE:
            parent1 = tournament_selection(population, fitnesses)
            parent2 = tournament_selection(population, fitnesses)
            child = crossover(parent1, parent2)
            child = mutate(child, MAX_DEPTH)
            new_population.append(child)

        population = new_population

        all_formulas.append((generation + 1, str(best_individual)))

        print(f"\n=== Generation {generation + 1} ===", flush=True)
        print(f"Best Individual Formula: {best_individual}", flush=True)
        fitness_function_with_output(best_individual, all_bug_ids)

    return best_individual, all_formulas


def main():
    bug_ids = get_all_bug_ids()
    kf = KFold(n_splits=K_FOLDS, shuffle=True, random_state=42)
    bug_ids = np.array(bug_ids)

    best_formulas = []
    fold = 1
    all_generations_formulas = []

    for train_index, test_index in kf.split(bug_ids):
        print(f"\n=== Fold {fold} ===", flush=True)
        training_data = bug_ids[train_index]
        validation_data = bug_ids[test_index]

        best_individual, formulas = evolve(training_data, bug_ids)
        val_fitness = fitness_function(best_individual, validation_data)
        print(f"\nValidation Fitness (Avg Total_Methods / Avg_WEF): {val_fitness:.6f}", flush=True)
        print(f"Evolved Formula: {best_individual}", flush=True)

        all_generations_formulas.extend([(fold, gen, form) for gen, form in formulas])
        best_formulas.append((best_individual, val_fitness))
        fold += 1

    best_formulas.sort(key=lambda x: x[1], reverse=True)
    final_formula = best_formulas[0][0]
    print(f"\nBest Formula after K-Fold CV:\n{final_formula}", flush=True)

    with open('best_formula_by_wef.txt', 'w') as f:
        f.write(str(final_formula))

    print("\n=== All Formulas from Each Generation ===")
    for fold, generation, formula in all_generations_formulas:
        print(f"Fold {fold}, Generation {generation}: {formula}")


if __name__ == '__main__':
    main()
