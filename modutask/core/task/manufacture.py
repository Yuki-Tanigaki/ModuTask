from typing import Union
from numpy.typing import NDArray
import logging
import numpy as np
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.task.task import BaseTask
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)

class Manufacture(BaseTask):
    """ 加工タスクのクラス """
    def __init__(self, name: str, coordinate: Union[tuple[float, float], NDArray[np.float64], list[float]], total_workload: float, 
                 completed_workload: float, required_performance: dict[PerformanceAttributes, float]):
        super().__init__(name=name, coordinate=coordinate, total_workload=total_workload, 
                         completed_workload=completed_workload, required_performance=required_performance)

    def update(self) -> bool:
        """
        加工タスクが実行
        完了済み仕事量を 1 増加する
        """
        if not self.is_performance_satisfied() or not self.are_dependencies_completed():
            return False
        if self.assigned_robot is None:
            raise_with_log(RuntimeError, f"Assigned_robot must be initialized: {self.name}.")

        for robot in self.assigned_robot:
            robot.act()
        
        self._completed_workload += 1.0
        return True