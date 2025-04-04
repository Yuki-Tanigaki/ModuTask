from typing import Any
from copy import deepcopy
from modutask.optimizer.my_moo.core.encoding import BaseVariable

class Individual:
    def __init__(self, encoding: BaseVariable):
        self.encoding = encoding
        self.genome = self.encoding.sample()
        self.objectives: list[float] = []
        self.fitness: dict[str, Any] = {}

    def set_objectives(self, values: list[float]):
        self.objectives = values

    def crossover(self, other: 'Individual') -> 'Individual':
        child = Individual(self.encoding)
        child.genome = self.encoding.crossover(self.genome, other.genome)
        return child

    def mutate(self):
        self.genome = self.encoding.mutate(self.genome)

    def copy(self) -> 'Individual':
        clone = Individual(self.encoding)
        clone.genome = self.genome[:]
        clone.objectives = self.objectives[:]
        clone.fitness = deepcopy(self.fitness)
        return clone

    def __repr__(self):
        return (
            f"Individual(genome={self.genome}, "
            f"objectives={self.objectives}, rank={self.rank})"
        )
