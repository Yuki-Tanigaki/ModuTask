from typing import Dict, Tuple, Union
import logging
import numpy as np
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.task.task import BaseTask
from modutask.core.utils import make_coodinate_to_tuple

logger = logging.getLogger(__name__)

class Transport(BaseTask):
    """ 運搬タスクのクラス """
    def __init__(self, name: str, coordinate: Union[Tuple[float, float], np.ndarray, list], 
                 required_performance: Dict[PerformanceAttributes, float], 
                 origin_coordinate: Union[Tuple[float, float], np.ndarray, list], 
                 destination_coordinate: Union[Tuple[float, float], np.ndarray, list],
                 transportability: float, total_workload: float=None, completed_workload: float=None):
        self._origin_coordinate = make_coodinate_to_tuple(origin_coordinate)  # 出発地点座標
        self._destination_coordinate = make_coodinate_to_tuple(destination_coordinate)  # 目的地座標
        self._transportability = transportability  # 荷物運搬の難しさ
        if transportability < 1.0:
            logger.error(f"{name}: transportability must be set to 1 or higher.")
            raise ValueError(f"{name}: transportability must be set to 1 or higher.")
        # total_workloadがNoneの場合は初期化
        if (total_workload is None) != (completed_workload is None):
            logger.error(f"{name}: both 'total_workload' and 'completed_workload' must be set together.")
            raise ValueError(f"{name}: both 'total_workload' and 'completed_workload' must be set together.")
            
        if total_workload is None:
            # 運搬距離*荷物運搬の難しさでタスクの総仕事量を初期化
            v = np.array(self.destination_coordinate) - np.array(self._origin_coordinate)
            total_workload = transportability * np.linalg.norm(v)
            completed_workload = 0.0
        super().__init__(name=name, coordinate=coordinate, total_workload=total_workload, 
                         completed_workload=completed_workload, required_performance=required_performance)
    
    @property
    def origin_coordinate(self) -> Tuple[float, float]:
        return self._origin_coordinate
    
    @property
    def destination_coordinate(self) -> Tuple[float, float]:
        return self._destination_coordinate
    
    @property
    def transportability(self) -> float:
        return self._transportability

    def _travel(self, mobility: float) -> None:
        """ 荷物の移動処理 """
        target_coordinate = np.array(self.destination_coordinate)
        v = target_coordinate - np.array(self.coordinate)
        if np.linalg.norm(v) < mobility:
            self.coordinate = self.destination_coordinate
        else:
            self.coordinate = self.coordinate + mobility * v / np.linalg.norm(v)

    def update(self) -> bool:
        """ タスクの進捗を更新 """
        if not self.is_performance_satisfied() or not self.are_dependencies_completed():
            return False  # 実行不可

        mobility_values = [robot.type.performance.get(PerformanceAttributes.MOBILITY, 0) for robot in self.assigned_robot]
        if not mobility_values or max(mobility_values) == 0:
            return False  # 移動能力なし

        min_mobility = min(mobility_values)
        adjusted_mobility = min_mobility / self.transportability
        
        self._travel(adjusted_mobility)
        # ロボットもタスクと同時に移動
        # ロボットのバッテリーを消費
        for robot in self.assigned_robot:
            robot.travel(self.coordinate)
            if robot.coordinate != self.coordinate:
                logger.error(f"{self.name}: {robot.name} cannot follow the object to be transported.")
                raise RuntimeError(f"{self.name}: {robot.name} cannot follow the object to be transported.")

        # 残り移動距離に応じて完了済み仕事量を計算
        v = np.array(self.destination_coordinate) - np.array(self.coordinate)
        left = np.linalg.norm(v) * self.transportability
        self._completed_workload = self.total_workload - left
        return True