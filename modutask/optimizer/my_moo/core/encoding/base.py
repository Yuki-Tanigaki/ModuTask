from abc import ABC, abstractmethod
from typing import Any

class BaseVariable(ABC):
    @abstractmethod
    def sample(self) -> Any:
        """初期化用にランダムな値を生成する"""
        pass

    @abstractmethod
    def mutate(self, value: Any) -> Any:
        """与えられた値に突然変異を適用する"""
        pass

    @abstractmethod
    def crossover(self, value1: Any, value2: Any) -> Any:
        """2つの親の値から子の値を生成する"""
        pass

    @abstractmethod
    def validate(self, value: Any) -> bool:
        """値が有効かどうかを判定する（範囲外チェックなど）"""
        pass

    @abstractmethod
    def equals(self, value1: Any, value2: Any) -> bool:
        """2つの値が等しいかどうかを判定する"""
        pass
    
    @abstractmethod
    def hash(self, value: Any) -> int:
        """値のハッシュ値を計算する"""
        pass