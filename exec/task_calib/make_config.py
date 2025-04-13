import argparse, os, yaml, random
import numpy as np
import networkx as nx
from modutask.core import *
from modutask.io import *
from modutask.visualization.task_dependency import dag_draw_dag_graph

parser = argparse.ArgumentParser(description="")
parser.add_argument("--setting_file", type=str, help="Path to the setting file")
args = parser.parse_args()

# YAMLファイルの読み込み
with open(args.setting_file, "r", encoding="utf-8") as f:
    yaml_data = yaml.load(f, Loader=yaml.FullLoader)

random.seed(yaml_data["task"]["seed"])
tasks = load_tasks(file_path=yaml_data["config_dir"]["task"])

nodes = [key for key in tasks]
num_roots = yaml_data["task"]["root"]
max_depth = yaml_data["task"]["depth"]
target_avg_influence = yaml_data["task"]["influence"]

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

# ルートノードとして追加するノードを選ぶ
root_candidates = random.sample(remaining_nodes, num_roots - 1)
layers[0].extend(root_candidates)
# 残りのノードをランダムにレイヤーに追加
remaining_nodes = [n for n in remaining_nodes if n not in root_candidates]
for node in remaining_nodes:
    layer_idx = random.randint(1, max_depth - 1)
    layers[layer_idx].append(node)

# 各ノードに最低1つ親を持たせる（深さ1以外）
for current_depth in range(1, max_depth):
    for node in layers[current_depth]:
        if G.in_degree(node) == 0:
            candidates = layers[current_depth - 1]
            # 出力数（出次数）を取得
            out_degrees = {n: G.out_degree(n) for n in candidates}
            min_out = min(out_degrees.values())

            # 最小出力ノードだけに絞る
            least_used = [n for n, deg in out_degrees.items() if deg == min_out]

            # その中からランダムに1つ選ぶ
            src = random.choice(least_used)
            G.add_edge(src, node)

# 影響範囲の平均
def avg_influence(G):
    return np.mean([len(nx.descendants(G, n)) for n in G.nodes])

current_avg = avg_influence(G)
while current_avg < target_avg_influence:
    d = random.randint(1, max_depth - 1)
    from_node = random.choice(layers[d])
    to_depth = random.randint(0, d - 1)
    to_node = random.choice(layers[to_depth])
    if not G.has_edge(to_node, from_node) and not nx.has_path(G, from_node, to_node):  # avoid cycles
        G.add_edge(to_node, from_node)
        current_avg = avg_influence(G)

print("ノード数:", G.number_of_nodes())
print("エッジ数:", G.number_of_edges())
root_nodes = [n for n in G.nodes if G.in_degree(n) == 0]
num_roots = len(root_nodes)
print("ルートノードの数:", num_roots)
print("最大深さ:", len(nx.dag_longest_path(G)))
print("平均影響度:", np.mean([len(nx.descendants(G, n)) for n in G.nodes]))

for name, task in tasks.items():
    ancestors = nx.ancestors(G, name)
    task_dependency = []
    for ancestor in ancestors:
        task_dependency.append(tasks[ancestor])
    task.initialize_task_dependency(task_dependency)

os.makedirs(os.path.dirname(yaml_data["config_dir"]["task_dependency"]), exist_ok=True)
save_task_dependency(tasks=tasks, file_path=yaml_data["config_dir"]["task_dependency"])
dag_draw_dag_graph(tasks=tasks, file_path=yaml_data["figures"]["dag_graph"])

# def set_task_type_and_location(max_attempts, tolerance, seed):
#     random.seed(seed)
#     np.random.seed(seed)
#     # タスク種類の割り当て
#     class_num = {}
#     floored_counts = [int(Config.TASK.NUMBER * r) for r in Config.TASK.CLASS_RATE]
#     remaining = Config.TASK.NUMBER - sum(floored_counts)
#     indices = list(range(len(Config.TASK.CLASS)))
#     random.shuffle(indices)
#     for i in range(remaining):
#         floored_counts[indices[i % len(Config.TASK.CLASS)]] += 1
#     class_num = {name: count for name, count in zip(Config.TASK.CLASS, floored_counts)}
#     # 作業座標の割り当て
#     cood_list = None
#     for _ in range(max_attempts):
#         indices = random.choices(range(len(Config.COORDINATE_SET)), k=Config.TASK.NUMBER)
#         variance = np.var(indices, ddof=0)  # インデックスの分散
#         if abs(variance - Config.TASK.LOCATION_VARIANCE) < tolerance:
#             cood_list = [Config.COORDINATE_SET[i] for i in indices]
#             break
#     if cood_list is None:
#         raise ValueError
    
#     return class_num, cood_list