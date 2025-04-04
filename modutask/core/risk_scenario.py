from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
import numpy as np
from numpy.random import Generator
import logging, copy
from modutask.utils import raise_with_log


if TYPE_CHECKING:
    from modutask.core.module import Module  # 遅延評価によって循環参照を回避

logger = logging.getLogger(__name__)

class BaseRiskScenario(ABC):
    """ 故障シナリオを定義する抽象基底クラス """

    def __init__(self, name: str, seed: int):
        self.name = name
        self.seed = seed
        self.rng: Optional[Generator] = None

    def initialize(self) -> None:
        if self.rng is not None:
            raise_with_log(RuntimeError, "RNG has already been initialized. 'initialize()' should only be called once.")
        self.rng = np.random.default_rng(self.seed)

    @abstractmethod
    def malfunction_module(self, module: "Module") -> bool:
        """ モジュールの故障を判定 """
        pass

    def __str__(self) -> str:
        return f"<Scenario: {self.name}>"

    def __repr__(self) -> str:
        return (f"Scenario(name={self.name}, seed={self.seed})")
    
    def __deepcopy__(self, memo):
        return BaseRiskScenario(
            copy.deepcopy(self.name, memo),
            copy.deepcopy(self.seed, memo),
        )


class ExponentialFailure(BaseRiskScenario):
    """ 使用時間が増えると指数関数で故障確率が増えるシナリオ """

    def __init__(self, name: str, failure_rate: float, seed: int):
        self.failure_rate = failure_rate
        super().__init__(name=name, seed=seed)

    def _exponential(self, val: float) -> float:
        return float(1 - np.exp(-self.failure_rate * val))

    def malfunction_module(self, module: "Module") -> bool:
        if self.rng is None:
            raise_with_log(RuntimeError, "RNG not initialized. Call 'initialize()' first.")
        return self.rng.random() < self._exponential(float(module.operating_time))

    def __deepcopy__(self, memo):
        return ExponentialFailure(
            copy.deepcopy(self.name, memo),
            copy.deepcopy(self.failure_rate, memo),
            copy.deepcopy(self.seed, memo),
        )
