from omegaconf import OmegaConf
from typing import Dict, List, Tuple, Type
from collections import Counter
import copy
import pandas as pd
import numpy as np

from .core import *

# クラスを動的に探索し、クラス名に基づいて辞書にマッピングするヘルパー関数
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

# 文字列を対応するEnumメンバーに変換する
def str_to_enum(enum_class, name):
    """
    文字列から対応する Enum メンバーを取得する。

    :param enum_class: 変換対象の Enum クラス
    :param name: 変換したい文字列
    :return: 一致する Enum メンバー, 一致しない場合は None
    """
    try:
        return enum_class[name]
    except KeyError:
        return None  # 該当するEnumメンバーがない場合はNoneを返す

# タスク，モジュール，ロボットの状態の読み込み・管理を行うクラス
class Manager:
    def __init__(self, properties):
        """
        設定ファイルを読み込み、タスク・モジュール・ロボットの情報を管理する。

        :param properties: 設定ファイルのパスを格納したオブジェクト
        """
        self._properties = properties  # プロパティ（設定ファイルのパスなど）
        self._task_config = OmegaConf.load(self._properties.taskConfigFile)  # タスク設定を読み込む
        self._module_type_config = OmegaConf.load(self._properties.moduleTypeConfigFile) # モジュールタイプ設定を読み込む
        self._robot_type_config = OmegaConf.load(self._properties.robotTypeConfigFile)  # ロボットタイプ設定を読み込む
        self._module_config = OmegaConf.load(self._properties.moduleConfigFile) # モジュール設定を読み込む
        self._robot_config = OmegaConf.load(self._properties.robotConfigFile) # ロボット設定を読み込む

    def read_task(self) -> Dict[str, Task]:
        """
        タスク情報を読み込み、Task オブジェクトを作成する。

        :param robots: ロボット情報の辞書
        :return: タスク名をキー、Task オブジェクトを値とする辞書
        """
        tasks = {}

        # タスククラスのマッピングを取得
        task_classes = find_subclasses_by_name(Task)

        for task_name, task_data in self._task_config.items():
            task_class = task_classes.get(task_data['class'])  # タスクのクラスを取得

            if task_class is None:
                raise ValueError(f"Unknown work category: {task_data['class']}")  # 不明なタスククラスのエラー

            # 依存タスクを取得
            task_dependency = [tasks[task_name_d] for task_name_d in task_data['task_dependency']]

            # 必要なロボット能力を取得
            required_performance = {
                str_to_enum(RobotPerformanceAttributes, name): req
                for name, req in task_data['required_performance'].items()
                if str_to_enum(RobotPerformanceAttributes, name) is not None
            }

            # 待機ロボットを初期化
            deployed_robot = []

            # タスククラスのインスタンスを生成
            task = task_class(
                name=task_name,
                coordinate=np.array(task_data['coordinate']),
                total_workload=task_data['workload'][0],
                completed_workload=task_data['workload'][1],
                task_dependency=task_dependency,
                required_performance=required_performance,
                deployed_robot=deployed_robot,
                other_attrs=task_data['other_attrs'],
                **{k: v for k, v in task_data.items() if k not in [
                    'class', 'coordinate', 'workload', 'task_dependency', 'required_performance', 'deployed_robot', 'other_attrs'
                ]}
            )

            tasks[task_name] = task

        return tasks
    
    def read_module_type(self) -> Dict[str, ModuleType]:
        """
        モジュールタイプ情報を読み込む。

        :return: モジュールタイプ名をキー、ModuleType オブジェクトを値とする辞書
        """
        return {
            type_name: ModuleType(name=type_name, max_battery=type_data["max_battery"])
            for type_name, type_data in self._module_type_config.items()
        }

    def read_robot_type(self, module_types) -> Dict[str, RobotType]:
        """
        ロボットタイプ情報を読み込み、RobotType オブジェクトを作成する。

        :param module_types: モジュールタイプの辞書
        :return: ロボットタイプ名をキー、RobotType オブジェクトを値とする辞書
        """
        robot_types = {}

        for type_name, type_data in self._robot_type_config.items():
            required_modules = {
                module_types[module_type_name]: req
                for module_type_name, req in type_data['required_modules'].items()
                if module_type_name in module_types
            }

            performance = {
                str_to_enum(RobotPerformanceAttributes, name): value
                for name, value in type_data['performance'].items()
                if str_to_enum(RobotPerformanceAttributes, name) is not None
            }

            robot_types[type_name] = RobotType(
                name=type_name,
                required_modules=required_modules,
                performance=performance,
                redundancy=None
            )

        return robot_types

    def read_module(self, module_types) -> Dict[str, Module]:
        """
        モジュール情報を読み込む。

        :param module_types: モジュールタイプの辞書
        :return: モジュールIDをキー、Module オブジェクトを値とする辞書
        """
        modules = {}

        for module_id, module_data in self._module_config.items():
            module_type = module_types.get(module_data['module_type'])

            if module_type is None:
                raise ValueError(f"Unknown module category: {module_data['module_type']}")

            modules[module_id] = Module(
                type=module_type,
                name=module_id,
                coordinate=np.array(tuple(module_data['coordinate']))
            )

        return modules

    def read_robot(self, robot_types, modules, tasks) -> Dict[str, Robot]:
        """
        ロボット情報を読み込み、Robot オブジェクトを作成する。

        :param robot_types: ロボットタイプの辞書
        :param modules: モジュールの辞書
        :return: ロボットIDをキー、Robot オブジェクトを値とする辞書
        """
        robots = {}

        for robot_id, robot_data in self._robot_config.items():
            robot_type = robot_types.get(robot_data['robot_type'])

            if robot_type is None:
                raise ValueError(f"Unknown robot category: {robot_data['robot_type']}")

            component = [modules[module_name] for module_name in robot_data['component']]
            task_priority = [tasks[task_name] for task_name in robot_data['task_priority']]

            robots[robot_id] = Robot(
                type=robot_type,
                name=robot_id,
                coordinate=np.array(tuple(robot_data['coordinate'])),
                component=component,
                task_priority=task_priority
            )

        return robots
