from typing import Dict, Type, List
import inspect, logging, yaml
import networkx as nx
from modutask.core import *
from modutask.io.input import Input
from modutask.io.output import Output

logger = logging.getLogger(__name__)

def find_subclasses_by_name(base_class: Type) -> Dict[str, Type]:
    """
    指定された基底クラスのすべてのサブクラスを探索し、クラス名をキーとする辞書を返す

    :param base_class: 基底クラス
    :return: クラス名をキー、クラスオブジェクトを値とする辞書
    """
    subclasses = {}
    for cls in base_class.__subclasses__():
        subclasses[cls.__name__] = cls  # クラス名 (__name__) をキーとして登録
    return subclasses

def get_class_init_args(cls):
    """ クラスの __init__ メソッドの引数を取得 """
    signature = inspect.signature(cls.__init__)
    return [param for param in signature.parameters]

class DataManager:
    """ タスク、モジュール、ロボットのデータを管理するクラス """

    def __init__(self, prop_file: str):
        try:
            with open(prop_file, 'r') as f:
                prop = yaml.safe_load(f)
        except FileNotFoundError as e:
            logging.error(f"File not found: {e}")
            raise
        self.input = Input(prop)
        self.output = Output()
    
    def check_duplicate_modules(self, robots: Dict[str, Robot]) -> bool:
        """
        ロボットごとのモジュール名の重複をチェックする関数。
        重複がある場合はエラーを出力し、Falseを返す。
        """
        all_module_names = []
        for robot_name, robot in robots.items():
            module_names = [module.name for module in robot.component_required]
            duplicates = set(name for name in module_names if module_names.count(name) > 1)
            if duplicates:
                logging.error(f"Robot '{robot_name}' has duplicate modules: {duplicates}.")
                raise ValueError(f"Robot '{robot_name}' has duplicate modules: {duplicates}.")
            all_module_names.extend(module_names)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run the robotic system simulator.")
    parser.add_argument("--property_file", type=str, help="Path to the property file")
    args = parser.parse_args()

    manager = DataManager(args.property_file)
    tasks = manager.input.load_tasks()
    module_types = manager.input.load_module_types()
    modules = manager.input.load_modules(module_types=module_types)
    robot_types = manager.input.load_robot_types(module_types=module_types)
    robots = manager.input.load_robots(robot_types=robot_types, modules=modules)
    manager.check_duplicate_modules(robots=robots)
    scenarios = manager.input.load_scenarios()
    task_priority = manager.input.load_task_priority(robots=robots, tasks=tasks)
    # print(robots)
    # print(task_priority)
    # manager.output.save_task_priority(task_priority=task_priority)

if __name__ == '__main__':
    main()
