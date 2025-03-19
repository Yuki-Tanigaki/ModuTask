from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Union
from enum import Enum
import math, copy
import numpy as np

class ModuleState(Enum):
    """ モジュールの状態を表す列挙型 """
    ACTIVE = (0, 'green')  # 正常
    ERROR = (1, 'gray')  # 故障
    
    @classmethod
    def from_value(cls, value):
        for state in cls:
            if state.value[0] == value:
                return state
        raise ValueError(f"{value} is not a valid ModuleState")
    
    @property
    def color(self):
        """ モジュールの状態に対応する色を取得 """
        return self.value[1]

class RobotState(Enum):
    """ ロボットの状態を表す列挙型 """
    IDLE = (0, 'green')  # 待機中
    MOVE = (1, 'blue')  # 移動中
    CHARGE = (2, 'orange')  # 充電中
    ASSIGNED = (3, 'pink')  # 配置中
    WORK = (4, 'red')  # 仕事中
    NO_ENERGY = (5, 'gray')  # バッテリー不足で稼働不可
    DEFECTIVE = (6, 'purple')  # 部品不足で稼働不可

    @property
    def color(self):
        """ ロボットの状態に対応する色を取得 """
        return self.value[1]

class RobotPerformanceAttributes(Enum):
    """ ロボットの能力カテゴリを表す列挙型 """
    TRANSPORT = 0  # 運搬能力
    MANUFACTURE = 1  # 加工能力
    MOBILITY = 2  # 移動能力

@dataclass
class ModuleType:
    """ モジュールの種類 """
    name: str  # モジュール名
    max_battery: float  # 最大バッテリー容量

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other: 'ModuleType') -> bool:
        return self.name == other.name

@dataclass
class RobotType:
    """ ロボットの種類 """
    name: str  # ロボット名
    required_modules: Dict[ModuleType, int]  # 構成に必要なモジュール数
    performance: Dict[RobotPerformanceAttributes, int]  # ロボットの各能力値
    power_consumption: float  # ロボットの消費電力

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other: 'ModuleType') -> bool:
        return self.name == other.name

class Task(ABC):
    """ タスクを表す抽象基底クラス """
    def __init__(self, name: str, coordinate: Tuple[float, float], total_workload: float, 
                 completed_workload: float, task_dependency: List["Task"], 
                 required_performance: Dict["RobotPerformanceAttributes", int], 
                 other_attrs: Dict[str, Any] = None):
        self._name = name  # タスク名
        self._coordinate = coordinate  # タスクの座標
        self._total_workload = total_workload  # タスクの総仕事量
        self._completed_workload = completed_workload  # 完了済み仕事量
        self._task_dependency = task_dependency  # 依存するタスクのリスト
        """
        タスクは複数のロボットの共同作業により実行される
        ロボットの合計能力値がrequired_performance以上の時、タスクは実行される
        """
        self._required_performance = required_performance  # タスク実行に要求される能力値
        self._assigned_robot = [] # タスクに配置済みのロボットのリスト（空で初期化）

        self._other_attrs = other_attrs if other_attrs is not None else {}  # 可視化用のタスク分類

    @property
    def name(self):
        return self._name

    @property
    def coordinate(self):
        return self._coordinate
    
    @property
    def total_workload(self):
        return self._total_workload
    
    @property
    def completed_workload(self):
        return self._completed_workload
    
    @property
    def task_dependency(self):
        return self._task_dependency

    @property
    def required_performance(self):
        return self._required_performance
    
    @property
    def assigned_robot(self):
        return self._assigned_robot
    
    @property
    def other_attrs(self):
        return self._other_attrs

    def __str__(self):
        """ タスクを文字列として表示（例: "タスク名[10/100]"）"""
        return f"{self.name}[{self.completed_workload}/{self.total_workload}]"

    def __repr__(self):
        """ デバッグ用の表現 """
        return f"Task(name={self.name}, completed={self.completed_workload}, total={self.total_workload})"

    def check_dependencies_completed(self) -> bool:
        """ 依存するタスクがすべて完了しているかを確認する """
        return all(dep.completed_workload >= dep.total_workload for dep in self.task_dependency)

    def check_assigned_performance(self) -> bool:
        """ 配置されたロボットが必要なパフォーマンスを満たしているか確認 """
        total_assigned_performance = {attr: 0 for attr in RobotPerformanceAttributes}
        for robot in self.assigned_robot:
            # ロボットの座標とタスクの座標が一致しているかチェック
            if robot.coordinate != self.coordinate:
                raise ValueError("Robot is not at the task location.")
            for attr, value in robot.type.performance.items():
                total_assigned_performance[attr] += value

        return all(total_assigned_performance[attr] >= req for attr, req in self.required_performance.items())

    def try_release_robot(self, robot: "Robot") -> bool:
        """ もしロボットが配置されているなら、リリース """
        if robot in self._assigned_robot:
            self._assigned_robot.remove(robot)
            return True
        return False

    def try_assign_robot(self, robot: "Robot") -> bool:
        """ ロボットを配置 """
        # RobotStateがDEFECTIVEでないことを確認
        if robot.state == RobotState.DEFECTIVE:
            return False
        # RobotStateがNO_ENERGYでないことを確認
        if robot.state == RobotState.NO_ENERGY:
            return False
        
        # ロボットの座標とタスクの座標が一致しているかチェック
        if robot.coordinate != self.coordinate:
            return False
        self._assigned_robot.append(robot)
        return True

    @abstractmethod
    def update(self) -> float:
        """ タスクが実行されたときの仕事量の増加を計算 """
        pass

class Transport(Task):
    """ 運搬タスクのクラス """
    def __init__(self, name: str, coordinate: Tuple[float, float], total_workload: float, 
                 completed_workload: float, task_dependency: List["Task"], 
                 required_performance: Dict["RobotPerformanceAttributes", int], 
                 origin_coordinate: Tuple[float, float], destination_coordinate: Tuple[float, float],
                 transportability: float, other_attrs = None):
        super().__init__(name, coordinate, total_workload, completed_workload, task_dependency, 
                         required_performance, other_attrs)
        self._origin_coordinate = origin_coordinate  # 出発地点座標
        self._destination_coordinate = destination_coordinate  # 目的地座標
        self._transportability = transportability  # 荷物の運搬のために低下する移動性能
    
    @property
    def origin_coordinate(self):
        return self._origin_coordinate
    
    @property
    def destination_coordinate(self):
        return self._destination_coordinate
    
    @property
    def transportability(self):
        return self._transportability

    def _travel(self, mobility: float) -> None:
        """ 荷物の移動処理 """
        target_coordinate = np.array(self.destination_coordinate)
        v = target_coordinate - np.array(self.coordinate)
        if np.linalg.norm(v) < mobility:
            self._coordinate = copy.deepcopy(self.destination_coordinate)
        else:
            self._coordinate = tuple(float(x) for x in np.copy(self.coordinate + mobility * v / np.linalg.norm(v)))

    def update(self) -> float:
        """ タスクの進捗を更新 """
        if not self.check_assigned_performance() or not self.check_dependencies_completed():
            return 0.0  # 実行不可

        mobility_values = [robot.type.performance.get(RobotPerformanceAttributes.MOBILITY, 0) for robot in self.assigned_robot]
        if not mobility_values or max(mobility_values) == 0:
            return 0.0  # 移動能力なし

        min_mobility = min(mobility_values)
        adjusted_mobility = min_mobility * self.transportability
        
        before_position = np.array(self.coordinate)
        self._travel(adjusted_mobility)
        after_position = np.array(self.coordinate)
        # ロボットもタスクと同時に移動
        for robot in self.assigned_robot:
            robot.update_coordinate(after_position)

        distance_traveled = np.linalg.norm(after_position - before_position)
        self._completed_workload += distance_traveled
        return distance_traveled

class Manufacture(Task):
    """ 加工タスクのクラス """
    def __init__(self, name: str, coordinate: Tuple[float, float], total_workload: float, 
                 completed_workload: float, task_dependency: List["Task"], 
                 required_performance: Dict["RobotPerformanceAttributes", int], 
                 other_attrs = None):
        super().__init__(name, coordinate, total_workload, completed_workload, task_dependency, 
                         required_performance, other_attrs)

    def update(self) -> float:
        """ タスクの進捗を更新（呼び出されるごとに+1） """
        if not self.check_assigned_performance() or not self.check_dependencies_completed():
            return 0.0  # 実行不可

        self._completed_workload += 1.0
        return 1.0  # 進捗量を1増加

class Charge(Task):
    """ 充電タスク """
    def __init__(self, name: str, coordinate: Tuple[float, float], total_workload: float, 
                 completed_workload: float, task_dependency: List["Task"], 
                 required_performance: Dict["RobotPerformanceAttributes", int], other_attrs = None):
        super().__init__(name, coordinate, total_workload, completed_workload, task_dependency, 
                         required_performance, other_attrs)

class Module:
    """ モジュールのクラス """
    def __init__(self, module_type: "ModuleType", name: str, coordinate: Tuple[float, float], 
                 battery: float, state: ModuleState = ModuleState.ACTIVE):
        self._type = module_type  # モジュールの種類
        self._name = name  # モジュール名
        self._coordinate = coordinate  # モジュールの座標
        if battery > module_type.max_battery:
            raise ValueError("Battery exceeds the maximum capacity.")
        self._battery = battery  # 現在のバッテリー残量
        self._state = state  # モジュールの状態

    @property
    def type(self):
        return self._type

    @property
    def name(self):
        return self._name

    @property
    def coordinate(self):
        return self._coordinate
    
    @property
    def battery(self):
        return self._battery
    
    @property
    def state(self):
        return self._state

    def update_coordinate(self, coordinate: Union[Tuple[float, float], np.ndarray, list]):
        # NumPyの配列ならタプルに変換
        if isinstance(coordinate, np.ndarray):
            if coordinate.shape == (2,):  # 2要素の1次元配列か確認
                coordinate = tuple(map(float, coordinate))  # float に変換
            else:
                raise TypeError(f"Invalid coordinate shape: {coordinate.shape}. Expected shape (2,).")

        # リストの場合もタプルに変換
        elif isinstance(coordinate, list):
            if len(coordinate) == 2:
                coordinate = tuple(map(float, coordinate))
            else:
                raise TypeError(f"Invalid coordinate length: {len(coordinate)}. Expected length 2.")

        # NumPyのfloat64が含まれているタプルを処理
        elif isinstance(coordinate, tuple):
            if len(coordinate) == 2 and all(isinstance(x, (float, int, np.float64)) for x in coordinate):
                coordinate = tuple(map(float, coordinate))  # floatに変換
            else:
                raise TypeError(f"Invalid coordinate format: {coordinate}. Expected Tuple[float, float].")

        else:
            raise TypeError(f"Invalid coordinate type: {type(coordinate)}. Expected Tuple[float, float] or np.ndarray.")
        
        """ モジュールの座標を更新 """
        self._coordinate = copy.deepcopy(coordinate)
    
    def update_battery(self, battery_variation: float):
        """ モジュールのバッテリーを更新 """
        if self.state == ModuleState.ERROR:
            raise ValueError("Cannot update battery of malfunctioning module.")
        battery = self.battery + battery_variation
        if battery > self.type.max_battery:
            battery = self.type.max_battery
        elif battery < 0:
            battery = 0
        self._battery = battery
    
    def update_state(self, state: ModuleState):
        """ モジュールの状態を更新 """
        self._state = state

    def __str__(self):
        """ モジュールの簡単な情報を文字列として表示 """
        return f"Module({self.name}, {self.state.name}, Battery: {self.battery}/{self.type.max_battery})"

    def __repr__(self):
        """ デバッグ用の詳細な表現 """
        return f"Module(name={self.name}, type={self.type.name}, state={self.state.name}, battery={self.battery})"

class Robot:
    """ ロボットのクラス """
    def __init__(self, robot_type: "RobotType", name: str, coordinate: Tuple[float, float], 
                 component: List["Module"], task_priority: List["Task"]):
        self._type = robot_type  # ロボットの種類
        self._name = name  # ロボット名
        self._coordinate = coordinate  # 現在の座標
        self._component = component  # 搭載モジュール
        self._state = RobotState.IDLE # ロボットの状態（IDLEで初期化）

        # ERRORな搭載モジュールはリストから除外
        self._component = [module for module in self._component if module.state != ModuleState.ERROR]
        # 座標の異なるモジュールをリストから除外
        self._component = [module for module in self._component if module.coordinate == self.coordinate]
        # 構成に必要なモジュール数を満たしているかチェック
        if self._check_component_shortage():
            self._state = RobotState.DEFECTIVE
        # バッテリーが使用電力以上かチェック
        if self._check_battery_shortage():
            self._state = RobotState.NO_ENERGY
        
        self._task_priority = task_priority  # タスクの優先順位リスト

    @property
    def type(self):
        return self._type

    @property
    def name(self):
        return self._name

    @property
    def coordinate(self):
        return self._coordinate
    
    @property
    def component(self):
        return self._component
    
    @property
    def state(self):
        return self._state
    
    def _check_component_shortage(self) -> bool:
        """ 構成に必要なモジュール数を満たしているかチェック """
        for module_type, required_num in self.type.required_modules.items():
            num = len([module for module in self._component if module.type == module_type])
            if num >= required_num:
                continue
            else:
                return True
        return False

    def total_battery(self):
        sum = 0
        for module in self._component:
            sum += module.battery
        return sum

    def _check_battery_shortage(self) -> bool:
        """ バッテリーが使用電力以上かチェック """
        return self.total_battery() < self.type.power_consumption

    def update_coordinate(self, coordinate: Union[Tuple[float, float], np.ndarray, list]):
        # NumPyの配列ならタプルに変換
        if isinstance(coordinate, np.ndarray):
            if coordinate.shape == (2,):  # 2要素の1次元配列か確認
                coordinate = tuple(map(float, coordinate))  # float に変換
            else:
                raise TypeError(f"Invalid coordinate shape: {coordinate.shape}. Expected shape (2,).")

        # リストの場合もタプルに変換
        elif isinstance(coordinate, list):
            if len(coordinate) == 2:
                coordinate = tuple(map(float, coordinate))
            else:
                raise TypeError(f"Invalid coordinate length: {len(coordinate)}. Expected length 2.")

        # NumPyのfloat64が含まれているタプルを処理
        elif isinstance(coordinate, tuple):
            if len(coordinate) == 2 and all(isinstance(x, (float, int, np.float64)) for x in coordinate):
                coordinate = tuple(map(float, coordinate))  # floatに変換
            else:
                raise TypeError(f"Invalid coordinate format: {coordinate}. Expected Tuple[float, float].")

        else:
            raise TypeError(f"Invalid coordinate type: {type(coordinate)}. Expected Tuple[float, float] or np.ndarray.")
        """ ロボットの座標を更新し、搭載モジュールの座標も同期 """
        self._coordinate = copy.deepcopy(coordinate)
        for module in self._component:
            module.update_coordinate(copy.deepcopy(coordinate))
    
    def try_assign_module(self, module: "Module"):
        """ モジュールを搭載 """
        # ModuleStateがERRORでないことを確認
        if module.state == ModuleState.ERROR:
            return False
        # ロボットの座標とモジュールの座標が一致しているかチェック
        if module.coordinate != self.coordinate:
            return False
        self._component.append(module)
        return True
    
    def malfunction(self, module: "Module"):
        """ モジュールの故障 """
        module.update_state(ModuleState.ERROR)
        self._component.remove(module)
    
    def update_state(self, state: RobotState):
        """ ロボットの状態を更新 """
        self._state = state
        # 構成に必要なモジュール数を満たしているかチェック
        if self._check_component_shortage():
            self._state = RobotState.DEFECTIVE
        # バッテリーが使用電力以上かチェック
        if self._check_battery_shortage():
            self._state = RobotState.NO_ENERGY

    def update_task_priority(self, task_priority: List["Task"]):
        """ タスクの優先順位リストを更新 """
        self._task_priority = task_priority

    def __str__(self):
        """ ロボットの簡単な情報を文字列として表示 """
        return f"Robot({self.name}, {self._state.name}, Pos: {self.coordinate})"

    def __repr__(self):
        """ デバッグ用の詳細な表現 """
        return (f"Robot(name={self.name}, type={self.type.name}, state={self._state.name}, "
                f"coordinate={self.coordinate}, modules={len(self._component)}, "
                f"task_priority={len(self._task_priority)})")
