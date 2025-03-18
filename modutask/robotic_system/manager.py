from omegaconf import OmegaConf
from typing import Dict, List, Type
from collections import Counter
import numpy as np
import inspect
from .core import Task, Module, Robot, ModuleType, RobotType, RobotPerformanceAttributes, ModuleState, RobotState

def find_subclasses_by_name(base_class: Type) -> Dict[str, Type]:
    """
    指定された基底クラスのすべてのサブクラスを探索し、クラス名をキーとする辞書を返す。

    :param base_class: 基底クラス
    :return: クラス名をキー、クラスオブジェクトを値とする辞書
    """
    subclasses = {}
    for cls in base_class.__subclasses__():
        subclasses[cls.__name__] = cls  # クラス名 (__name__) をキーとして登録
    return subclasses

def get_class_init_args(cls):
    """クラスの __init__ メソッドの引数を取得"""
    signature = inspect.signature(cls.__init__)
    return [param for param in signature.parameters]

class DataManager:
    """ タスク、モジュール、ロボットのデータを管理するクラス """
    def __init__(self, config_files: Dict[str, str]):
        """
        設定ファイルを読み込み、データを管理する。

        :param config_files: 設定ファイルのパスを格納した辞書
        """
        self._task_config = OmegaConf.load(config_files["task"])
        self._module_type_config = OmegaConf.load(config_files["module_type"])
        self._robot_type_config = OmegaConf.load(config_files["robot_type"])
        self._module_config = OmegaConf.load(config_files["module"])
        self._robot_config = OmegaConf.load(config_files["robot"])

    def load_module_types(self) -> Dict[str, ModuleType]:
        """ モジュールタイプを読み込む """
        return {
            type_name: ModuleType(name=type_name, max_battery=type_data["max_battery"])
            for type_name, type_data in self._module_type_config.items()
        }

    def load_robot_types(self, module_types: Dict[str, ModuleType]) -> Dict[str, RobotType]:
        """ ロボットタイプを読み込む """
        robot_types = {}
        for type_name, type_data in self._robot_type_config.items():
            required_modules = {}
            for module_name, count in type_data["required_modules"].items():
                if module_name not in module_types:
                    raise ValueError(f"Unknown module type: {module_name}")
                required_modules[module_types[module_name]] = count
            performance = {}
            for name, value in type_data["performance"].items():
                if name not in RobotPerformanceAttributes.__members__:
                    raise ValueError(f"Unknown performance attribute: {name}")
                performance[RobotPerformanceAttributes[name]] = value
            robot_types[type_name] = RobotType(
                name=type_name,
                required_modules=required_modules,
                performance=performance,
                power_consumption=type_data["power_consumption"]
            )
        return robot_types

    def load_tasks(self) -> Dict[str, Task]:
        """ タスクを読み込む """
        task_classes = find_subclasses_by_name(Task)
        tasks = {}
        for task_name, task_data in self._task_config.items():
            task_class = task_classes.get(task_data["class"])
            if task_class is None:
                raise ValueError(f"Unknown task class: {task_data['class']}")
            task_dependency = []
            for dep_name in task_data["dependencies"]:
                if dep_name not in tasks:
                    raise ValueError(f"Unknown task dependency: {dep_name}")
                task_dependency.append(tasks[dep_name])
            required_performance = {}
            for name, value in task_data["required_performance"].items():
                if name not in RobotPerformanceAttributes.__members__:
                    raise ValueError(f"Unknown performance attribute: {name}")
                required_performance[RobotPerformanceAttributes[name]] = value
            # タスクの割り当てられたロボットを取得
            arguments_to_ignore = get_class_init_args(Task)
            tasks[task_name] = task_class(
                name=task_name,
                coordinate=np.array(task_data['coordinate']),
                total_workload=task_data["total_workload"],
                completed_workload=task_data["completed_workload"],
                task_dependency=task_dependency,
                required_performance=required_performance,
                other_attrs=task_data['other_attrs'],
                **{k: v for k, v in task_data.items() if k not in arguments_to_ignore}
            )
        return tasks

    def load_modules(self, module_types: Dict[str, ModuleType]) -> Dict[str, Module]:
        """ モジュールを読み込む """
        modules = {}
        for module_id, module_data in self._module_config.items():
            module_type = module_types.get(module_data["module_type"])
            if module_type is None:
                raise ValueError(f"Unknown module type: {module_data['module_type']}")
            modules[module_id] = Module(
                module_type=module_type,
                name=module_id,
                coordinate=tuple(module_data["coordinate"]),
                battery=module_data["battery"],
                state=ModuleState[module_data["state"]]
            )
        return modules

    def load_robots(self, robot_types: Dict[str, RobotType], modules: Dict[str, Module], 
                    tasks: Dict[str, Task]) -> Dict[str, Robot]:
        """ ロボットを読み込む """
        robots = {}
        for robot_id, robot_data in self._robot_config.items():
            robot_type = robot_types.get(robot_data["robot_type"])
            if robot_type is None:
                raise ValueError(f"Unknown robot type: {robot_data['robot_type']}")
            component = []
            for module_name in robot_data["components"]:
                if module_name not in modules:  # 存在しないモジュールはエラーを発生させる
                    raise ValueError(f"Unknown module: {module_name}")
                component.append(modules[module_name])
            task_priority = []
            for task_name in robot_data["task_priority"]:
                if task_name not in tasks:  # 存在しないタスクはエラーを発生させる
                    raise ValueError(f"Unknown task: {task_name}")
                task_priority.append(tasks[task_name])

            def is_valid_permutation(original: list, permuted: list) -> bool:
                """ 配列の順列が正しく作成されているかチェックする """
                counter_original = Counter(original)
                counter_permuted = Counter(permuted)
                return counter_original == counter_permuted and all(count == 1 for count in counter_original.values())
            
            if not is_valid_permutation(robot_data["task_priority"], task_priority):
                raise ValueError(f"Invalid task priority: {robot_data['task_priority']}")
            
            robots[robot_id] = Robot(
                robot_type=robot_type,
                name=robot_id,
                coordinate=tuple(robot_data["coordinate"]),
                component=component,
                task_priority=task_priority
            )
        return robots

# # 文字列を対応するEnumメンバーに変換する
# def str_to_enum(enum_class, name):
#     """
#     文字列から対応する Enum メンバーを取得する。

#     :param enum_class: 変換対象の Enum クラス
#     :param name: 変換したい文字列
#     :return: 一致する Enum メンバー, 一致しない場合は None
#     """
#     try:
#         return enum_class[name]
#     except KeyError:
#         return None  # 該当するEnumメンバーがない場合はNoneを返す

# # タスク，モジュール，ロボットの状態の読み込み・管理を行うクラス
# class Manager:
#     def __init__(self, properties):
#         """
#         設定ファイルを読み込み、タスク・モジュール・ロボットの情報を管理する。

#         :param properties: 設定ファイルのパスを格納したオブジェクト
#         """
#         self._properties = properties  # プロパティ（設定ファイルのパスなど）
#         self._task_config = OmegaConf.load(self._properties.taskConfigFile)  # タスク設定を読み込む
#         self._module_type_config = OmegaConf.load(self._properties.moduleTypeConfigFile) # モジュールタイプ設定を読み込む
#         self._robot_type_config = OmegaConf.load(self._properties.robotTypeConfigFile)  # ロボットタイプ設定を読み込む
#         self._module_config = OmegaConf.load(self._properties.moduleConfigFile) # モジュール設定を読み込む
#         self._robot_config = OmegaConf.load(self._properties.robotConfigFile) # ロボット設定を読み込む

#     def read_task(self) -> Dict[str, Task]:
#         """
#         タスク情報を読み込み、Task オブジェクトを作成する。

#         :param robots: ロボット情報の辞書
#         :return: タスク名をキー、Task オブジェクトを値とする辞書
#         """
#         tasks = {}

#         # タスククラスのマッピングを取得
#         task_classes = find_subclasses_by_name(Task)

#         for task_name, task_data in self._task_config.items():
#             task_class = task_classes.get(task_data['class'])  # タスクのクラスを取得

#             if task_class is None:
#                 raise ValueError(f"Unknown work category: {task_data['class']}")  # 不明なタスククラスのエラー

#             # 依存タスクを取得
#             task_dependency = [tasks[task_name_d] for task_name_d in task_data['task_dependency']]

#             # 必要なロボット能力を取得
#             required_performance = {
#                 str_to_enum(RobotPerformanceAttributes, name): req
#                 for name, req in task_data['required_performance'].items()
#                 if str_to_enum(RobotPerformanceAttributes, name) is not None
#             }

#             # 待機ロボットを初期化
#             deployed_robot = []

#             # タスククラスのインスタンスを生成
#             task = task_class(
#                 name=task_name,
#                 coordinate=np.array(task_data['coordinate']),
#                 total_workload=task_data['workload'][0],
#                 completed_workload=task_data['workload'][1],
#                 task_dependency=task_dependency,
#                 required_performance=required_performance,
#                 deployed_robot=deployed_robot,
#                 other_attrs=task_data['other_attrs'],
#                 **{k: v for k, v in task_data.items() if k not in [
#                     'class', 'coordinate', 'workload', 'task_dependency', 'required_performance', 'deployed_robot', 'other_attrs'
#                 ]}
#             )

#             tasks[task_name] = task

#         return tasks
    
#     def read_module_type(self) -> Dict[str, ModuleType]:
#         """
#         モジュールタイプ情報を読み込む。

#         :return: モジュールタイプ名をキー、ModuleType オブジェクトを値とする辞書
#         """
#         return {
#             type_name: ModuleType(name=type_name, max_battery=type_data["max_battery"])
#             for type_name, type_data in self._module_type_config.items()
#         }

#     def read_robot_type(self, module_types) -> Dict[str, RobotType]:
#         """
#         ロボットタイプ情報を読み込み、RobotType オブジェクトを作成する。

#         :param module_types: モジュールタイプの辞書
#         :return: ロボットタイプ名をキー、RobotType オブジェクトを値とする辞書
#         """
#         robot_types = {}

#         for type_name, type_data in self._robot_type_config.items():
#             required_modules = {
#                 module_types[module_type_name]: req
#                 for module_type_name, req in type_data['required_modules'].items()
#                 if module_type_name in module_types
#             }

#             performance = {
#                 str_to_enum(RobotPerformanceAttributes, name): value
#                 for name, value in type_data['performance'].items()
#                 if str_to_enum(RobotPerformanceAttributes, name) is not None
#             }

#             robot_types[type_name] = RobotType(
#                 name=type_name,
#                 required_modules=required_modules,
#                 performance=performance,
#                 redundancy=None
#             )

#         return robot_types

#     def read_module(self, module_types) -> Dict[str, Module]:
#         """
#         モジュール情報を読み込む。

#         :param module_types: モジュールタイプの辞書
#         :return: モジュールIDをキー、Module オブジェクトを値とする辞書
#         """
#         modules = {}

#         for module_id, module_data in self._module_config.items():
#             module_type = module_types.get(module_data['module_type'])

#             if module_type is None:
#                 raise ValueError(f"Unknown module category: {module_data['module_type']}")

#             modules[module_id] = Module(
#                 type=module_type,
#                 name=module_id,
#                 coordinate=np.array(tuple(module_data['coordinate']))
#             )

#         return modules

#     def read_robot(self, robot_types, modules, tasks) -> Dict[str, Robot]:
#         """
#         ロボット情報を読み込み、Robot オブジェクトを作成する。

#         :param robot_types: ロボットタイプの辞書
#         :param modules: モジュールの辞書
#         :return: ロボットIDをキー、Robot オブジェクトを値とする辞書
#         """
#         robots = {}

#         for robot_id, robot_data in self._robot_config.items():
#             robot_type = robot_types.get(robot_data['robot_type'])

#             if robot_type is None:
#                 raise ValueError(f"Unknown robot category: {robot_data['robot_type']}")

#             component = [modules[module_name] for module_name in robot_data['component']]
#             task_priority = [tasks[task_name] for task_name in robot_data['task_priority']]

#             robots[robot_id] = Robot(
#                 type=robot_type,
#                 name=robot_id,
#                 coordinate=np.array(tuple(robot_data['coordinate'])),
#                 component=component,
#                 task_priority=task_priority
#             )

#         return robots
