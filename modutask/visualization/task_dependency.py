import argparse, yaml, os, logging
import networkx as nx
import matplotlib.pyplot as plt
from modutask.core import BaseTask
from modutask.io import DataManager
from modutask.utils import raise_with_log
# plt.figure(figsize=(10, 8), constrained_layout=True)
# pos = nx.nx_agraph.graphviz_layout(G, prog="dot")  # `dot` はツリー風にレイアウト
# nx.draw(G, pos, with_labels=True, arrows=True, node_size=1500, node_color="lightblue", font_size=10)
# plt.title("Task Dependency DAG")
# plt.tight_layout()
# plt.savefig("graph.png")

logger = logging.getLogger(__name__)

def make_figure(tasks: dict[str, BaseTask], file_path: str):
    dependency_dict = {}
    for task_name, task in tasks.items():
        dependency_dict[task_name] = [t.name for t in task.task_dependency]

    # DAGを構築（依存先 → タスク）
    G = nx.DiGraph()
    for task, deps in dependency_dict.items():
        for dep in deps:
            G.add_edge(dep, task)

    def remove_transitive_edges(dag: nx.DiGraph) -> nx.DiGraph:
        # 推移的辺を削除
        dag = dag.copy()
        edges_to_check = list(dag.edges())
        edges_to_remove = []

        for u, v in edges_to_check:
            dag.remove_edge(u, v)
            if nx.has_path(dag, u, v):
                edges_to_remove.append((u, v))
            else:
                dag.add_edge(u, v)

        dag.remove_edges_from(edges_to_remove)
        return dag

    G_simple = remove_transitive_edges(G)
    fig, ax = plt.subplots(figsize=(10, 8), constrained_layout=True)
    nx.draw(G_simple, pos=nx.circular_layout(G_simple), with_labels=True, arrows=True, ax=ax)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    plt.savefig(file_path)

def main():
    """
    property_fileの設定でタスク依存関係をグラフ化
    """
    parser = argparse.ArgumentParser(description="Run the robotic system simulator.")
    parser.add_argument("--property_file", type=str, help="Path to the property file")
    args = parser.parse_args()
    try:
        with open(args.property_file, 'r') as f:
            prop = yaml.safe_load(f)
    except FileNotFoundError as e:
        raise_with_log(FileNotFoundError, f"File not found: {e}.")

    manager = DataManager(load_task_priorities=True)
    manager.load(load_path=prop["load"])
    make_figure(tasks=manager.tasks, file_path=prop["figure"]["task_dependency"])
    

if __name__ == '__main__':
    main()