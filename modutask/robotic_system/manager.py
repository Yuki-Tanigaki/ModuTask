from omegaconf import OmegaConf
from typing import Dict, List, Tuple, Type
from collections import Counter
import copy
import pandas as pd
import numpy as np

from .core import *

# クラスを動的に探索し、クラス名に基づいて辞書にマッピングするヘルパー関数
def find_subclasses_by_name(base_class: Type) -> Dict[str, Type]:
    subclasses = {}
    # base_classのすべてのサブクラスを取得
    for cls in base_class.__subclasses__():
        subclasses[cls.__name__] = cls  # クラス名 (__name__) をキーとして辞書に登録
    return subclasses

# 入力名に対応するEnumメンバーに変換する
def str_to_enum(enum_class, name):
    try:
        return enum_class[name]
    except KeyError:
        return None  # 該当するEnumメンバーがない場合はNoneを返す

# タスク，モジュール，ロボットの状態の読み込み書き出しマネージャー
class Manager:
    def __init__(self, properties):
        self._properties = properties  # プロパティ（設定ファイルのパスなど）
        self._task_config = OmegaConf.load(self._properties.taskConfigFile)  # タスク設定ファイルを読み込む
        self._module_type_config = OmegaConf.load(self._properties.moduleTypeConfigFile) # モジュールタイプ設定ファイルを読み込む
        self._robot_type_config = OmegaConf.load(self._properties.robotTypeConfigFile)  # ロボットタイプ設定ファイルを読み込む
        self._module_config = OmegaConf.load(self._properties.moduleConfigFile) # モジュール設定ファイルを読み込む
        self._robot_config = OmegaConf.load(self._properties.robotConfigFile) # ロボット設定ファイルを読み込む

    def read_task(self) -> Dict[str, Task]:
        tasks = {}

        # タスクカテゴリーとクラスの対応関係を動的に探索
        task_classes = find_subclasses_by_name(Task)

        # 各タスクの設定を解析し、対応する Task オブジェクトを動的に生成
        for task_name, task_data in self._task_config.items():
            # Transport or Manufacture
            task_class = task_classes.get(task_data['class'])  # タスクに対応するクラスを取得

            if task_class is None:
                raise ValueError(f"Unknown work category: {task_data['class']}")  # 不明な作業カテゴリの場合はエラーを投げる

            task_dependency = []
            for task_name_d in task_data['task_dependency']:
                task_dependency.append(tasks[task_name_d])

            required_abilities = {}
            for performance_name, req in task_data['required_abilities'].items():
                performance_enum = str_to_enum(RobotPerformanceAttributes, performance_name)
                if performance_enum is not None:
                    required_abilities[performance_enum] = req

            # 動的にタスククラスをインスタンス化
            task = task_class(
                name=task_name, # 名前
                coordinate=np.array(task_data['coordinate']),   # タスクの座標
                workload=task_data['workload'],  # 仕事量[全体, 完了済み]
                task_dependency=task_dependency,  # 依存するタスクのリスト
                required_abilities=required_abilities, # タスクを実行するために必要な合計パフォーマンス
                other_attrs=task_data['other_attrs'], # 任意の追加情報
                **{k: v for k, v in task_data.items() if k not in ['class', 'coordinate', 'workload', 'task_dependency', 'required_abilities', 'other_attrs']}
            )

            tasks[task_name] = task # タスクを追加

        return tasks
    
    def read_module_type(self) -> Dict[str, ModuleType]:
        module_types = {}
        for type_name, type_data in self._module_type_config.items():
            module_types[type_name] = ModuleType(name=type_name, max_battery=type_data["max_battery"])
        
        return module_types
    
    def read_robot_type(self, module_types) -> Dict[str, RobotType]:
        robot_types = {}
        for type_name, type_data in self._robot_type_config.items():
            required_modules = {}
            for module_type_name, req in type_data['required_modules'].items():
                module_type = module_types.get(module_type_name)
                if module_type is None:
                    raise ValueError(f"Unknown module category: {module_type_name}")
                required_modules[module_type] = req

            performance = {}
            for performance_name, stuts in type_data['performance'].items():
                performance[str_to_enum(RobotPerformanceAttributes, performance_name)] = stuts

            robot_types[type_name] = RobotType(name=type_name, required_modules=required_modules, performance=performance, redundancy=None)
        
        return robot_types

    def read_module(self, module_types) -> Dict[str, Module]:
        modules = {}
        for module_id, module_data in self._module_config.items():
            module_type_name = module_data['module_type']  # モジュールカテゴリ
            module_type = module_types.get(module_type_name)
            if module_type is None:
                raise ValueError(f"Unknown module category: {module_type_name}")

            if module_type is None:
                raise ValueError(f"Unknown module category: {module_type_name}")  # 不明なモジュールカテゴリの場合はエラーを投げる

            module = Module(
                type=module_type,
                name=module_id,
                coordinate=np.array(tuple(module_data['coordinate'])),
            )

            modules[module_id] = module  # モジュールを辞書に追加
        return modules  # モジュールの辞書を返す

    def read_robot(self, robot_types, modules) -> Dict[str, Robot]:
        robots = {}
        for robot_id, robot_data in self._robot_config.items():
            robot_type_name = robot_data['robot_type']  # ロボットカテゴリ
            robot_type = robot_types.get(robot_type_name)
            if robot_type is None:
                raise ValueError(f"Unknown robot category: {robot_type_name}")

            if robot_type is None:
                raise ValueError(f"Unknown module category: {robot_type_name}")  # 不明なモジュールカテゴリの場合はエラーを投げる

            component = []
            for module_name in robot_data['component']:
                component.append(modules[module_name])

            robot = Robot(
                type=robot_type,
                name=robot_id,
                coordinate=np.array(tuple(robot_data['coordinate'])),
                component=component
            )

            robots[robot_id] = robot  # ロボットを辞書に追加
        return robots  # ロボットの辞書を返す
    