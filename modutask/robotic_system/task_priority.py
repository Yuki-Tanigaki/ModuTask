from itertools import permutations
from typing import Dict, List, Tuple, Any
import pickle

from .core import *

class RobotTaskPriority:
    """
    各ロボットのタスク優先度リストを生成・管理するクラス。
    """

    def __init__(self, robots: List[Robot], tasks: List[Task]):
        """
        コンストラクタでロボットとタスクの情報を受け取り、優先度リストを作成する。

        :param robots: 使用可能なロボットのリスト
        :param tasks: 実行可能なタスクのリスト
        """
        self.robots = robots
        self.tasks = tasks
        self.priority_map = self._initialize_priority_map()

    def _initialize_priority_map(self) -> Dict[str, List[Tuple[str]]]:
        """
        各ロボットのタスク優先度リスト（タスクの順列）を生成。

        :return: ロボット名をキー、タスク名の順列リストを値とする辞書
        """
        priority_map = {}

        for robot in self.robots:
            # 順列を生成（タスク名の順列）
            task_permutations = list(permutations([task.name for task in self.tasks]))

            # ロボットごとに優先度リストを保存
            priority_map[robot.name] = task_permutations

        return priority_map

    def get_priority(self, robot_name: str) -> List[Tuple[str]]:
        """
        指定したロボットのタスク優先度リストを取得。

        :param robot_name: ロボット名
        :return: タスク名の順列リスト
        """
        return self.priority_map.get(robot_name, [])

    def update_priority(self, priority_map):
        """
        タスクやロボットの状態が変化した場合に優先度リストを再計算する。
        """
        self.priority_map = priority_map

    def display_priority(self):
        """
        各ロボットのタスク優先度リストを表示する。
        """
        for robot_name, task_orders in self.priority_map.items():
            print(f"{robot_name}: {task_orders[:5]}")  # 最初の5パターンのみ表示

    def save_priority_map_to_txt(self, file_path: str):
        """
        優先度マップをテキストファイルとして保存する。

        :param file_path: 保存するファイルのパス
        """
        with open(file_path, "w") as f:
            for robot_name, task_orders in self.priority_map.items():
                f.write(f"{robot_name}:\n")
                for order in task_orders:
                    f.write(f"  {', '.join(order)}\n")
                f.write("\n")  # 改行を入れる
        print(f"Priority map saved as text file: {file_path}")

    def save_priority_map_to_pickle(self, file_path: str):
        """
        優先度マップを pickle ファイルとして保存する。

        :param file_path: 保存するファイルのパス
        """
        with open(file_path, "wb") as f:
            pickle.dump(self.priority_map, f)
        print(f"Priority map saved as pickle file: {file_path}")