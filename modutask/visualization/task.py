
import argparse, yaml, pickle, logging
import matplotlib.pyplot as plt
from modutask.core.task import *
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)

def plot_workload_pie(tasks: dict[str, BaseTask], file_path: str) -> None:
    """ 残りのworloadと完了済みworload: 円グラフ """
    total_completed = sum(task.completed_workload for task in tasks.values())
    total_remaining = sum(task.total_workload - task.completed_workload for task in tasks.values())

    sizes = [total_completed, total_remaining]
    labels = ['Completed', 'Remaining']
    colors = ['#4CAF50', '#FF7043']  # 緑・オレンジ系
    fig = plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
    plt.title('Total Task Progress')
    plt.axis('equal')  # 円を丸くする

    plt.tight_layout()
    plt.savefig(file_path)
    plt.close(fig)

# Plotting the task bar
# def plot_task(tasks, save_dir=None):
#     # カラーマップを用意する
#     color_map = {
#         'Transport': 'blue',
#         'Manufacture': 'green'
#     }
#     # 横軸はタスクのキー、縦軸は required_workload
#     task_keys = list(tasks.keys())
#     workloads = np.array([task.required_workload for task in tasks.values()])
#     current_progress = np.array([task.current_progress for task in tasks.values()])
#     left_workloads = workloads - current_progress
#     # 各要素が0より小さくならないようにする
#     left_workloads = np.maximum(left_workloads, 0)
#     # タスクごとの色を決定
#     colors = [color_map[task.__class__.__name__] for task in tasks.values()]

#     # 棒グラフを作成
#     plt.figure(figsize=(8, 6))
#     plt.bar(task_keys, left_workloads, color=colors)

#     # グラフにラベルを付ける
#     plt.xlabel('Tasks')
#     plt.ylabel('Required Workload')
#     plt.title('Required Workload for Each Task')
#     # 凡例を追加
#     handles = [plt.Rectangle((0,0),1,1, color=color_map[cat]) for cat in color_map]
#     labels = list(color_map.keys())
#     plt.legend(handles, labels)
#     # グラフを表示
#     if not os.path.exists(save_dir):
#         os.makedirs(save_dir)
#     if save_dir:
#         image_file = os.path.join(save_dir, 'task.png')
#         plt.savefig(image_file)
#     plt.close()

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

    max_step = prop['simulation']['max_step']
    for current_step in range(max_step):
        load_template = prop['results']['task']
        load_path = load_template.format(index=current_step)
        save_template = prop["figure"]["workload_pie"]
        save_path = save_template.format(index=current_step)
        with open(load_path, "rb") as f:
            tasks: dict[str, BaseTask] = pickle.load(f)
            # for name, task in tasks.items():
                # print(task.completed_workload)
            plot_workload_pie(tasks=tasks, file_path=save_path)

    

if __name__ == '__main__':
    main()