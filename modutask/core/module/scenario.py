from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict
import logging

if TYPE_CHECKING:
    from modutask.core.module import Module  # 遅延評価によって循環参照を回避

logger = logging.getLogger(__name__)

class BaseScenario(ABC):
    """ ランダムな故障シナリオに関する抽象基底クラス """

    @abstractmethod
    def malfunction_module(self, module: "Module") -> bool:
        pass

class TimeBasedScenario(BaseScenario):
    def __init__(self, thresholds: Dict[str, float]):
        self.thresholds = thresholds

        for _, threshold in self.thresholds.items():
            if threshold < 0.0:
                logger.error(f"Maximum operating_time must be positive.")
                raise ValueError(f"Maximum operating_time must be positive.")

    def malfunction_module(self, module: "Module") -> bool:
        if module.operating_time > self.thresholds[module.name]:
            logger.error(f"Operating_time exceeds the maximum operating_time in {module.name}.")
            raise ValueError(f"Operating_time exceeds the maximum operating_time in {module.name}.")
        return module.operating_time == self.thresholds[module.name]
