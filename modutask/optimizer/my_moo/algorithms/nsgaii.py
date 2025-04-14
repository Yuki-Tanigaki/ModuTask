from typing import Callable

import numpy as np
from modutask.optimizer.my_moo.core.individual import Individual
from modutask.optimizer.my_moo.core.population import Population
from modutask.optimizer.my_moo.rng_manager import get_rng
from modutask.optimizer.my_moo.utils import dominates

def fast_non_dominated_sort(individuals: list[Individual]) -> list[list[Individual]]:
    fronts: list[list[Individual]] = []
    S = {}  # individuals dominated by p
    n = {}  # number of individuals dominating p
    rank = {}

    seen = []
    for p in individuals:
        # 重複チェック
        if any(p == q for q in seen):
            p.fitness['rank'] = float('inf')  # 最悪ランクを付与
            continue

        seen.append(p)

        S[p] = []
        n[p] = 0
        for q in individuals:
            if p == q:
                continue
            if dominates(p.objectives, q.objectives):
                S[p].append(q)
            elif dominates(q.objectives, p.objectives):
                n[p] += 1
        if n[p] == 0:
            rank[p] = 0
            p.fitness['rank'] = 0
            if len(fronts) == 0:
                fronts.append([])
            fronts[0].append(p)

    i = 0
    while i < len(fronts):
        next_front = []
        for p in fronts[i]:
            for q in S[p]:
                n[q] -= 1
                if n[q] == 0:
                    rank[q] = i + 1
                    q.fitness['rank'] = i + 1
                    next_front.append(q)
        if next_front:
            fronts.append(next_front)
        i += 1

    return fronts

def calculate_crowding_distance(front: list[Individual]) -> None:
    if not front:
        return

    num_objectives = len(front[0].objectives)
    for ind in front:
        ind.fitness['crowding_distance'] = 0.0

    for m in range(num_objectives):
        front.sort(key=lambda ind: ind.objectives[m])
        front[0].fitness['crowding_distance'] = float('inf')
        front[-1].fitness['crowding_distance'] = float('inf')
        obj_min = front[0].objectives[m]
        obj_max = front[-1].objectives[m]
        if obj_max - obj_min == 0:
            continue
        for i in range(1, len(front) - 1):
            prev_obj = front[i - 1].objectives[m]
            next_obj = front[i + 1].objectives[m]
            front[i].fitness['crowding_distance'] += (next_obj - prev_obj) / (obj_max - obj_min)

def tournament_selection(population: list[Individual], tournament_size: int = 2) -> Individual:
    candidates = get_rng().choice(population, size=tournament_size, replace=False)
    return min(candidates, key=lambda ind: (ind.fitness['rank'], -ind.fitness['crowding_distance']))

def generate_offspring(population: list[Individual], num_offspring: int, tournament_size=2) -> list[Individual]:
    fronts = fast_non_dominated_sort(population)
    for front in fronts:
        calculate_crowding_distance(front)

    for ind in population:
        if 'crowding_distance' not in ind.fitness:
            ind.fitness['crowding_distance'] = 0.0
    offspring = []
    for _ in range(num_offspring):
        p1 = tournament_selection(population, tournament_size)
        p2 = tournament_selection(population, tournament_size)
        child = p1.crossover(p2)
        child.mutate()
        offspring.append(child)
    return offspring

class NSGAII:
    def __init__(
        self,
        func: Callable[[list[int]], list[float]],
        encoding,
        population_size: int = 50,
        generations: int = 100,
    ):
        self.func = func
        self.encoding = encoding
        self.population_size = population_size
        self.generations = generations

        self.population: Population = Population.initialize(population_size, encoding)
        self.population.evaluate(func)

    def evolve(self):
        for _ in range(self.generations):
            # print(_)
            # F = np.array([ind.objectives for ind in list(self.population)])
            # from pymoo.indicators.hv import HV
            # hv = HV(ref_point=np.array([110, 110, 110]))
            # print(hv.do(F))
            # 1. 子個体を生成
            offspring = Population(generate_offspring(list(self.population), self.population_size))

            # 2. 評価
            offspring.evaluate(self.func)
            for child in offspring:
                child.set_objectives(self.func(child.genome))

            # 3. 親 + 子を統合
            combined = list(self.population) + list(offspring)

            # 4. 非支配ソート
            fronts = fast_non_dominated_sort(combined)

            # 5. 次世代の選択
            next_population = []
            for front in fronts:
                calculate_crowding_distance(front)
                if len(next_population) + len(front) <= self.population_size:
                    next_population.extend(front)
                else:
                    sorted_front = sorted(front, key=lambda ind: ind.fitness['crowding_distance'], reverse=True)
                    next_population.extend(sorted_front[:self.population_size - len(next_population)])
                    break

            self.population = Population(next_population)

    def get_result(self) -> list[Individual]:
        return self.population.individuals
