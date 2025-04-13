from typing import Any, Union
from numpy.typing import NDArray
import logging
import numpy as np
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.task.transport import Transport
from modutask.core.module.module import Module
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)

class TransportModule(Transport):
    """ モジュール運搬タスクのクラス """

    def __init__(self, name: str, coordinate: Union[tuple[float, float], NDArray[np.float64], list[float]], 
                 required_performance: dict[PerformanceAttributes, float], 
                 origin_coordinate: Union[tuple[float, float], NDArray[np.float64], list[float]], 
                 destination_coordinate: Union[tuple[float, float], NDArray[np.float64], list[float]],
                 transport_resistance: float, total_workload: float, completed_workload: float,
                 target_module: Module):
        self._target_module = target_module
        super().__init__(name=name, coordinate=coordinate, total_workload=total_workload, 
                         completed_workload=completed_workload, required_performance=required_performance,
                         origin_coordinate=origin_coordinate, destination_coordinate=destination_coordinate,
                         transport_resistance=transport_resistance)
        self.initialize_task_dependency([])

    def update(self) -> bool:
        """
        運搬タスクが実行
        モジュールの位置を変更する
        """
        if super().update():
            self._target_module.coordinate = self.coordinate
            return True
        return False
    
    def __deepcopy__(self, memo: dict[int, Any]) -> "TransportModule":
        raise_with_log(RuntimeError, f"TransportModule cannot deepcopy: {self.name}.")
