from copy import deepcopy
from typing import Any, Callable
import numpy as np
from math import exp
from pymoo.indicators.hv import HV
from modutask.optimizer.my_moo.core.individual import Individual
from modutask.optimizer.my_moo.core.population import Population
from modutask.optimizer.my_moo.rng_manager import get_rng

def calculate_hv_contributions(individuals: list[Individual], ref_point: list[float]) -> list[float]:
    # 全個体の目的関数値を NumPy 配列に変換
    F = np.array([ind.objectives for ind in individuals])
    hv = HV(ref_point=np.array(ref_point))

    # 全体の Hypervolume を事前に計算（省略可）
    base_volume = hv.do(F)

    contributions = []

    for i in range(len(individuals)):
        # 個体 i を除いたときの目的値集合
        F_excluded = np.delete(F, i, axis=0)
        volume_without_i = hv.do(F_excluded)
        contribution = base_volume - volume_without_i
        contributions.append(contribution)

    return contributions

def calculate_fitness(contributions: list[float], kappa: float = 0.05) -> list[float]:
    fitness = []
    for i, _ in enumerate(contributions):
        fit = 0.0
        for j, contrib_j in enumerate(contributions):
            if i == j:
                continue
            delta = contrib_j - contributions[i]  # 貢献度の差（y - x）
            try:
                value = -exp(-delta / kappa)
            except OverflowError:
                value = 0.0  # 極限的に小さい値と見なす
            fit += value
        fitness.append(fit)
    return fitness

def truncate_to_n(individuals: list[Individual], n: int, ref_point: list[float], kappa: float = 0.05) -> list[Individual]:
    pool = deepcopy(individuals)

    while len(pool) > n:
        # 1. HV貢献度を計算
        contributions = calculate_hv_contributions(pool, ref_point)

        # 2. 適応度を計算
        fitness = calculate_fitness(contributions, kappa)

        # 3. 最も fitness（削除しても痛くない）な個体を削除
        worst_idx = np.argmax(fitness)
        del pool[worst_idx]

    return pool

def tournament_selection(population: list[Individual], tournament_size=2) -> Individual:
    candidates = get_rng().choice(population, size=tournament_size, replace=False)
    return min(candidates, key=lambda ind: ind.fitness['ibea_fit'])  # fitnessは小さいほど良い

def generate_offspring(population: list[Individual], num_offspring: int, kappa: float, tournament_size=2) -> list[Individual]:
    num_objs = len(population[0].objectives)
    ref_point = [
        max(ind.objectives[i] for ind in population) * 1.1
        for i in range(num_objs)
    ]
    contributions = calculate_hv_contributions(population, ref_point)
    fitness = calculate_fitness(contributions, kappa)
    for i, p in enumerate(population):
        p.fitness['ibea_fit'] = fitness[i]

    offspring = []
    for _ in range(num_offspring):
        p1 = tournament_selection(population, tournament_size)
        p2 = tournament_selection(population, tournament_size)
        child = p1.crossover(p2)
        child.mutate()
        offspring.append(child)
    return offspring

class IBEAHV:
    def __init__(
        self,
        simulation_func: Callable[[Any], list[float]],
        encoding,
        population_size: int = 50,
        generations: int = 100,
        kappa: float = 0.05,
    ):
        self.simulation_func = simulation_func
        self.encoding = encoding
        self.population_size = population_size
        self.generations = generations
        self.kappa = kappa

        self.population: Population = Population.initialize(population_size, encoding)
        self.population.evaluate(simulation_func)

    def evolve(self):
        for gen in range(self.generations):
            # 1. 子個体を生成
            offspring = generate_offspring(list(self.population), self.population_size, ref_point, self.kappa)

            # 2. 評価
            for child in offspring:
                child.set_objectives(self.simulation_func(child.genome))

            # 3. 親 + 子を統合
            combined = list(self.population) + offspring

            # 4. 参照点を決定（目的関数最大値 × 1.1）
            num_objs = len(combined[0].objectives)
            ref_point = [
                max(ind.objectives[i] for ind in combined) * 1.1
                for i in range(num_objs)
            ]

            # 5. IBEAによる生存選択
            survivors = truncate_to_n(combined, self.population_size, ref_point, self.kappa)

            # 6. 次世代へ更新
            self.population = Population(survivors)

            print(f"Generation {gen+1} complete")

    def get_result(self) -> list[Individual]:
        return self.population.individuals