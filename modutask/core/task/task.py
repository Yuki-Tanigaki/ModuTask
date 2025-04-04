from abc import ABC, abstractmethod
from typing import Union, Optional
from numpy.typing import NDArray
import copy, logging
import numpy as np
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.robot.robot import Robot, RobotState
from modutask.core.utils import make_coodinate_to_tuple
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)

class BaseTask(ABC):
    """ タスクを表す抽象基底クラス """

    def __init__(self, name: str, coordinate: Union[tuple[float, float], NDArray[np.float64], list[float]], total_workload: float, 
                 completed_workload: float, required_performance: dict[PerformanceAttributes, float]):
        self._name = name  # タスク名
        self._coordinate = make_coodinate_to_tuple(coordinate)  # タスクの座標
        self._total_workload = total_workload  # タスクの総仕事量
        self._completed_workload = completed_workload  # 完了済み仕事量
        self._required_performance = required_performance  # タスク実行に要求される能力値
        self._task_dependency: Optional[list[BaseTask]] = None  # 依存するタスクのリスト
        self._assigned_robot: list[Robot] = [] # タスクに配置済みのロボットのリスト
        if total_workload < 0.0:
            raise_with_log(ValueError, f"Total_workload must be positive: {self.name}.")
        if completed_workload > total_workload:
            raise_with_log(ValueError, f"Completed_workload exceeds the maximum capacity: {self.name}.")
        if completed_workload < 0.0:
            raise_with_log(ValueError, f"Completed_workload must be positive: {self.name}.")
    
    @property
    def name(self) -> str:
        return self._name

    @property
    def coordinate(self) -> tuple[float, float]:
        return self._coordinate
    
    @coordinate.setter
    def coordinate(self, coordinate: Union[tuple[float, float], NDArray[np.float64], list[float]]) -> None:
        self._coordinate = copy.deepcopy(make_coodinate_to_tuple(coordinate))

    @property
    def total_workload(self) -> float:
        return self._total_workload
    
    @property
    def completed_workload(self) -> float:
        return self._completed_workload
    
    @property
    def task_dependency(self) -> list["BaseTask"]:
        if self._task_dependency is None:
            raise_with_log(RuntimeError, f"Task_dependency must be initialized before use: {self.name}.")
        return self._task_dependency

    @property
    def required_performance(self) -> dict["PerformanceAttributes", float]:
        return self._required_performance
    
    @property
    def assigned_robot(self) -> list[Robot]:
        return self._assigned_robot

    @abstractmethod
    def update(self) -> bool:
        """ タスクが実行されたときの処理を記述 """
        pass
    
    def initialize_task_dependency(self, task_dependency: list["BaseTask"]) -> None:
        """ タスクの依存関係を設定 """
        self._task_dependency = task_dependency

    def is_completed(self) -> bool:
        """ タスクが完了しているかを確認 """
        return self.completed_workload >= self.total_workload
    
    def are_dependencies_completed(self) -> bool:
        """ 依存するタスクがすべて完了しているかを確認する """
        return all(dep.is_completed() for dep in self.task_dependency)

    def is_performance_satisfied(self) -> bool:
        """ 
        配置されたロボットが必要なパフォーマンスを満たしているか確認
        タスクは複数のロボットの共同作業により実行される
        ロボットの合計能力値がrequired_performance以上の時、タスクは実行される
        """
        total_assigned_performance = {attr: 0 for attr in PerformanceAttributes}
        for robot in self.assigned_robot:
            for attr, value in robot.type.performance.items():
                total_assigned_performance[attr] += value

        return all(total_assigned_performance[attr] >= req for attr, req in self.required_performance.items())

    def release_robot(self) -> None:
        """ 配置されている全ロボットをリリース """
        self._assigned_robot = []

    def assign_robot(self, robot: Robot) -> None:
        """ ロボットを配置 """
        if robot.state != RobotState.ACTIVE:
            raise_with_log(RuntimeError, f"{robot.name} with {robot.state} are assigned: {self.name}.")
        if not np.allclose(robot.coordinate, self.coordinate, atol=1e-8):
            raise_with_log(RuntimeError, f"{robot.name} with mismatched coordinates are assigned: {self.name}.")

        self._assigned_robot.append(robot)

    def __str__(self) -> str:
        """ タスクを文字列として表示 """
        return f"{self.name}[{self.completed_workload}/{self.total_workload}]"

    def __repr__(self) -> str:
        """ デバッグ用の表現 """
        return f"Task(name={self.name}, completed={self.completed_workload}, total={self.total_workload})"
    
    def __deepcopy__(self, memo):
        clone = BaseTask(
            copy.deepcopy(self.name, memo),
            copy.deepcopy(self.coordinate, memo),
            copy.deepcopy(self.total_workload, memo),
            copy.deepcopy(self.completed_workload, memo),
            copy.deepcopy(self.required_performance, memo)
        )
        clone._task_dependency = copy.deepcopy(self.task_dependency, memo)
        return clone
