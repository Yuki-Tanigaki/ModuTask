from typing import Union
import logging
import numpy as np
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.task.task import BaseTask
from modutask.core.utils import make_coodinate_to_tuple
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)

class Transport(BaseTask):
    """ 運搬タスクのクラス """

    def __init__(self, name: str, coordinate: Union[tuple[float, float], np.ndarray, list], 
                 required_performance: dict[PerformanceAttributes, float], 
                 origin_coordinate: Union[tuple[float, float], np.ndarray, list], 
                 destination_coordinate: Union[tuple[float, float], np.ndarray, list],
                 resistance: float, total_workload: float, completed_workload: float):
        self._origin_coordinate = make_coodinate_to_tuple(origin_coordinate)  # 出発地点座標
        self._destination_coordinate = make_coodinate_to_tuple(destination_coordinate)  # 目的地座標
        self._resistance = resistance  # 荷物運搬の難しさ

        if resistance < 1.0:
            raise_with_log(ValueError, f"Resistance must be set to 1 or higher: {name}.")
        v = np.array(self.destination_coordinate) - np.array(self._origin_coordinate)
        total = resistance * np.linalg.norm(v)
        if total_workload != total:
            raise_with_log(ValueError, f"Total_workload does not match carrying_distance * resistance: {name}.")
        super().__init__(name=name, coordinate=coordinate, total_workload=total_workload, 
                         completed_workload=completed_workload, required_performance=required_performance)
    
    @property
    def origin_coordinate(self) -> tuple[float, float]:
        return self._origin_coordinate
    
    @property
    def destination_coordinate(self) -> tuple[float, float]:
        return self._destination_coordinate
    
    @property
    def resistance(self) -> float:
        return self._resistance

    def _travel(self, mobility: float) -> None:
        """ 荷物の移動処理 """
        target_coordinate = np.array(self.destination_coordinate)
        v = target_coordinate - np.array(self.coordinate)
        if np.linalg.norm(v) < mobility:
            self.coordinate = self.destination_coordinate
        else:
            self.coordinate = self.coordinate + mobility * v / np.linalg.norm(v)

        for robot in self.assigned_robot:  # ロボットを荷物に追従
            robot.travel(self.coordinate)
            if robot.coordinate != self.coordinate:
                raise_with_log(RuntimeError, f"{robot.name} cannot follow the object: {self.name}.")

    def update(self) -> bool:
        """
        運搬タスクが実行
        完了済み仕事量は残り移動距離に応じて計算する
        """
        if not self.is_performance_satisfied() or not self.are_dependencies_completed():
            return False

        mobility_values = [robot.type.performance.get(PerformanceAttributes.MOBILITY, 0) for robot in self.assigned_robot]
        if not mobility_values or max(mobility_values) == 0:
            return False

        min_mobility = min(mobility_values)
        adjusted_mobility = min_mobility / self.resistance
        
        self._travel(adjusted_mobility)

        v = np.array(self.destination_coordinate) - np.array(self.coordinate)
        left = np.linalg.norm(v) * self.resistance
        self._completed_workload = self.total_workload - left
        return True