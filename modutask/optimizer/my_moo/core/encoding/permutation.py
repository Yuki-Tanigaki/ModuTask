import random
from typing import Any
from modutask.optimizer.my_moo.core.encoding import BaseVariable
from modutask.optimizer.my_moo.rng_manager import get_rng

class PermutationVariable(BaseVariable):
    def __init__(self, items: list[Any]):
        self.items = items  # 初期リスト（例：[0, 1, 2, 3, 4]）

    def sample(self) -> list[Any]:
        """ランダムな順列を生成"""
        rng = get_rng()
        perm = self.items[:]
        rng.shuffle(perm)
        return perm

    def mutate(self, value: list[Any]) -> list[Any]:
        """スワップ突然変異"""
        rng = get_rng()
        mutated = value[:]
        i, j = rng.choice(len(mutated), 2, replace=False)
        mutated[i], mutated[j] = mutated[j], mutated[i]
        return mutated

    def crossover(self, value1: list[Any], value2: list[Any]) -> list[Any]:
        """順序交叉（Order Crossover, OX）"""
        rng = get_rng()
        size = len(value1)
        start, end = sorted(rng.choice(size, 2, replace=False))
        child = [None] * size
        child[start:end+1] = value1[start:end+1]
        fill_values = [item for item in value2 if item not in child]
        fill_index = 0
        for i in range(size):
            if child[i] is None:
                child[i] = fill_values[fill_index]
                fill_index += 1
        return child

    def validate(self, value: list[Any]) -> bool:
        """すべての要素が一度ずつ現れるかチェック"""
        return sorted(value) == sorted(self.items)

    def __repr__(self):
        return f"PermutationVariable(items={self.items})"
