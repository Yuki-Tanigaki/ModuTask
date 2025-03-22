from dataclasses import dataclass
from typing import Tuple, Union
from enum import Enum
import logging
import numpy as np
from .utils import make_coodinate_to_tuple

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
                 battery: float, state: ModuleState = ModuleState.ACTIVE):
        self._type = module_type  # モジュールの種類
        self._name = name  # モジュール名
        self._coordinate = make_coodinate_to_tuple(coordinate)  # モジュールの座標
        if battery > module_type.max_battery:
            logger.error(f"{name}: battery exceeds the maximum capacity.")
            raise ValueError(f"{name}: battery exceeds the maximum capacity.")
        self._battery = battery  # 現在のバッテリー残量
        self._state = state  # モジュールの状態

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
    def state(self):
        return self._state

    def update_coordinate(self, coordinate: Union[Tuple[float, float], np.ndarray, list]):
        """ モジュールの座標を更新 """
        self._coordinate = make_coodinate_to_tuple(coordinate)
    
    def update_battery(self, battery_variation: float):
        """ モジュールのバッテリーを更新 """
        if self.state == ModuleState.ERROR:
            logger.error(f"{self.name}: try update battery of malfunctioning module.")
            raise RuntimeError(f"{self.name}: try update battery of malfunctioning module.")
        battery = self.battery + battery_variation
        if battery > self.type.max_battery:
            battery = self.type.max_battery
        elif battery < 0:
            battery = 0
        self._battery = battery
    
    def update_state(self, state: ModuleState):
        """ モジュールの状態を更新 """
        self._state = state

    def __str__(self):
        """ モジュールの簡単な情報を文字列として表示 """
        return f"Module({self.name}, {self.state.name}, Battery: {self.battery}/{self.type.max_battery})"

    def __repr__(self):
        """ デバッグ用の詳細な表現 """
        return f"Module(name={self.name}, type={self.type.name}, state={self.state.name}, battery={self.battery})"