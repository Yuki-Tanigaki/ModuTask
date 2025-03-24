from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
import logging
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.robot.robot import Robot, RobotState

logger = logging.getLogger(__name__)

class AbstractTask(ABC):
    """ タスクを表す抽象基底クラス """
    def __init__(self, name: str, coordinate: Tuple[float, float], total_workload: float, 
                 completed_workload: float, required_performance: Dict["PerformanceAttributes", float]):
        self._name = name  # タスク名
        self._coordinate = coordinate  # タスクの座標
        self._total_workload = total_workload  # タスクの総仕事量
        self._completed_workload = completed_workload  # 完了済み仕事量
        self._required_performance = required_performance  # タスク実行に要求される能力値
        self._task_dependency = None  # 依存するタスクのリスト
        self._assigned_robot = None # タスクに配置済みのロボットのリスト
        if total_workload < 0.0:
            logger.error(f"{name}: total_workload must be positive.")
            raise ValueError(f"{name}: total_workload must be positive.")
        if completed_workload > total_workload:
            logger.error(f"{name}: completed_workload exceeds the maximum capacity.")
            raise ValueError(f"{name}: completed_workload exceeds the maximum capacity.")
        if completed_workload < 0.0:
            logger.error(f"{name}: completed_workload must be positive.")
            raise ValueError(f"{name}: completed_workload must be positive.")
    
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
    def task_dependency(self) -> List["AbstractTask"]:
        return self._task_dependency

    @property
    def required_performance(self) -> Dict["PerformanceAttributes", float]:
        return self._required_performance
    
    @property
    def assigned_robot(self) -> List["Robot"]:
        return self._assigned_robot

    @abstractmethod
    def update(self) -> bool:
        """ タスクが実行されたときの処理を記述 """
        pass
    
    def set_task_dependency(self, task_dependency) -> None:
        """ 依存するタスクを設定 """
        self._task_dependency = task_dependency

    def is_completed(self) -> bool:
        """ タスクが完了しているかを確認 """
        return self.completed_workload >= self.total_workload

    def are_dependencies_completed(self) -> bool:
        """ 依存するタスクがすべて完了しているかを確認する """
        if self.task_dependency is None:
            logger.error(f"{self.name}: task_dependency is not set.")
            raise RuntimeError(f"{self.name}: task_dependency is not set.")
        return all(dep.is_completed() for dep in self.task_dependency)

    def is_performance_satisfied(self) -> bool:
        """ 
        配置されたロボットが必要なパフォーマンスを満たしているか確認
        タスクは複数のロボットの共同作業により実行される
        ロボットの合計能力値がrequired_performance以上の時、タスクは実行される
        """
        if self.assigned_robot is None:
            logger.error(f"{self.name}: assigned_robot is not set.")
            raise RuntimeError(f"{self.name}: assigned_robot is not set.")
        total_assigned_performance = {attr: 0 for attr in PerformanceAttributes}
        for robot in self.assigned_robot:
            for attr, value in robot.type.performance.items():
                total_assigned_performance[attr] += value

        return all(total_assigned_performance[attr] >= req for attr, req in self.required_performance.items())

    def release_robot(self) -> None:
        """ 配置されている全ロボットをリリース """
        self._assigned_robot = None

    def assign_robot(self, robot: "Robot") -> None:
        if self.assigned_robot is None:
            self._assigned_robot = []
        """ ロボットを配置 """
        # RobotStateがACTIVEなことを確認
        if robot.state != RobotState.ACTIVE:
            logger.error(f"{robot.name} is {robot.state}, cannot be assigned to tasks.")
            raise RuntimeError(f"{robot.name} is {robot.state}, cannot be assigned to tasks.")
        # ロボットの座標とタスクの座標が一致しているかチェック
        if robot.coordinate != self.coordinate:
            logger.error(f"{robot.name} with different coordinates are assigned to {self.name}.")
            raise RuntimeError(f"{robot.name} with different coordinates are assigned to {self.name}.")

        self._assigned_robot.append(robot)

    def __str__(self) -> str:
        """ タスクを文字列として表示 """
        return f"{self.name}[{self.completed_workload}/{self.total_workload}]"

    def __repr__(self) -> str:
        """ デバッグ用の表現 """
        return f"Task(name={self.name}, completed={self.completed_workload}, total={self.total_workload})"
