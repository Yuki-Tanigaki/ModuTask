import logging
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.task.task import BaseTask
from modutask.core.robot.robot import Robot

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

    @property
    def target_robot(self) -> Robot:
        return self._target_robot

    def update(self) -> bool:
        """ 対象のロボットを組み立てる """
        if self.is_completed():
            return False
        for module in self.target_robot.missing_components():
            if module.coordinate == self.target_robot.coordinate:
                self.target_robot.mount_module(module)
                self._completed_workload += 1.0
                return True
        return False

        