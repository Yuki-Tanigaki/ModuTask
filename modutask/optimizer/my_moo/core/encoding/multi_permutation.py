from typing import Any
from copy import deepcopy
from modutask.optimizer.my_moo.core.encoding import BaseVariable
from modutask.optimizer.my_moo.rng_manager import get_rng

class MultiPermutationVariable(BaseVariable):
    def __init__(self, items: list[Any], n_multi: int):
        self.items = items  # 初期リスト（例：[0, 1, 2, 3, 4]）
        self.n_multi = n_multi

    def sample(self) -> list[list[Any]]:
        """ランダムな順列を生成"""
        gene_list = []
        for _ in range(self.n_multi):
            rng = get_rng()
            perm = self.items[:]
            rng.shuffle(perm)
            gene_list.append(perm)
        return gene_list

    def mutate(self, value: list[list[Any]]) -> list[list[Any]]:
        """スワップ突然変異"""
        rng = get_rng()
        p = float(1.0/self.n_multi)
        mutated = []
        for permutation in value:
            new_perm = deepcopy(permutation)
            if len(new_perm) >= 2 and rng.random() < p:
                i, j = rng.choice(len(new_perm), 2, replace=False)
                new_perm[i], new_perm[j] = new_perm[j], new_perm[i]
            mutated.append(new_perm)
        return mutated

    def crossover(self, value1: list[list[Any]], value2: list[list[Any]]) -> list[list[Any]]:
        """順序交叉（Order Crossover, OX）"""
        rng = get_rng()
        def order_crossover(perm1: list[Any], perm2: list[Any]):
            size = len(perm1)
            start, end = sorted(rng.choice(size, 2, replace=False))
            new_perm = [None] * size
            new_perm[start:end+1] = perm1[start:end+1]
            fill_values = [item for item in perm2 if item not in new_perm]
            fill_index = 0
            for i in range(size):
                if new_perm[i] is None:
                    new_perm[i] = fill_values[fill_index]
                    fill_index += 1
            return new_perm
        child = []
        for permutation1, permutation2 in zip(value1, value2):
            # ランダムに親の役割を決める
            if rng.random() < 0.5:
                p1, p2 = permutation1, permutation2
            else:
                p1, p2 = permutation2, permutation1
            new_perm = order_crossover(deepcopy(p1), deepcopy(p2))
            child.append(new_perm)
        return child

    def validate(self, value: list[list[Any]]) -> bool:
        """すべての要素が一度ずつ現れるかチェック"""
        return sorted(value) == sorted(self.items)

    def __repr__(self):
        return f"MultiPermutationVariable(items={self.items})"
