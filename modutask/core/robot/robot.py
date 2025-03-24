from dataclasses import dataclass
from typing import Dict, List, Tuple, Union
from enum import Enum
import logging
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

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other: 'ModuleType') -> bool:
        return self.name == other.name

class Robot:
    """ ロボットのクラス """
    def __init__(self, robot_type: "RobotType", name: str, coordinate: Tuple[float, float], 
                 component_installed: List["Module"], component_required: List["Module"], task_priority: List[str]):
        self._type = robot_type  # ロボットの種類
        self._name = name  # ロボット名
        self._coordinate = make_coodinate_to_tuple(coordinate)  # 現在の座標
        self._component_installed = component_installed  # 搭載モジュール
        self._component_required = component_required  # 必要モジュール

        self._state = RobotState.ACTIVE # ロボットの状態（ACTIVEで初期化）

        # ERRORな搭載モジュールはリストから除外
        self._component_installed = [module for module in self._component_installed if module.state != ModuleState.ERROR]
        # 座標の異なるモジュールをリストから除外
        self._component_installed = [module for module in self._component_installed if module.coordinate == self.coordinate]
        # 構成に必要なモジュール数を満たしているかチェック
        if self.list_unavailable_components():
            self._state = RobotState.DEFECTIVE
        # バッテリーが使用電力以上かチェック
        if self.check_battery_shortage():
            self._state = RobotState.NO_ENERGY
        
        self._task_priority = task_priority  # タスクの優先順位リスト

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
    def component_installed(self):
        return self._component_installed

    @property
    def component_required(self):
        return self._component_required

    @property
    def state(self):
        return self._state

    @property
    def task_priority(self):
        return self._task_priority

    def total_battery(self):
        sum = 0
        for module in self._component:
            sum += module.battery
        return sum
    
    def total_max_battery(self):
        sum = 0
        for module in self._component:
            sum += module.type.max_battery
        return sum
    
    def missing_components(self):
        return list(set(self.component_required) - set(self.component_installed))

    def list_unavailable_components(self) -> bool:
        """ 構成に必要なモジュール数を満たしているかチェック """
        for module_type, required_num in self.type.required_modules.items():
            num = len([module for module in self._component if module.type == module_type])
            if num >= required_num:
                continue
            else:
                return True
        return False
        # """
        # 必要数に対して不足しているモジュール種別と数を返す。
        # """
        # # ACTIVEなモジュールのみカウント
        # active_modules = [module.type.name for module in self.component if module.state == ModuleState.ACTIVE]
        # available_counts = Counter(active_modules)

        # # 不足分の算出
        # shortages = {}
        # for module_name, required_count in required.items():
        # available_count = available_counts.get(module_name, 0)
        # if available_count < required_count:
        #     shortages[module_name] = required_count - available_count

        return shortages

    def check_battery_shortage(self) -> bool:
        """ バッテリーが使用電力以上かチェック """
        return self.total_battery() < self.type.power_consumption
    
    def check_battery_full(self) -> bool:
        """ バッテリーが満タンかチェック """
        return self.total_battery() == self.total_max_battery()

    def draw_battery_power(self):
        if self.check_battery_shortage():
            raise ValueError("Battery level is less than the amount needed for action.")
        left = self.type.power_consumption
        for module in reversed(self.component):
            if left <=  module.battery:
                module.update_battery(battery_variation=-left)
                return
            else:
                module.update_battery(battery_variation=-module.battery)
                left -= module.battery

    def charge_battery_power(self, charging_speed: float) -> None:
        left_charge_power = charging_speed
        # モジュールを順番に充電
        for module in self.component:
            remaining_capacity = module.type.max_battery - module.battery
            if remaining_capacity < left_charge_power:
                module.update_battery(battery_variation=remaining_capacity)  # フル充電
                left_charge_power -= remaining_capacity
            else:
                module.update_battery(battery_variation=left_charge_power)
                return

    def travel(self, target_coordinate): # 移動
        self.draw_battery_power()
        v = np.array(target_coordinate) - np.array(self.coordinate)
        mob = self.type.performance[PerformanceAttributes.MOBILITY]
        if np.linalg.norm(v) < mob:  # 距離が移動能力以下
            self.update_coordinate(target_coordinate)
            return np.linalg.norm(v)
        else:
            self.update_coordinate(self.coordinate + mob*v/np.linalg.norm(v))
            return mob

    def update_coordinate(self, coordinate: Union[Tuple[float, float], np.ndarray, list]):
        """ ロボットの座標を更新し、搭載モジュールの座標も同期 """
        self._coordinate = copy.deepcopy(make_coodinate_to_tuple(coordinate))
        for module in self._component:
            module.update_coordinate(copy.deepcopy(self._coordinate))
    
    def try_assign_module(self, module: "Module"):
        """ モジュールを搭載 """
        # ModuleStateがERRORでないことを確認
        if module.state == ModuleState.ERROR:
            return False
        # ロボットの座標とモジュールの座標が一致しているかチェック
        if module.coordinate != self.coordinate:
            return False
        self._component.append(module)
        return True
    
    def malfunction(self, module: "Module"):
        """ モジュールの故障 """
        module.update_state(ModuleState.ERROR)
        self._component.remove(module)
    
    def install_module(self, module: "Module"):
        """ モジュールを組み込む """
        if module.coordinate != self.coordinate:
            logger.error(f"{self.name}: {module.name} is in a different location.")
            raise ValueError(f"{self.name}: {module.name} is in a different location.")
        self._component_installed.append(module)
    
    def update_state(self):
        """ ロボットの状態を更新 """
        # 構成に必要なモジュール数を満たしているかチェック
        if self._check_component_shortage():
            self._state = RobotState.DEFECTIVE
        # バッテリーが使用電力以上かチェック
        if self.check_battery_shortage():
            self._state = RobotState.NO_ENERGY

    def update_task_priority(self, task_priority: List[str]):
        """ タスクの優先順位リストを更新 """
        self._task_priority = task_priority

    def __str__(self):
        """ ロボットの簡単な情報を文字列として表示 """
        return f"Robot({self.name}, {self._state.name}, Pos: {self.coordinate})"

    def __repr__(self):
        """ デバッグ用の詳細な表現 """
        return (f"Robot(name={self.name}, type={self.type.name}, state={self._state.name}, "
                f"coordinate={self.coordinate}, modules={len(self._component)}, "
                f"task_priority={len(self._task_priority)})")