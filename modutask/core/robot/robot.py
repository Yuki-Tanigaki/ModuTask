from dataclasses import dataclass
from typing import Any, Union, Optional
from numpy.typing import NDArray
from enum import Enum
import logging
import numpy as np
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.module.module import Module, ModuleType
from modutask.core.utils.coodinate_utils import is_within_range, make_coodinate_to_tuple
from modutask.core.risk_scenario import BaseRiskScenario
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)

class RobotState(Enum):
    """ ロボットの状態を表す列挙型 """
    ACTIVE = (0, 'green')  # 正常
    NO_ENERGY = (1, 'yellow')  # バッテリー不足で稼働不可
    DEFECTIVE = (2, 'purple')  # 部品不足で稼働不可

    @property
    def color(self) -> str:
        """ ロボットの状態に対応する色を取得 """
        return self.value[1]

@dataclass
class RobotType:
    """ ロボットの種類 """
    name: str  # ロボット名
    required_modules: dict[ModuleType, int]  # 構成に必要なモジュール数
    performance: dict[PerformanceAttributes, int]  # ロボットの各能力値
    power_consumption: float  # ロボットの消費電力
    recharge_trigger: float  # 充電に戻るバッテリー量の基準

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RobotType):
            return NotImplemented
        return self.name == other.name

def has_duplicate_module(robots: dict[str, 'Robot']) -> None:
    """
    全ロボットのモジュール名の重複をチェックする関数
    """
    all_module_names = []
    for robot in robots.values():
        module_names = [module.name for module in robot.component_required]
        all_module_names.extend(module_names)

    duplicates = set(name for name in all_module_names if all_module_names.count(name) > 1)
    if duplicates:
        raise_with_log(ValueError, f"Duplicate module names across robots: {duplicates}.")

class Robot:
    """ ロボットのクラス """
    def __init__(self, robot_type: RobotType, name: str, coordinate: Union[tuple[float, float], NDArray[np.float64], list[float]], 
                 component: list[Module]):
        self._type = robot_type  # ロボットの種類
        self._name = name  # ロボット名
        self._coordinate = make_coodinate_to_tuple(coordinate)  # 現在の座標
        self._component_mounted = list(component)  # 搭載モジュール
        self._component_required = list(component)  # 必要モジュール
        for module_type, required_num in self.type.required_modules.items():
            # component_required内のモジュール数が指定されたタイプと一致しているかチェック
            num = len([module for module in self._component_required if module.type == module_type])
            if num == required_num:
                continue
            else:
                raise_with_log(ValueError, f"{module_type.name} is required {required_num} but {num} is assigned: {self.name}")

        self.update_state()

    @property
    def type(self) -> RobotType:
        return self._type

    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    @property
    def coordinate(self) -> tuple[float, float]:
        return self._coordinate
    
    @property
    def component_mounted(self) -> list[Module]:
        return self._component_mounted

    @property
    def component_required(self) -> list[Module]:
        return self._component_required

    @property
    def state(self) -> RobotState:
        if self._state is None:
            raise_with_log(RuntimeError, f"State is not initialized: {self.name}.")
        return self._state

    def total_battery(self) -> float:
        """ 残りバッテリー量を算出 """
        total = 0.0
        for module in self.component_mounted:
            total += module.battery
        return total
    
    def total_max_battery(self) -> float:
        """ フル充電したときのバッテリー量を算出 """
        total = 0.0
        for module in self.component_mounted:
            total += module.type.max_battery
        return total
    
    def missing_components(self) -> list[Module]:
        """ 不足中のモジュールをリスト化 """
        return list(set(self.component_required) - set(self.component_mounted))

    def is_battery_sufficient(self) -> bool:
        """ バッテリーが使用電力以上かチェック """
        return self.total_battery() > self.type.power_consumption
    
    def is_battery_full(self) -> bool:
        """ バッテリーが満タンかチェック """
        return self.total_battery() == self.total_max_battery()

    def draw_battery_power(self) -> None:
        """ 1ステップの行動でバッテリーを消費 """
        if not self.is_battery_sufficient():
            raise_with_log(RuntimeError, f"Battery level is less than the amount needed for action: {self.name}.")
        left = self.type.power_consumption
        for module in reversed(self.component_mounted):
            if left <= module.battery:
                module.battery = module.battery-left
                return
            else:
                left -= module.battery
                module.battery = 0.0

    def charge_battery_power(self, charging_speed: float) -> None:
        """ 1ステップの充電 """
        left_charge_power = charging_speed
        for module in self.component_mounted:   # 充電順は先頭から
            remaining_capacity = module.type.max_battery - module.battery
            if remaining_capacity < left_charge_power:
                module.battery = module.type.max_battery  # フル充電
                left_charge_power -= remaining_capacity
            else:
                module.battery = module.battery + left_charge_power
                return
    
    def operate(self, scenarios: Optional[list[BaseRiskScenario]]) -> None:
        """ 搭載モジュールを稼働させる """
        if self.state != RobotState.ACTIVE:
            raise_with_log(RuntimeError, f"Not ACTIVE: {self.name}.")
        
        self.draw_battery_power()
        for module in self.component_mounted:
            module.operating_time = module.operating_time + 1.0
        
        """ ロボットのモジュールに故障判定 """
        if scenarios is not None:  # 構成モジュールの状態を更新
            for module in self.component_mounted:
                module.update_state(scenarios)

    def travel(self, target_coordinate: tuple[float, float]) -> None:
        """ 目的地点に向けて移動 """
        v = np.array(target_coordinate) - np.array(self.coordinate)
        mob = self.type.performance[PerformanceAttributes.MOBILITY]
        if np.linalg.norm(v) < mob:  # 距離が移動能力以下
            self._coordinate = make_coodinate_to_tuple(target_coordinate)
        else:
            self._coordinate = make_coodinate_to_tuple(self.coordinate + mob*v/np.linalg.norm(v))
        for module in self.component_mounted:
            module.coordinate = self.coordinate
    
    def mount_module(self, module: Module) -> None:
        """ モジュールを搭載 """
        if not module.is_active():
            raise_with_log(RuntimeError, f"{module.name} is failed to mount due to a malfunction: {self.name}.")
        if not is_within_range(module.coordinate, self.coordinate):
            raise_with_log(RuntimeError, f"{module.name} is failed to mount due to a coordinate mismatch: {self.name}.")
        if module not in self.component_required:
            raise_with_log(RuntimeError, f"{module.name} not found in component_required: {self.name}.")
        self._component_mounted.append(module)

    def update_state(self) -> None:
        """ ロボットの状態を更新 """
        self._component_mounted = [module for module in self.component_mounted if module.is_active()]
        self._component_mounted = [module for module in self._component_mounted if is_within_range(module.coordinate, self.coordinate)]

        self._state = RobotState.ACTIVE
        if len(self.missing_components()) != 0:
            self._state = RobotState.DEFECTIVE
            return
        if not self.is_battery_sufficient():
            self._state = RobotState.NO_ENERGY
            return
    
    def __str__(self) -> str:
        """ ロボットの簡単な情報を文字列として表示 """
        return f"Robot({self.name}, {self.state.name}, {self.coordinate})"

    def __repr__(self) -> str:
        """ デバッグ用の詳細な表現 """
        return (f"Robot(name={self.name}, type={self.type.name}, state={self.state.name}, "
                f"coordinate={self.coordinate}, modules={len(self.component_mounted)})")
    
    def __deepcopy__(self, memo: dict[int, Any]) -> "Robot":
        raise_with_log(RuntimeError, f"Robot cannot deepcopy: {self.name}.")