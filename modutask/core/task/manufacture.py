from typing import Dict, Tuple
import logging
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.task.task import AbstractTask

logger = logging.getLogger(__name__)

class Manufacture(AbstractTask):
    """ 加工タスクのクラス """
    def __init__(self, name: str, coordinate: Tuple[float, float], total_workload: float, 
                 completed_workload: float, required_performance: Dict[PerformanceAttributes, int]):
        super().__init__(name=name, coordinate=coordinate, total_workload=total_workload, 
                         completed_workload=completed_workload, required_performance=required_performance)

    def update(self) -> bool:
        """ タスクの進捗を更新（呼び出されるごとに+1） """
        if not self.is_performance_satisfied() or not self.are_dependencies_completed():
            return False # 実行不可
        
        # ロボットのバッテリーを消費
        for robot in self.assigned_robot:
            robot.act()
        
        self._completed_workload += 1.0
        return True  # 進捗量を1増加
