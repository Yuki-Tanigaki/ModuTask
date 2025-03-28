import random
import numpy as np
from config import Config
import networkx as nx
from modutask.core import *
from modutask.io.output import Output


def generate_dag_with_influence(nodes, max_depth, target_avg_influence, max_attempts, tolerance, seed=None):
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    G = nx.DiGraph()
    G.add_nodes_from(nodes)

    # ノードをレイヤーに分割
    random.shuffle(nodes)
    layers = [[] for _ in range(max_depth)]
    
    # 最初に1つのパスを作成（深さ=max_depth に相当する接続）
    path = random.sample(nodes, max_depth)
    for i in range(max_depth - 1):
        G.add_edge(path[i], path[i + 1])
        layers[i].append(path[i])
    layers[-1].append(path[-1])
    remaining_nodes = [n for n in nodes if n not in path]

    # 残りのノードをランダムにレイヤーに追加
    for node in remaining_nodes:
        layer_idx = random.randint(0, max_depth - 1)
        layers[layer_idx].append(node)

    # 各ノードに最低1つ親を持たせる（深さ1以外）
    for current_depth in range(1, max_depth):
        for node in layers[current_depth]:
            src = random.choice(layers[current_depth - 1])
            G.add_edge(src, node)

    # 影響範囲の平均が目標に近づくまでランダムに追加
    def avg_influence(G):
        return np.mean([len(nx.descendants(G, n)) for n in G.nodes])
    
    current_avg = avg_influence(G)
    iteration = 0
    while abs(current_avg - target_avg_influence) > tolerance and iteration < max_attempts:
        d = random.randint(1, max_depth - 1)
        from_node = random.choice(layers[d])
        to_depth = random.randint(0, d - 1)
        to_node = random.choice(layers[to_depth])
        if not G.has_edge(to_node, from_node) and not nx.has_path(G, from_node, to_node):  # avoid cycles
            G.add_edge(to_node, from_node)
            current_avg = avg_influence(G)
        iteration += 1

    return G

def set_task_type_and_location(max_attempts, tolerance, seed):
    random.seed(seed)
    np.random.seed(seed)
    # タスク種類の割り当て
    class_num = {}
    floored_counts = [int(Config.TASK.NUMBER * r) for r in Config.TASK.CLASS_RATE]
    remaining = Config.TASK.NUMBER - sum(floored_counts)
    indices = list(range(len(Config.TASK.CLASS)))
    random.shuffle(indices)
    for i in range(remaining):
        floored_counts[indices[i % len(Config.TASK.CLASS)]] += 1
    class_num = {name: count for name, count in zip(Config.TASK.CLASS, floored_counts)}
    # 作業座標の割り当て
    cood_list = None
    for _ in range(max_attempts):
        indices = random.choices(range(len(Config.COORDINATE_SET)), k=Config.TASK.NUMBER)
        variance = np.var(indices, ddof=0)  # インデックスの分散
        if abs(variance - Config.TASK.LOCATION_VARIANCE) < tolerance:
            cood_list = [Config.COORDINATE_SET[i] for i in indices]
            break
    if cood_list is None:
        raise ValueError
    
    return class_num, cood_list

max_attempts = 100000  # 試行回数
tolerance = 0.05  # 許容誤差
seed = 1234


class_num, cood_list = set_task_type_and_location(max_attempts, tolerance, seed)

tasks = {}
i = 0
for class_name, class_num in  class_num.items():
    performance = {attr: random.randint(Config.TASK.PERFORMANCE_MIN, Config.TASK.PERFORMANCE_MAX) for attr in PerformanceAttributes}
    for _ in range(class_num):
        if class_name == 'Transport':
            v = np.array(cood_list[i]) - np.array([0.0, 0.0])
            transportability = 10 / np.linalg.norm(v)
            filtered_args = {
                'name':f"t_{i:03}",
                'coordinate':[0.0, 0.0],
                'required_performance':performance,
                'origin_coordinate':[0.0, 0.0],
                'destination_coordinate':cood_list[i],
                'transportability':transportability,
                'total_workload':10,
                'completed_workload':0
                }
            tasks[f"t_{i:03}"] = Transport(**filtered_args)
        if class_name == 'Manufacture':
            filtered_args = {
                'name':f"t_{i:03}",
                'coordinate':cood_list[i],
                'required_performance':performance,
                'total_workload':10,
                'completed_workload':0
                }
            tasks[f"t_{i:03}"] = Manufacture(**filtered_args)
        i += 1

nodes = [key for key in tasks]

G = generate_dag_with_influence(nodes, max_depth=Config.TASK.DEPENDENCY_DEPTH, 
                                target_avg_influence=Config.TASK.DEPENDENCY_INFLUENCE, 
                                max_attempts=max_attempts, tolerance=tolerance,
                                seed=seed)
print("ノード数:", G.number_of_nodes())
print("エッジ数:", G.number_of_edges())
print("最大深さ:", len(nx.dag_longest_path(G)))
print("平均影響度:", np.mean([len(nx.descendants(G, n)) for n in G.nodes]))

for name, task in tasks.items():
    ancestors = nx.ancestors(G, name)
    task_dependency = []
    for ancestor in ancestors:
        task_dependency.append(tasks[ancestor])
    task.initialize_task_dependency(task_dependency)

output = Output()
output.save_tasks(tasks=tasks, filepath='./configs/sample001/task.yaml')
output.save_task_dependency(tasks=tasks, filepath='./configs/sample001/task_dependency.yaml')