from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any
from enum import Enum
import math, copy
import numpy as np

# モジュールの状態表現
class ModuleState(Enum):
    ACTIVE = (0, 'green') # 何れかのロボットの一部
    SPARE = (1, 'limegreen') # 何れかのロボットの一部
    MALFUNCTION = (2, 'gray') # 故障中

# ロボットの状態表現
class RobotState(Enum):
    IDLE = (0, 'green') # 待機中
    MOVE = (1, 'blue') # 移動中
    CHARGE = (2, 'orange') # 充電中
    READY = (3, 'pink')
    WORK = (4, 'red') # 仕事中
    INACTIVE = (5, 'gray') # 部品不足

    # プロパティで色を取得
    @property
    def color(self):
        return self.value[1]

# ロボットの能力カテゴリ
class RobotPerformanceAttributes(Enum):
    TRANSPORT = 0 # 運搬能力
    MANUFACTURE = 1 # 加工能力
    MOBILITY = 2 # 移動能力

# タスク
@dataclass
class Task:
    name: str # 名前
    coordinate: Tuple[float, float]  # タスクの座標
    workload: Tuple[float, float]  # 仕事量[全体, 完了済み]
    task_dependency: List["Task"]  # 依存するタスクのリスト
    required_abilities: Dict[RobotPerformanceAttributes, int] # タスクを実行するために必要な合計パフォーマンス
    other_attrs: Dict[str, Any] # 任意の追加情報

# 運搬タスク
@dataclass
class Transport(Task):
    origin_destination: Tuple[Tuple[float, float], Tuple[float, float], float] # 出発地点, 目的地, 移動速度に対する補正値(0.5=速度半分)

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

    # 完了済み仕事量の更新: 総移動距離に対する移動割合
    def update(self):
        # タスク位置を移動
        # 働くロボットのうち最も遅いロボットの速度×補正値
        self._travel(self.origin_destination[2])
        total_dist = self._calculate_distance(self.origin_destination[0], self.origin_destination[1])
        current_dist = self._calculate_distance(self.origin_destination[0], self.coordinate)
        self.workload[1] = self.workload[0]*(current_dist/total_dist)

# 加工タスク
@dataclass
class Manufacture(Task):
    # 完了済み仕事量の更新: 呼び出されるたびに+1
    def update(self):
        self.workload[1] += 1

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
    ability: Dict[RobotPerformanceAttributes, int] # 能力値
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
