from dataclasses import dataclass
from typing import Tuple, Union
from enum import Enum
import logging
import numpy as np
from modutask.core.utils import make_coodinate_to_tuple

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
    def color(self):
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
    def __init__(self, module_type: "ModuleType", name: str, coordinate: Tuple[float, float], 
                 battery: float, max_operating_time: float, current_operating_time: float=0.0):
        self._type = module_type  # モジュールの種類
        self._name = name  # モジュール名
        self._coordinate = make_coodinate_to_tuple(coordinate)  # モジュールの座標
        self._battery = battery  # 現在のバッテリー残量
        self._max_operating_time = max_operating_time  # モジュールの耐久
        self._current_operating_time = current_operating_time  # 現在の耐久
        # モジュールの状態
        if current_operating_time == max_operating_time:
            self._state = ModuleState.ERROR
        else:
            self._state = ModuleState.ACTIVE
        
        if battery > module_type.max_battery:
            logger.error(f"{name}: battery exceeds the maximum capacity.")
            raise ValueError(f"{name}: battery exceeds the maximum capacity.")
        if battery < 0.0:
            logger.error(f"{name}: battery must be positive.")
            raise ValueError(f"{name}: battery must be positive.")
        if current_operating_time > max_operating_time:
            logger.error(f"{name}: current operating_time exceeds the maximum operating_time.")
            raise ValueError(f"{name}: current operating_time exceeds the maximum operating_time.")
        if current_operating_time < 0.0:
            logger.error(f"{name}: current operating_time must be positive.")
            raise ValueError(f"{name}: current operating_time must be positive.")
        if max_operating_time < 0.0:
            logger.error(f"{name}: maximum operating_time must be positive.")
            raise ValueError(f"{name}: maximum operating_time must be positive.")

    @property
    def type(self):
        return self._type

    @property
    def name(self):
        return self._name

    @property
    def coordinate(self):
        return self._coordinate
    
    @property
    def battery(self):
        return self._battery

    @property
    def max_operating_time(self):
        return self._max_operating_time
    
    @property
    def current_operating_time(self):
        return self._current_operating_time

    @property
    def state(self):
        return self._state


    def set_coordinate(self, coordinate: Union[Tuple[float, float], np.ndarray, list]):
        """ モジュールの座標を更新 """
        self._coordinate = make_coodinate_to_tuple(coordinate)
    
    def set_battery(self, battery: float):
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
    
    def set_operating_time(self, operating_time: float):
        """ モジュールの稼働量を更新 """
        if self.state == ModuleState.ERROR:
            logger.error(f"{self.name}: try update runtime of malfunctioning module.")
            raise RuntimeError(f"{self.name}: try update battery of malfunctioning module.")
        if operating_time < 0.0:
            logger.error(f"{self.name}: operating_time must be positive.")
            raise ValueError(f"{self.name}: operating_time must be positive.")
        if operating_time < self.current_operating_time:
            logger.error(f"{self.name}: operating_time less than the current operating_time.")
            raise ValueError(f"{self.name}: operating_time less than the current operating_time.")
        if operating_time > self.max_operating_time:
            logger.error(f"{self.name}: operating_time exceeds the maximum operating_time.")
            raise ValueError(f"{self.name}: operating_time exceeds the maximum operating_time.")

        self._operating_time = operating_time
    
    def update_state(self):
        """ モジュールの故障 """
        if self.current_operating_time == self.max_operating_time:
            self._state = ModuleState.ERROR
        else:
            self._state = ModuleState.ACTIVE

    def __str__(self):
        """ モジュールの簡単な情報を文字列として表示 """
        return f"Module({self.name}, {self.state.name}, Battery: {self.battery}/{self.type.max_battery})"

    def __repr__(self):
        """ デバッグ用の詳細な表現 """
        return f"Module(name={self.name}, type={self.type.name}, state={self.state.name}, battery={self.battery})"