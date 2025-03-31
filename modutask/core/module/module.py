from dataclasses import dataclass
from typing import Union
from enum import Enum
import copy, logging
import numpy as np
from modutask.core.risk_scenario import BaseRiskScenario
from modutask.core.utils import make_coodinate_to_tuple
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)

class ModuleState(Enum):
    """ モジュールの状態を表す列挙型 """
    ACTIVE = (0, 'green')  # 正常
    ERROR = (1, 'gray')  # 故障
    
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
    def __init__(self, module_type: ModuleType, name: str, coordinate: Union[tuple[float, float], np.ndarray, list], 
                 battery: float, operating_time: float, state: ModuleState):
        self._type = module_type  # モジュールの種類
        self._name = name  # モジュール名
        self._coordinate = make_coodinate_to_tuple(coordinate)  # モジュールの座標
        self._battery = battery  # 現在のバッテリー残量
        self._operating_time = operating_time  # モジュールの稼働時間
        self._state = state  # モジュールの状態
        
        if battery > module_type.max_battery:
            raise_with_log(ValueError, f"Battery exceeds the maximum capacity: {name}.")
        if battery < 0.0:
            raise_with_log(ValueError, f"Battery must be positive: {name}.")
        if operating_time < 0.0:
            raise_with_log(ValueError, f"Operating_time must be positive: {name}.")

    @property
    def type(self) -> ModuleType:
        return self._type

    @property
    def name(self) -> str:
        return self._name

    @property
    def coordinate(self) -> tuple[float, float]:
        return self._coordinate
    
    @property
    def battery(self) -> float:
        return self._battery
    
    @property
    def operating_time(self) -> float:
        return self._operating_time
    
    @property
    def state(self) -> ModuleState:
        return self._state

    @coordinate.setter
    def coordinate(self, coordinate: Union[tuple[float, float], np.ndarray, list]):
        """ モジュールの座標を更新 """
        self._coordinate = copy.deepcopy(make_coodinate_to_tuple(coordinate))
    
    @battery.setter
    def battery(self, battery: float):
        """ モジュールのバッテリーを更新 """
        if self.state == ModuleState.ERROR:
            raise_with_log(RuntimeError, f"Try update battery of malfunctioning module: {self.name}.")
        if battery > self.type.max_battery:
            raise_with_log(ValueError, f"Battery exceeds the maximum capacity: {self.name}.")
        if battery < 0.0:
            raise_with_log(ValueError, f"Battery must be positive: {self.name}.")

        self._battery = battery
    
    @operating_time.setter
    def operating_time(self, operating_time: float):
        """ モジュールの稼働量を更新 """
        if self.state == ModuleState.ERROR:
            raise_with_log(RuntimeError, f"Try update runtime of malfunctioning module: {self.name}.")
        if operating_time < 0.0:
            raise_with_log(ValueError, f"Operating_time must be positive: {self.name}.")
        if operating_time < self.operating_time:
            raise_with_log(ValueError, f"Operating_time less than the current operating_time: {self.name}.")

        self._operating_time = operating_time
    
    def is_active(self) -> bool:
        """ モジュールが使用可能か """
        return self.state == ModuleState.ACTIVE

    def update_state(self, scenarios: list[BaseRiskScenario]):
        """ モジュール状態の更新 """
        self._state = ModuleState.ACTIVE
        for scenario in scenarios:
            if scenario.malfunction_module(self):
                self._state = ModuleState.ERROR
                return

    def __str__(self):
        """ モジュールの簡単な情報を文字列として表示 """
        return f"Module({self.name}, {self.state.name}, Battery: {self.battery}/{self.type.max_battery})"

    def __repr__(self):
        """ デバッグ用の詳細な表現 """
        return f"Module(name={self.name}, type={self.type.name}, state={self.state.name}, battery={self.battery})"