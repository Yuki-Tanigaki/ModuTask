import logging
from typing import Any
import numpy as np
from modutask.core.module.module import ModuleState
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.task.task import BaseTask
from modutask.core.robot.robot import Robot
from modutask.core.utils.coodinate_utils import is_within_range
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)

class Assembly(BaseTask):
    """ ロボット自己組み立てタスク """
    def __init__(self, name: str, robot: Robot):
        missingComponents = robot.missing_components()
        
        total_workload = len(missingComponents)
        completed_workload = 0.0
        required_performance: dict[PerformanceAttributes, float] = {}
        super().__init__(name=name, coordinate=robot.coordinate, total_workload=total_workload, 
                         completed_workload=completed_workload, required_performance=required_performance)
        self._target_robot = robot
        self.initialize_task_dependency([])

    @property
    def target_robot(self) -> Robot:
        return self._target_robot

    def update(self) -> bool:
        """ 対象のロボットを組み立てる """
        if self.is_completed():
            return False
        for module in self.target_robot.missing_components():
            if module.state == ModuleState.ERROR:
                continue
            if is_within_range(module.coordinate, self.target_robot.coordinate):
                self.target_robot.mount_module(module)
                self._completed_workload += 1.0
                return True
        return False
    
    def __deepcopy__(self, memo: dict[int, Any]) -> "Assembly":
        raise_with_log(RuntimeError, f"Assembly cannot deepcopy: {self.name}.")

        