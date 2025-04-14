from typing import Any
from copy import deepcopy
from modutask.optimizer.my_moo.core.encoding import BaseVariable

class Individual:
    def __init__(self, encoding: BaseVariable, genome: list[Any] = None):
        self.encoding = encoding
        self.genome = genome if genome is not None else self.encoding.sample()
        self.objectives: list[float] = []
        self.fitness: dict[str, Any] = {}

    def set_objectives(self, values: list[float]):
        self.objectives = values

    def crossover(self, other: 'Individual') -> 'Individual':
        child_genome = self.encoding.crossover(self.genome, other.genome)
        return Individual(self.encoding, genome=child_genome)

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
            f"objectives={self.objectives})"
        )
    
    def __eq__(self, other):
        if not isinstance(other, Individual):
            return False
        # genomeが等しいかはencodingを使って判定
        return self.encoding.equals(self.genome, other.genome)
    
    def __hash__(self):
        return hash(self.encoding.hash(self.genome))