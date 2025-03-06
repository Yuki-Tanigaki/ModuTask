from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any
from enum import Enum
import math, copy
import numpy as np

# モジュールの状態表現
class ModuleState(Enum):
    """ モジュールの状態を表す列挙型 """
    ACTIVE = (0, 'green')  # 使用中
    SPARE = (1, 'limegreen')  # 予備
    MALFUNCTION = (2, 'gray')  # 故障中

    @property
    def color(self):
        """ モジュールの状態に対応する色を取得 """
        return self.value[1]

# ロボットの状態表現
class RobotState(Enum):
    """ ロボットの状態を表す列挙型 """
    IDLE = (0, 'green')  # 待機中
    MOVE = (1, 'blue')  # 移動中
    CHARGE = (2, 'orange')  # 充電中
    DEPLOYED = (3, 'pink')  # 待機中
    WORK = (4, 'red')  # 仕事中
    INACTIVE = (5, 'gray')  # 部品不足

    @property
    def color(self):
        """ ロボットの状態に対応する色を取得 """
        return self.value[1]

# ロボットの能力カテゴリ
class RobotPerformanceAttributes(Enum):
    """ ロボットの能力カテゴリを表す列挙型 """
    TRANSPORT = 0  # 運搬能力
    MANUFACTURE = 1  # 加工能力
    MOBILITY = 2  # 移動能力

# タスクの基底クラス
@dataclass
class Task(ABC):
    """ タスクを表す抽象基底クラス """
    name: str  # タスク名
    coordinate: Tuple[float, float]  # タスクの座標
    total_workload: float  # タスクの総仕事量
    completed_workload: float  # 完了済み仕事量
    task_dependency: List["Task"]  # 依存するタスクのリスト
    required_performance: Dict[RobotPerformanceAttributes, int]  # タスク実行に必要なロボット能力
    deployed_robot: List["Robot"]  # タスク実行に参加しているロボット
    other_attrs: Dict[str, Any]  # その他の属性

    def check_dependencies_completed(self) -> bool:
        """ 依存するタスクがすべて完了しているかを確認する """
        return all(dep.completed_workload >= dep.total_workload for dep in self.task_dependency)

    def check_deployed_performance(self) -> bool:
        """ 配置されたロボットが必要なパフォーマンスを満たしているか確認 """
        deployed_performance = {attr: 0 for attr in RobotPerformanceAttributes}
        for robot in self.deployed_robot:
            for attr, value in robot.type.performance.items():
                deployed_performance[attr] += value

        return all(deployed_performance[attr] >= req for attr, req in self.required_performance.items())

    @abstractmethod
    def update(self) -> float:
        """ タスクが実行されたときの仕事量の増加を計算 """
        pass

# 運搬タスク
@dataclass
class Transport(Task):
    """ 運搬タスクのクラス """
    origin_destination: Tuple[Tuple[float, float], Tuple[float, float], float]  # (出発地点, 目的地, 移動補正値)

    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """ 2点間の距離を計算する """
        return math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)

    def _travel(self, mobility: float):
        """ ロボットの移動処理 """
        target_coordinate = np.array(self.origin_destination[1])
        v = target_coordinate - np.array(self.coordinate)
        if np.linalg.norm(v) < mobility:
            self.coordinate = copy.deepcopy(target_coordinate)
        else:
            self.coordinate = np.copy(self.coordinate + mobility * v / np.linalg.norm(v))

    def update(self):
        """ タスクの進捗を更新 """
        if not self.deployed_robot or not self.check_dependencies_completed():
            return 0.0  # 実行不可

        mobility_values = [robot.type.performance.get(RobotPerformanceAttributes.MOBILITY, 0) for robot in self.deployed_robot]
        if not mobility_values or max(mobility_values) == 0:
            return 0.0  # 移動能力なし

        min_mobility = min(mobility_values)
        adjusted_mobility = min_mobility * self.origin_destination[2]
        
        before_position = np.array(self.coordinate)
        self._travel(adjusted_mobility)
        after_position = np.array(self.coordinate)

        distance_traveled = np.linalg.norm(after_position - before_position)
        self.completed_workload += distance_traveled

# 加工タスク
@dataclass
class Manufacture(Task):
    """ 加工タスクのクラス """
    def update(self):
        """ タスクの進捗を更新（呼び出されるごとに+1） """
        if not self.deployed_robot or not self.check_dependencies_completed():
            return
        self.completed_workload += 1

# モジュールのタイプ
@dataclass
class ModuleType:
    """ モジュールの種類 """
    name: str  # モジュール名
    max_battery: float  # 最大バッテリー容量

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, ModuleType) and self.name == other.name

# モジュール
@dataclass
class Module:
    """ モジュールのクラス """
    type: ModuleType
    name: str
    coordinate: Tuple[float, float]
    battery: Tuple[float, float] = field(init=False)
    state: ModuleState = ModuleState.SPARE

    def __post_init__(self):
        """ 初期化時にバッテリーを設定 """
        self.battery = (self.type.max_battery, self.type.max_battery)

# ロボットのタイプ
@dataclass
class RobotType:
    """ ロボットの種類 """
    name: str
    required_modules: Dict[ModuleType, int]
    performance: Dict[RobotPerformanceAttributes, int]
    redundancy: Dict[Tuple[ModuleType, int], Dict[RobotPerformanceAttributes, int]]

# ロボット
@dataclass
class Robot:
    """ ロボットのクラス """
    type: RobotType
    name: str
    coordinate: Tuple[float, float]
    component: List[Module]
    state: RobotState = RobotState.INACTIVE

    def update_coordinate(self, coordinate: Tuple[float, float]):
        """ ロボットの座標を更新し、構成モジュールの座標も同期 """
        self.coordinate = copy.deepcopy(coordinate)
        for module in self.component:
            module.coordinate = copy.deepcopy(coordinate)
