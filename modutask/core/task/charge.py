from typing import Union
from numpy.typing import NDArray
import logging, copy
import numpy as np
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.task.task import BaseTask
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)

class Charge(BaseTask):
    """ 充電タスク """
    def __init__(self, name: str, coordinate: Union[tuple[float, float], NDArray[np.float64], list[float]], charging_speed: float):
        total_workload = 0.0
        completed_workload = 0.0
        required_performance: dict[PerformanceAttributes, float] = {}
        super().__init__(name=name, coordinate=coordinate, total_workload=total_workload, 
                         completed_workload=completed_workload, required_performance=required_performance)
        self._charging_speed = charging_speed
        self.initialize_task_dependency([])

    @property
    def charging_speed(self) -> float:
        return self._charging_speed

    def update(self) -> bool:
        """ 割り当てられたロボットを充電 """
        if self.assigned_robot is None:
            raise_with_log(RuntimeError, f"Assigned_robot must be initialized: {self.name}.")
        for robot in self.assigned_robot:
            robot.charge_battery_power(self.charging_speed)
        return True
    
    def __deepcopy__(self, memo):
        clone = Charge(
            copy.deepcopy(self.name, memo),
            copy.deepcopy(self.coordinate, memo),
            copy.deepcopy(self.charging_speed, memo),
        )
        clone._task_dependency = copy.deepcopy(self.task_dependency, memo)
        return clone