from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any
from enum import Enum
import math, copy
import numpy as np

# モジュールの状態表現
class ModuleState(Enum):
    ACTIVE = (0, 'green') # 使用中
    SPARE = (1, 'limegreen') # 予備
    MALFUNCTION = (2, 'gray') # 故障中

    # プロパティで色を取得
    @property
    def color(self):
        return self.value[1]

# ロボットの状態表現
class RobotState(Enum):
    IDLE = (0, 'green') # 待機中
    MOVE = (1, 'blue') # 移動中
    CHARGE = (2, 'orange') # 充電中
    DEPLOYED = (3, 'pink') # 待機中
    WORK = (4, 'red') # 仕事中
    INACTIVE = (5, 'gray') # 部品不足

    # プロパティで色を取得
    @property
    def color(self):
        return self.value[1]

# ロボットの能力カテゴリ
class RobotPerformanceAttributes(Enum):
    TRANSPORT = 0 # 運搬能力（荷物の移動に使える余剰トルクを表現）
    MANUFACTURE = 1 # 加工能力（マニピュレータによる部品の取付などの能力を表現）
    MOBILITY = 2 # 移動能力（ロボット単体の移動能力を表現）

# タスク
@dataclass
class Task(ABC):
    name: str # 名前
    coordinate: Tuple[float, float]  # タスクの座標
    total_workload: float # 全体仕事量
    completed_workload: float # 完了済み仕事量
    task_dependency: List["Task"]  # 開始条件となるタスクのリスト（完了済みである必要がある）
    required_performance: Dict[RobotPerformanceAttributes, int] # タスクを実行するために必要な合計パフォーマンス
    deployed_robot: List["Robot"] # タスク実行のために待機済みのロボット
    other_attrs: Dict[str, Any] # 任意の追加情報

    def check_dependencies_completed(self) -> bool:
        """
        タスクの依存タスクがすべて完了済みか確認する関数
        :return: すべての依存タスクが完了していればTrue, そうでなければFalse
        """
        return all(dep.completed_workload >= dep.total_workload for dep in self.task_dependency)
    
    def check_deployed_performance(self) -> bool:
        """
        タスクを実行するために待機済みのロボットの合計能力が必要なパフォーマンスを満たしているか確認
        :return: 必要な能力を満たしていればTrue, そうでなければFalse
        """
        deployed_performance = {attr: 0 for attr in RobotPerformanceAttributes}

        # 待機中ロボットの能力値を合計
        for robot in self.deployed_robot:
            for attr, value in robot.type.performance.items():
                deployed_performance[attr] += value

        # すべての必要な能力を満たしているか確認
        return all(deployed_performance[attr] >= req for attr, req in self.required_performance.items())
    
    @abstractmethod
    def update(self) -> float:
        """
        このタスクが実行されたときに1ステップで増加する仕事量を計算する関数
        :return: 1ステップで増加する仕事量
        """
        pass

# 運搬タスク
@dataclass
class Transport(Task):
    origin_destination: Tuple[Tuple[float, float], Tuple[float, float], float] # 出発地点, 目的地, 移動能力に対する補正値(0.5=速度半分)

    # 2次元の距離計算
    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        x1, y1 = point1
        x2, y2 = point2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    # 移動
    def _travel(self, mobijity: float): 
        target_coordinate = np.array(self.origin_destination[1])
        v = np.array(target_coordinate) - np.array(self.coordinate)
        if np.linalg.norm(v) < mobijity:  # 距離が移動能力以下
            self.coordinate = copy.deepcopy(target_coordinate)
        else:
            self.coordinate = np.copy(self.coordinate + mobijity*v/np.linalg.norm(v))

    # 完了済み仕事量の更新
    def update(self):
        """
        待機中のロボットのうち最も移動能力が低いロボットを特定
        そのロボットの移動能力値に補正を行う
        補正後の能力値でtravel()
        移動距離をcompleted_workloadに加算
        """
        if not self.deployed_robot or not self.check_dependencies_completed():
            return 0.0  # ロボットがいない、または依存タスクが完了していない場合は何もしない

        # すべての待機中ロボットの移動能力を取得
        mobility_values = [
            robot.type.performance.get(RobotPerformanceAttributes.MOBILITY, 0)
            for robot in self.deployed_robot
        ]

        if not mobility_values or max(mobility_values) == 0:
            return 0.0  # 移動能力を持つロボットがいない場合は何もしない

        # 最も移動能力が低いロボットの移動能力を取得
        min_mobility = min(mobility_values)

        # 移動能力に補正を適用
        adjusted_mobility = min_mobility * self.origin_destination[2]

        # 移動を実行
        before_position = np.array(self.coordinate)
        self._travel(adjusted_mobility)
        after_position = np.array(self.coordinate)

        # 移動距離を計算して completed_workload に加算
        distance_traveled = np.linalg.norm(after_position - before_position)
        self.completed_workload += distance_traveled

# 加工タスク
@dataclass
class Manufacture(Task):
    # 完了済み仕事量の更新: 呼び出されるたびに+1
    def update(self):
        if not self.deployed_robot or not self.check_dependencies_completed():
            return # ロボットがいない、または依存タスクが完了していない場合は何もしない
        self.completed_workload += 1

# モジュールのタイプ
@dataclass
class ModuleType:
    name: str # 名前
    max_battery: float  # バッテリー最大量

    # 一意性を定義するプロパティに基づくハッシュ
    def __hash__(self):
        return hash(self.name)

    # ハッシュ関数と一貫性のある平等性を確保する
    def __eq__(self, other):
        if isinstance(other, ModuleType):
            return self.name == other.name
        return False

# モジュール
@dataclass
class Module:
    type: ModuleType # モジュールのタイプ
    name: str # 名前
    coordinate: Tuple[float, float]  # モジュールの座標
    battery: Tuple[float, float]=field(init=False)  # バッテリー[最大量, 残量]
    state: ModuleState=ModuleState.SPARE # デフォルトは予備

    # dataclassのフィールドがすべて初期化された後に呼び出される
    def __post_init__(self):
        # typeのmax_batteryを使ってbatteryを初期化
        self.battery = (self.type.max_battery, self.type.max_battery)

# ロボットのタイプ
@dataclass
class RobotType:
    name: str # 名前
    required_modules: Dict[ModuleType, int]  # 必要モジュール数
    performance: Dict[RobotPerformanceAttributes, int] # 能力値
    redundancy: Dict[Tuple[ModuleType, int], Dict[RobotPerformanceAttributes, int]] # 各モジュールの故障数に対して変化できるロボットタイプ

# ロボット
@dataclass
class Robot:
    type: RobotType # ロボットのタイプ
    name: str # 名前
    coordinate: Tuple[float, float]  # ロボットの座標
    component: List[Module]
    state: RobotState=RobotState.INACTIVE # デフォルトは待機

    def update_coordinate(self, coordinate: Tuple[float, float]):
        self.coordinate = copy.deepcopy(coordinate)
        for module in self.component:
            module.coordinate = copy.deepcopy(coordinate)
