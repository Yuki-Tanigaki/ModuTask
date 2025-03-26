from dataclasses import dataclass
from typing import Tuple, Union
from enum import Enum
import copy, logging
import numpy as np
from modutask.core.utils import make_coodinate_to_tuple
from modutask.core.module.scenario import BaseScenario

logger = logging.getLogger(__name__)

class ModuleState(Enum):
    """ モジュールの状態を表す列挙型 """
    ACTIVE = (0, 'green')  # 正常
    ERROR = (1, 'gray')  # 故障
    
    @classmethod
    def from_value(cls, value):
        for state in cls:
            if state.value[0] == value:
                return state
        logger.error(f"{value} is not a valid ModuleState.")
        raise ValueError(f"{value} is not a valid ModuleState.")
    
    @property
    def color(self) -> str:
        """ モジュールの状態に対応する色を取得 """
        return self.value[1]
    
@dataclass
class ModuleType:
    """ モジュールの種類 """
    name: str  # モジュール名
    max_battery: float  # 最大バッテリー容量

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other: 'ModuleType') -> bool:
        return self.name == other.name

class Module:
    """ モジュールのクラス """
    def __init__(self, module_type: ModuleType, name: str, coordinate: Union[Tuple[float, float], np.ndarray, list], 
                 battery: float, operating_time: float):
        self._type = module_type  # モジュールの種類
        self._name = name  # モジュール名
        self._coordinate = make_coodinate_to_tuple(coordinate)  # モジュールの座標
        self._battery = battery  # 現在のバッテリー残量
        self._operating_time = operating_time  # モジュールの稼働時間
        self._scenarios = None  # 故障シナリオ
        self._state = None  # モジュールの状態
        
        if battery > module_type.max_battery:
            logger.error(f"{name}: battery exceeds the maximum capacity.")
            raise ValueError(f"{name}: battery exceeds the maximum capacity.")
        if battery < 0.0:
            logger.error(f"{name}: battery must be positive.")
            raise ValueError(f"{name}: battery must be positive.")
        if operating_time < 0.0:
            logger.error(f"{name}: current operating_time must be positive.")
            raise ValueError(f"{name}: current operating_time must be positive.")

    @property
    def type(self) -> ModuleType:
        return self._type

    @property
    def name(self) -> str:
        return self._name

    @property
    def coordinate(self) -> Tuple[float, float]:
        return self._coordinate
    
    @property
    def battery(self) -> float:
        return self._battery
    
    @property
    def operating_time(self) -> float:
        return self._operating_time
    
    @property
    def scenarios(self) -> float:
        if self._scenarios is None:
            logger.error(f"{self.name}: scenarios is not initialized.")
            raise RuntimeError(f"{self.name}: scenarios is not initialized.")
        return self._scenarios
    
    @property
    def state(self) -> ModuleState:
        if self._state is None:
            logger.error(f"{self.name}: state is not initialized.")
            raise RuntimeError(f"{self.name}: state is not initialized.")
        return self._state

    @coordinate.setter
    def coordinate(self, coordinate: Union[Tuple[float, float], np.ndarray, list]):
        """ モジュールの座標を更新 """
        self._coordinate = copy.deepcopy(make_coodinate_to_tuple(coordinate))
    
    @battery.setter
    def battery(self, battery: float):
        """ モジュールのバッテリーを更新 """
        if self.state == ModuleState.ERROR:
            logger.error(f"{self.name}: try update battery of malfunctioning module.")
            raise RuntimeError(f"{self.name}: try update battery of malfunctioning module.")
        if battery > self.type.max_battery:
            logger.error(f"{self.name}: battery exceeds the maximum capacity.")
            raise ValueError(f"{self.name}: battery exceeds the maximum capacity.")
        if battery < 0.0:
            logger.error(f"{self.name}: battery must be positive.")
            raise ValueError(f"{self.name}: battery must be positive.")

        self._battery = battery
    
    @operating_time.setter
    def operating_time(self, operating_time: float):
        """ モジュールの稼働量を更新 """
        if self.state == ModuleState.ERROR:
            logger.error(f"{self.name}: try update runtime of malfunctioning module.")
            raise RuntimeError(f"{self.name}: try update battery of malfunctioning module.")
        if operating_time < 0.0:
            logger.error(f"{self.name}: operating_time must be positive.")
            raise ValueError(f"{self.name}: operating_time must be positive.")
        if operating_time < self.operating_time:
            logger.error(f"{self.name}: operating_time less than the current operating_time.")
            raise ValueError(f"{self.name}: operating_time less than the current operating_time.")

        self._operating_time = operating_time
    
    def is_active(self) -> bool:
        """ モジュールが使用可能か """
        return self.state == ModuleState.ACTIVE

    def initialize_scenarios(self, scenarios: "BaseScenario"):
        """ モジュール状態の初期化 """
        self._scenarios = scenarios
        self.update_state()

    def update_state(self):
        """ モジュール状態の更新 """
        self._state = ModuleState.ACTIVE
        for scenario in self.scenarios:
            if scenario.malfunction_module(self):
                self._state = ModuleState.ERROR
                return

    def __str__(self):
        """ モジュールの簡単な情報を文字列として表示 """
        return f"Module({self.name}, {self.state.name}, Battery: {self.battery}/{self.type.max_battery})"

    def __repr__(self):
        """ デバッグ用の詳細な表現 """
        return f"Module(name={self.name}, type={self.type.name}, state={self.state.name}, battery={self.battery})"