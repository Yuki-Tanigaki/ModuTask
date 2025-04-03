from modutask.optimizer.my_moo.core.individual import Individual

def dominates(obj1: list[float], obj2: list[float]) -> bool:
    """obj1 が obj2 を支配するなら True（すべての目的で劣らず、少なくとも1つで勝る）"""
    return all(a <= b for a, b in zip(obj1, obj2)) and any(a < b for a, b in zip(obj1, obj2))

def get_non_dominated_individuals(individuals: list[Individual]) -> list[Individual]:
    """与えられた個体群の中から、非支配な個体だけを抽出する"""
    non_dominated = []
    for i, ind_i in enumerate(individuals):
        dominated = False
        for j, ind_j in enumerate(individuals):
            if i != j and dominates(ind_j.objectives, ind_i.objectives):
                dominated = True
                break
        if not dominated:
            non_dominated.append(ind_i)
    return non_dominated
