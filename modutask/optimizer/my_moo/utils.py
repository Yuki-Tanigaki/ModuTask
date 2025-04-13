from sklearn.cluster import KMeans
import numpy as np
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

def select_kmeans_representatives(pareto_individuals: list[Individual], k: int) -> list[Individual]:
    if len(pareto_individuals) <= k:
        return pareto_individuals

    # 目的関数空間を取得
    F = np.array([ind.objectives for ind in pareto_individuals])

    # ユニークな目的関数ベクトルをチェック
    unique_F = np.unique(F, axis=0)
    effective_k = min(k, len(unique_F))

    # k-meansクラスタリングを実行
    kmeans = KMeans(n_clusters=effective_k, n_init='auto', random_state=0)
    labels = kmeans.fit_predict(F)
    centers = kmeans.cluster_centers_

    # 各クラスタから中心に最も近い個体を1つ選択
    selected = []
    for i in range(effective_k):
        cluster_indices = np.where(labels == i)[0]
        cluster_points = F[cluster_indices]
        center = centers[i]

        # 中心に最も近い個体を選ぶ
        dists = np.linalg.norm(cluster_points - center, axis=1)
        best_idx = cluster_indices[np.argmin(dists)]
        selected.append(pareto_individuals[best_idx])

    return selected