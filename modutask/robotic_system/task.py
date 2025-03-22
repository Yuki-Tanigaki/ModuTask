from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any
import logging
import numpy as np
from .robot import Robot, RobotState, PerformanceAttributes
from .utils import make_coodinate_to_tuple

logger = logging.getLogger(__name__)

class Task(ABC):
    """ タスクを表す抽象基底クラス """
    def __init__(self, name: str, coordinate: Tuple[float, float], total_workload: float, 
                 completed_workload: float, task_dependency: List["Task"], 
                 required_performance: Dict["PerformanceAttributes", float], 
                 other_attrs: Dict[str, Any] = None):
        self._name = name  # タスク名
        self._coordinate = make_coodinate_to_tuple(coordinate)  # タスクの座標
        self._total_workload = total_workload  # タスクの総仕事量
        self._completed_workload = completed_workload  # 完了済み仕事量
        self._task_dependency = task_dependency  # 依存するタスクのリスト
        self._required_performance = required_performance  # タスク実行に要求される能力値
        self._assigned_robot = [] # タスクに配置済みのロボットのリスト（空で初期化）
        self._other_attrs = other_attrs if other_attrs is not None else {}  # 可視化用のタスク分類

    @property
    def name(self) -> str:
        return self._name

    @property
    def coordinate(self) -> Tuple[float, float]:
        return self._coordinate
    
    @property
    def total_workload(self) -> float:
        return self._total_workload
    
    @property
    def completed_workload(self) -> float:
        return self._completed_workload
    
    @property
    def task_dependency(self) -> List["Task"]:
        return self._task_dependency

    @property
    def required_performance(self) -> Dict["PerformanceAttributes", float]:
        return self._required_performance
    
    @property
    def assigned_robot(self) -> List["Robot"]:
        return self._assigned_robot
    
    @property
    def other_attrs(self) -> Dict[str, Any]:
        return self._other_attrs

    def __str__(self) -> str:
        """ タスクを文字列として表示（例: "タスク名[10/100]"）"""
        return f"{self.name}[{self.completed_workload}/{self.total_workload}]"

    def __repr__(self) -> str:
        """ デバッグ用の表現 """
        return f"Task(name={self.name}, completed={self.completed_workload}, total={self.total_workload})"

    def are_dependencies_completed(self) -> bool:
        """ 依存するタスクがすべて完了しているかを確認する """
        return all(dep.completed_workload >= dep.total_workload for dep in self.task_dependency)

    def is_performance_satisfied(self) -> bool:
        """ 
        配置されたロボットが必要なパフォーマンスを満たしているか確認
        タスクは複数のロボットの共同作業により実行される
        ロボットの合計能力値がrequired_performance以上の時、タスクは実行される
        """
        total_assigned_performance = {attr: 0 for attr in PerformanceAttributes}
        for robot in self.assigned_robot:
            # ロボットの座標とタスクの座標が一致しているかチェック
            if robot.coordinate != self.coordinate:
                logger.error(f"{robot.name} with different coordinates are assigned to {self.name}.")
                raise RuntimeError(f"{robot.name} with different coordinates are assigned to {self.name}.")
            for attr, value in robot.type.performance.items():
                total_assigned_performance[attr] += value

        return all(total_assigned_performance[attr] >= req for attr, req in self.required_performance.items())

    def release_robot(self) -> None:
        """ 配置されている全ロボットをリリース """
        self._assigned_robot = []

    def assign_robot(self, robot: "Robot") -> None:
        """ ロボットを配置 """
        # RobotStateがDEFECTIVEでないことを確認
        if robot.state == RobotState.DEFECTIVE:
            logger.error(f"{robot.name} is DEFECTIVE, cannot be assigned to tasks.")
            raise RuntimeError(f"{robot.name} is DEFECTIVE, cannot be assigned to tasks.")
        # RobotStateがNO_ENERGYでないことを確認
        if robot.state == RobotState.NO_ENERGY:
            logger.error(f"{robot.name} is NO_ENERGY, cannot be assigned to tasks.")
            raise RuntimeError(f"{robot.name} is NO_ENERGY, cannot be assigned to tasks.")   
        # ロボットの座標とタスクの座標が一致しているかチェック
        if robot.coordinate != self.coordinate:
            logger.error(f"{robot.name} with different coordinates are assigned to {self.name}.")
            raise RuntimeError(f"{robot.name} with different coordinates are assigned to {self.name}.")

        self._assigned_robot.append(robot)

    @abstractmethod
    def update(self) -> bool:
        """ タスクが実行されたときの処理を記述 """
        pass

class Transport(Task):
    """ 運搬タスクのクラス """
    def __init__(self, name: str, coordinate: Tuple[float, float], 
                 task_dependency: List["Task"], required_performance: Dict["PerformanceAttributes", float], 
                 origin_coordinate: Tuple[float, float], destination_coordinate: Tuple[float, float],
                 transportability: float, total_workload: None, completed_workload: None, other_attrs = None):
        self._origin_coordinate = make_coodinate_to_tuple(origin_coordinate)  # 出発地点座標
        self._destination_coordinate = make_coodinate_to_tuple(destination_coordinate)  # 目的地座標
        self._transportability = transportability  # 荷物運搬の難しさ
        if transportability < 1.0:
            logger.error(f"{name}: transportability must be set to 1 or higher.")
            raise ValueError(f"{name}: transportability must be set to 1 or higher.")
        # total_workloadがNoneの場合は初期化
        if total_workload is None:
            if completed_workload is not None:
                logger.error(f"{name}: only completed_workload is set — total_workload is still missing.")
                raise ValueError(f"{name}: only completed_workload is set — total_workload is still missing.")
            else:
                # 運搬距離*荷物運搬の難しさでタスクの総仕事量を初期化
                v = np.array(self.destination_coordinate) - np.array(self._origin_coordinate)
                total_workload = transportability * np.linalg.norm(v)
                completed_workload = 0.0
        super().__init__(name, coordinate, total_workload, completed_workload, task_dependency, 
                         required_performance, other_attrs)
    
    @property
    def origin_coordinate(self) -> Tuple[float, float]:
        return self._origin_coordinate
    
    @property
    def destination_coordinate(self) -> Tuple[float, float]:
        return self._destination_coordinate
    
    @property
    def transportability(self) -> float:
        return self._transportability

    def _travel(self, mobility: float) -> None:
        """ 荷物の移動処理 """
        target_coordinate = np.array(self.destination_coordinate)
        v = target_coordinate - np.array(self.coordinate)
        if np.linalg.norm(v) < mobility:
            self._coordinate = make_coodinate_to_tuple(self.destination_coordinate)
        else:
            self._coordinate = make_coodinate_to_tuple(self.coordinate + mobility * v / np.linalg.norm(v))

    def update(self) -> bool:
        """ タスクの進捗を更新 """
        if not self.is_performance_satisfied() or not self.are_dependencies_completed():
            return False  # 実行不可

        mobility_values = [robot.type.performance.get(PerformanceAttributes.MOBILITY, 0) for robot in self.assigned_robot]
        if not mobility_values or max(mobility_values) == 0:
            return False  # 移動能力なし

        min_mobility = min(mobility_values)
        adjusted_mobility = min_mobility / self.transportability
        
        self._travel(adjusted_mobility)
        # ロボットもタスクと同時に移動
        # ロボットのバッテリーを消費
        for robot in self.assigned_robot:
            robot.update_coordinate(self.coordinate)
            robot.draw_battery_power()

        # 残り移動距離に応じて完了済み仕事量を計算
        v = np.array(self.destination_coordinate) - np.array(self.coordinate)
        left = np.linalg.norm(v) * self.transportability
        self._completed_workload = self.total_workload - left
        return True

class Manufacture(Task):
    """ 加工タスクのクラス """
    def __init__(self, name: str, coordinate: Tuple[float, float], total_workload: float, 
                 completed_workload: float, task_dependency: List["Task"], 
                 required_performance: Dict["PerformanceAttributes", int], 
                 other_attrs = None):
        super().__init__(name, coordinate, total_workload, completed_workload, task_dependency, 
                         required_performance, other_attrs)

    def update(self) -> bool:
        """ タスクの進捗を更新（呼び出されるごとに+1） """
        if not self.is_performance_satisfied() or not self.are_dependencies_completed():
            return False # 実行不可
        
        # ロボットのバッテリーを消費
        for robot in self.assigned_robot:
            robot.draw_battery_power()
        
        self._completed_workload += 1.0
        return True  # 進捗量を1増加

class Charge(Task):
    """ 充電タスク """
    def __init__(self, name: str, coordinate: Tuple[float, float], 
                 charging_speed: float, other_attrs = None):
        total_workload = 0.0
        completed_workload = 0.0
        task_dependency = []
        required_performance = {}
        super().__init__(name, coordinate, total_workload, completed_workload, task_dependency, 
                         required_performance, other_attrs)
        self._charging_speed = charging_speed  # 充電速度

    @property
    def charging_speed(self):
        return self._charging_speed

    def update(self) -> bool:
        """ 割り当てられたロボットを充電 """
        for robot in self._assigned_robot:
            robot.charge_battery_power(self._charging_speed)
        return True