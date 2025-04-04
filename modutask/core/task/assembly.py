import logging
import numpy as np
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.task.task import BaseTask
from modutask.core.robot.robot import Robot
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
            if np.allclose(module.coordinate, self.target_robot.coordinate, atol=1e-8):
                self.target_robot.mount_module(module)
                self._completed_workload += 1.0
                return True
        return False
    
    def __deepcopy__(self, memo):
        raise_with_log(RuntimeError, f"Assembly cannot deepcopy: {self.name}.")

        