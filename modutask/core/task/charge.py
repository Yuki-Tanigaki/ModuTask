from typing import Tuple
import logging
from modutask.core.task.task import BaseTask

logger = logging.getLogger(__name__)

class Charge(BaseTask):
    """ 充電タスク """
    def __init__(self, name: str, coordinate: Tuple[float, float], charging_speed: float):
        total_workload = 0.0
        completed_workload = 0.0
        required_performance = {}
        super().__init__(name=name, coordinate=coordinate, total_workload=total_workload, 
                         completed_workload=completed_workload, required_performance=required_performance)
        self._charging_speed = charging_speed  # 充電速度

    @property
    def charging_speed(self) -> float:
        return self._charging_speed

    def update(self) -> bool:
        """ 割り当てられたロボットを充電 """
        for robot in self.assigned_robot:
            robot.charge_battery_power(self.charging_speed)
        return True