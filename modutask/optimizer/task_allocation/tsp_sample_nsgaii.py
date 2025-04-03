import numpy as np
import random, math
from modutask.optimizer.my_moo import *

num_cities = 30

def generate_random_cities(num_cities: int, seed: int = 42) -> list[tuple[float, float]]:
    random.seed(seed)
    return [
        (random.uniform(0, 100), random.uniform(0, 100))
        for _ in range(num_cities)
    ]

def dummy_tsp(order: list[int], cities_a, cities_b) -> list[float]:
    """TSPを使ったダミー目的関数"""
    def euclidean(p1: tuple[float, float], p2: tuple[float, float]) -> float:
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])
    def total_distance(cities):
        return sum(
            euclidean(cities[order[i]], cities[order[(i + 1) % len(order)]])
            for i in range(len(order))
        )
    
    dist1 = total_distance(cities_a)
    dist2 = total_distance(cities_b)
    return [dist1, dist2]

def main():
    seed_rng(42)
    cities_a = generate_random_cities(30, seed=123)
    cities_b = generate_random_cities(30, seed=456)
    def sim_func(order: list[int]) -> list[float]:
        return dummy_tsp(order, cities_a, cities_b)

    encoding = PermutationVariable(items=list(range(30)))

    algo = NSGAII(
        simulation_func=sim_func,
        encoding=encoding,
        population_size=100,
        generations=200,
    )
    algo.evolve()

    nds = get_non_dominated_individuals(algo.get_result())
    print("\n非支配解:")
    for ind in nds:
        print(ind.objectives)

if __name__ == "__main__":
    main()
