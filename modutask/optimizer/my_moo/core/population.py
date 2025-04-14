from typing import Any, Callable
from modutask.optimizer.my_moo.core.encoding import BaseVariable
from modutask.optimizer.my_moo.core.individual import Individual

class Population:
    def __init__(self, individuals: list[Individual]):
        self.individuals = individuals

    @classmethod
    def initialize(cls, size: int, encoding: BaseVariable) -> 'Population':
        """指定したサイズの個体群をランダム生成"""
        individuals = [Individual(encoding) for _ in range(size)]
        return cls(individuals)

    def evaluate(self, func: Callable[[Any], list[float]]):
        """全個体を一括評価"""
        for ind in self.individuals:
            ind.objectives = func(ind.genome)

    def __len__(self):
        return len(self.individuals)

    def __getitem__(self, idx):
        return self.individuals[idx]

    def __iter__(self):
        return iter(self.individuals)
