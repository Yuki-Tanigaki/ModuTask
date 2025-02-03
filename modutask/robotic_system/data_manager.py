from omegaconf import OmegaConf
from typing import Dict, List, Tuple, Type
from typing import Type
from collections import Counter
import copy
import pandas as pd
import numpy as np

from .core import Task, Module, Robot, ModuleType, RobotType, RobotPerformanceAttributes, ModuleState

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
        self._robot_config = OmegaConf.load(self._properties.robotConfigFile) # モジュール設定ファイルを読み込む

    def read_task(self) -> Dict[str, Task]:
        tasks = {}

        # タスクカテゴリーとクラスの対応関係を動的に探索
        task_classes = find_subclasses_by_name(Task)

        # 各タスクの設定を解析し、対応する Task オブジェクトを動的に生成
        for task_name, task_data in self._task_config.items():
            # Transport or Manufacture
            task_class = task_classes.get(task_data['class'])  # タスクに対応するクラスを取得

            if task_class is None:
                raise ValueError(f"Unknown work category: {task_class}")  # 不明な作業カテゴリの場合はエラーを投げる

            task_dependency = []
            for task_name_d in task_data['task_dependency']:
                task_dependency.append(tasks[task_name_d])

            required_abilities = {}
            for ability_name, req in task_data['required_abilities'].items():
                required_abilities[str_to_enum(RobotPerformanceAttributes, ability_name)] = req

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
            module_types[type_name] = ModuleType(name=type_name, max_battery=type_data.max_battery)
        
        return module_types
    
    def read_robot_type(self, module_types) -> Dict[str, RobotType]:
        robot_types = {}
        for type_name, type_data in self._robot_type_config.items():
            required_modules = {}
            for module_type_name, req in type_data['required_modules'].items():
                required_modules[module_types[module_type_name]] = req

            ability = {}
            for ability_name, stuts in type_data['ability'].items():
                ability[str_to_enum(RobotPerformanceAttributes, ability_name)] = stuts

            robot_types[type_name] = RobotType(name=type_name, required_modules=required_modules, ability=ability, redundancy=None)
        
        return robot_types


    def read_module(self, module_types) -> Dict[str, Module]:
        modules = {}
        for module_id, module_data in self._module_config.items():
            module_type_name = module_data['module_type']  # モジュールカテゴリ
            module_type = module_types[module_type_name]  # 対応するクラスを取得

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
            robot_type = robot_types[robot_type_name]  # 対応するクラスを取得

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
    
    def find_robot_category(self, module_count):
        # モジュール要件を満たしているかチェック
        candidate = None
        for _, robot_category in self.robot_categories.items():
            # 必要なモジュールをPandasの条件付きで一度にチェック
            required_modules = robot_category.required_modules
            conditions = (module_count[list(required_modules.keys())] >= pd.Series(required_modules))

            # 条件がすべてTrueならフラグを立てる
            if not conditions.values.all():
                continue
            if candidate is None:
                candidate = robot_category
            else:
                if candidate.priority > robot_category.priority:
                    candidate = robot_category
        return candidate
    
    def build_robot(self, robot_category, component, modules):
        # コンポーネントの位置から多数決でロボットの位置を仮想的に設定
        coordinate_list = []
        for moduleName in component:
            coordinate_list.append(tuple(modules[moduleName].coordinate))
            modules[moduleName].state = ModuleState.ACTIVE
        counter = Counter(coordinate_list)
        most_common, _ = counter.most_common(1)[0]

        # すべてのパーツがロボットの現在位置にあるかチェック
        active = all(len(t) == len(most_common) and all(abs(x - y) < 1e-9 for x, y in zip(t, most_common)) for t in coordinate_list)
        # バッテリーが残っているかチェック
        battery = 0
        for moduleName in component:
            battery += modules[moduleName].battery
        if battery == 0:
            active = False

        return robot_category(
            coordinate = copy.deepcopy(most_common),
            required_modules=robot_category.required_modules,
            priority=robot_category.priority,
            transport=robot_category.transport,
            manufacture=robot_category.manufacture,
            mobility=robot_category.mobility,
            redundancy=robot_category.redundancy,
            component=component,
            active=active
        )

        

    # def define_robot(self, module_allocation, module_count, max_robot):
    #     # 各ロボットを定義
    #     robots = []
    #     for i in range(max_robot): # i = max_robotは予備として使わないことを表すため+1しない
    #         # モジュール要件を満たしているかチェック
    #         candidate = None
    #         for category_name, robot_category in self.robot_categories.items():
    #             # 必要なモジュールをPandasの条件付きで一度にチェック
    #             required_modules = robot_category.required_modules
    #             conditions = (module_count.loc[i, list(required_modules.keys())] >= pd.Series(required_modules))

    #             # 条件がすべてTrueならフラグを立てる
    #             if not conditions.all():
    #                 continue
    #             if candidate is None:
    #                 candidate = robot_category
    #             else:
    #                 if candidate.priority > robot_category.priority:
    #                     candidate = robot_category

    #         if candidate is None:
    #             continue

    #         # コンポーネントの位置から多数決でロボットの位置を仮想的に設定
    #         coordinate_list = []
    #         for _, module in module_allocation[i].items():
    #             # numpy.ndarray を tuple に変換
    #             coordinate_list.append(tuple(module.coordinate))
    #         counter = Counter(coordinate_list)
    #         most_common, _ = counter.most_common(1)[0]

    #         # すべてのパーツがロボットの現在位置にあるかチェック
    #         active = all(len(t) == len(most_common) and all(abs(x - y) < 1e-9 for x, y in zip(t, most_common)) for t in coordinate_list)

    #         # componentからrequired_modules以外のモジュールを算出
    #         # componentの先頭から順に使っていく
    #         # どのモジュールがどれだけ必要か
    #         rest_required_modules = copy.deepcopy(candidate.required_modules) 
    #         component_state = {}
    #         for moduleName, module in module_allocation[i].items():
    #             if rest_required_modules[type(module).__name__] == 0:
    #                 component_state[moduleName] = ModuleState.Spare
    #                 continue
    #             rest_required_modules[type(module).__name__] += -1
    #             component_state[moduleName] = ModuleState.IN_USE
                
    #         robot = candidate(
    #             coordinate = copy.deepcopy(most_common),
    #             required_modules=candidate.required_modules,
    #             priority=candidate.priority,
    #             transport=candidate.transport,
    #             manufacture=candidate.manufacture,
    #             mobility=candidate.mobility,
    #             component=module_allocation[i],
    #             component_state=component_state,
    #             active=active
    #         )

    #         robots.append(robot)

    #     return robots