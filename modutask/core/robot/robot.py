from dataclasses import dataclass
from typing import Dict, List, Tuple, Union
from enum import Enum
import copy, logging
import numpy as np
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.module.module import Module, ModuleState, ModuleType
from modutask.core.utils import make_coodinate_to_tuple

logger = logging.getLogger(__name__)

class RobotState(Enum):
    """ ロボットの状態を表す列挙型 """
    ACTIVE = (0, 'green')  # 正常
    NO_ENERGY = (1, 'yellow')  # バッテリー不足で稼働不可
    DEFECTIVE = (2, 'purple')  # 部品不足で稼働不可

    @property
    def color(self):
        """ ロボットの状態に対応する色を取得 """
        return self.value[1]

@dataclass
class RobotType:
    """ ロボットの種類 """
    name: str  # ロボット名
    required_modules: Dict[ModuleType, int]  # 構成に必要なモジュール数
    performance: Dict[PerformanceAttributes, int]  # ロボットの各能力値
    power_consumption: float  # ロボットの消費電力
    recharge_trigger: float  # 充電に戻るバッテリー量の基準

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other: 'ModuleType') -> bool:
        return self.name == other.name

class Robot:
    """ ロボットのクラス """
    def __init__(self, robot_type: RobotType, name: str, coordinate: Union[Tuple[float, float], np.ndarray, list], 
                 component: List[Module]):
        self._type = robot_type  # ロボットの種類
        self._name = name  # ロボット名
        self._coordinate = make_coodinate_to_tuple(coordinate)  # 現在の座標
        self._component_mounted = list(component)  # 搭載モジュール
        self._component_required = list(component)  # 必要モジュール
        """ 指定されたタイプと必要モジュールが一致しているかチェック """
        for module_type, required_num in self.type.required_modules.items():
            num = len([module for module in self._component_required if module.type == module_type])
            if num == required_num:
                continue
            else:
                logger.error(f"{self.name}: {module_type.name} is required {required_num} but {num} is mounted.")
                raise ValueError(f"{self.name}: {module_type.name} is required {required_num} but {num} is mounted.")

        self._state = RobotState.ACTIVE # ロボットの状態（ACTIVEで初期化）
        # ERRORな搭載モジュールはリストから除外
        self._component_mounted = [module for module in self._component_mounted if module.state != ModuleState.ERROR]
        # 座標の異なるモジュールをリストから除外
        self._component_mounted = [module for module in self._component_mounted if module.coordinate == self.coordinate]
        # 構成に必要なモジュール数を満たしているかチェック
        if len(self.missing_components()) != 0:
            self._state = RobotState.DEFECTIVE
        # バッテリーが使用電力以上かチェック
        if self.is_battery_sufficient():
            self._state = RobotState.NO_ENERGY

    @property
    def type(self) -> RobotType:
        return self._type

    @property
    def name(self) -> str:
        return self._name

    @property
    def coordinate(self) -> Tuple[float, float]:
        return self._coordinate
    
    @property
    def component_mounted(self) -> List[Module]:
        return self._component_mounted

    @property
    def component_required(self) -> List[Module]:
        return self._component_required

    @property
    def state(self) -> RobotState:
        return self._state

    @coordinate.setter
    def coordinate(self, coordinate: Union[Tuple[float, float], np.ndarray, list]):
        """ ロボットの座標を更新し、搭載モジュールの座標も同期 """
        self._coordinate = copy.deepcopy(make_coodinate_to_tuple(coordinate))
        for module in self.component_mounted:
            module.coordinate = self.coordinate

    def total_battery(self) -> float:
        """ 残りバッテリー量を算出 """
        sum = 0
        for module in self.component_mounted:
            sum += module.battery
        return sum
    
    def total_max_battery(self) -> float:
        """ フル充電したときのバッテリー量を算出 """
        sum = 0
        for module in self.component_mounted:
            sum += module.type.max_battery
        return sum
    
    def missing_components(self) -> List[Module]:
        """ 不足中のモジュールをリスト化 """
        return list(set(self.component_required) - set(self.component_mounted))

    def is_battery_sufficient(self) -> bool:
        """ バッテリーが使用電力以上かチェック """
        return self.total_battery() < self.type.power_consumption
    
    def is_battery_full(self) -> bool:
        """ バッテリーが満タンかチェック """
        return self.total_battery() == self.total_max_battery()

    def draw_battery_power(self):
        """ 1ステップの行動でバッテリーを消費 """
        if self.is_battery_sufficient():
            logger.error(f"{self.name}: Battery level is less than the amount needed for action.")
            raise RuntimeError(f"{self.name}: Battery level is less than the amount needed for action.")
        left = self.type.power_consumption
        for module in reversed(self.component_mounted):
            if left <= module.battery:
                module.battery = module.battery-left
                return
            else:
                left -= module.battery
                module.battery = 0.0

    def charge_battery_power(self, charging_speed: float):
        """ 1ステップの充電 """
        left_charge_power = charging_speed
        # モジュールを順番に充電
        for module in self.component_mounted:
            remaining_capacity = module.type.max_battery - module.battery
            if remaining_capacity < left_charge_power:
                module.battery = module.type.max_battery  # フル充電
                left_charge_power -= remaining_capacity
            else:
                module.battery = module.battery + left_charge_power
                return

    def travel(self, target_coordinate: Tuple[float, float]): # 移動
        """ 目的地点に向けて移動 """
        self.draw_battery_power()
        v = np.array(target_coordinate) - np.array(self.coordinate)
        mob = self.type.performance[PerformanceAttributes.MOBILITY]
        if np.linalg.norm(v) < mob:  # 距離が移動能力以下
            self.coordinate = target_coordinate
        else:
            self.coordinate = self.coordinate + mob*v/np.linalg.norm(v)
    
    def mount_module(self, module: Module):
        """ モジュールを搭載 """
        # ModuleStateがERRORなときエラー
        if module.state == ModuleState.ERROR:
            logger.error(f"{self.name}: {module.name} is failed to mount due to a malfunction.")
            raise RuntimeError(f"{self.name}: {module.name} is failed to mount due to a malfunction.")
        # ロボットの座標とモジュールの座標が一致しない場合エラー
        if module.coordinate != self.coordinate:
            logger.error(f"{self.name}: {module.name} is failed to mount due to a coordinate mismatch.")
            raise RuntimeError(f"{self.name}: {module.name} is failed to mount due to a coordinate mismatch.")
        # モジュールがcomponent_requiredに含まれていない場合エラー
        if module not in self.component_required:
            logger.error(f"{self.name}: {module.name} not found in component_required.")
            raise RuntimeError(f"{self.name}: {module.name} not found in component_required.")
        self._component_mounted.append(module)
        return True
        
    def update_state(self):
        """ ロボットの状態を更新 """
        # 構成モジュールの状態を更新
        for module in self.component_mounted:
            module.update_state()
        # ERRORな搭載モジュールはリストから除外
        self._component_mounted = [module for module in self._component_mounted if module.state != ModuleState.ERROR]
        # 構成に必要なモジュール数を満たしているかチェック
        if len(self.missing_components()) != 0:
            self._state = RobotState.DEFECTIVE
        # バッテリーが使用電力以上かチェック
        if self.is_battery_sufficient():
            self._state = RobotState.NO_ENERGY
        self._state = RobotState.ACTIVE

    def __str__(self):
        """ ロボットの簡単な情報を文字列として表示 """
        return f"Robot({self.name}, {self.state.name}, {self.coordinate})"

    def __repr__(self):
        """ デバッグ用の詳細な表現 """
        return (f"Robot(name={self.name}, type={self.type.name}, state={self.state.name}, "
                f"coordinate={self.coordinate}, modules={len(self.component_mounted)}, ")