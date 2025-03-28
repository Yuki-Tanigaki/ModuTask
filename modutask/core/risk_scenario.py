from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict
import numpy as np
import logging


if TYPE_CHECKING:
    from modutask.core.module import Module  # 遅延評価によって循環参照を回避

logger = logging.getLogger(__name__)

class BaseScenario(ABC):
    """ ランダムな故障シナリオに関する抽象基底クラス """

    @abstractmethod
    def malfunction_module(self, module: "Module") -> bool:
        pass

class TimeSigmoid(BaseScenario):
    def __init__(self, sharpness: float, limit: int, seed: int):
        self.sharpness = sharpness
        self.limit = limit
        self.rng = np.random.default_rng(seed)

    def _normalize_sigmoid(self, current_val: float) -> float:
        ratio = current_val / float(self.limit)
        return 1 / (1 + np.exp(self.sharpness * (ratio - 0.5)))

    def malfunction_module(self, module: "Module") -> bool:
        return self.rng.random() < self._normalize_sigmoid(float(module.operating_time))
