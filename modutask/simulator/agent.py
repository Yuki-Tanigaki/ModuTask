from enum import Enum
from collections import Counter
import copy, sys, math
import numpy as np
import pandas as pd

from robotic_system.core import RobotState, ModuleState, RobotPerformanceAttributes

prob = 0.005

class SimulationAgent:
    def __init__(self, robot, battery_limit):
        self.robot = robot
        self.battery_limit = battery_limit
        self.target_coordinate = None
        self.assigned_task = None
        self.to_be_charged = None
        self.movement = 0  # 移動量積算

    def _calc_battery(self):
        sum = 0
        for module in self.robot.component:
            sum += module.battery[1] # バッテリー[最大量, 残量]
        return sum

    def break_limb(self):
        for module in self.robot.component:
            if module.type.name == 'Limb':
                module.state = ModuleState.MALFUNCTION
                break

    def travel(self): # 移動
        v = np.array(self.target_coordinate) - np.array(self.robot.coordinate)
        mob = self.robot.type.ability[RobotPerformanceAttributes.MOBILITY]
        if np.linalg.norm(v) < mob:  # 距離が移動能力以下
            self.robot.update_coordinate(self.target_coordinate)
            self.movement += np.linalg.norm(v)
        else:
            self.robot.update_coordinate(self.robot.coordinate + mob*v/np.linalg.norm(v))
            self.movement += mob

    def set_work(self):
        self.robot.state = RobotState.READY
    
    def work(self, simulation_rng):
        self.robot.state = RobotState.WORK
        self.target_coordinate = copy.deepcopy(self.assigned_task.coordinate)
        # バッテリー消耗
        for module in reversed(self.robot.component):
            if module.battery[1] >= 1:
                module.battery = (module.battery[0], module.battery[1]-1) # バッテリー消耗
                break

    def update_active(self):
        # 各モジュールの位置をチェック
        coordinate_list= []
        state_list = []
        for module in self.robot.component:
            coordinate_list.append(module.coordinate)
            state_list.append(module.state)
        # すべてのパーツがロボットの現在位置にあるかチェック
        assembe = all(all(x == y for x, y in zip(t, self.robot.coordinate)) for t in coordinate_list)
        # 全てのパーツが壊れていないかチェック
        malf = all(state != ModuleState.MALFUNCTION for state in state_list)
        # 全てのパーツが揃い，かつ壊れていない
        if assembe and malf:
            self.robot.state = RobotState.IDLE
        else:
            self.robot.state = RobotState.INACTIVE

    def check_battery(self, charge_station):
        # バッテリーが設定以下なら充電に向かう
        if self._calc_battery() < self.battery_limit:
            # 現在地から最も近くの充電スペースまでの距離を計算
            min_dist = sys.float_info.max
            for _, station_data in charge_station.items():
                dist = math.sqrt(sum((x - y) ** 2 for x, y in zip(station_data.coordinate, self.robot.coordinate)))
                if min_dist > dist:
                    min_dist = dist
                    self.to_be_charged = station_data
            self.target_coordinate = copy.deepcopy(np.array(self.to_be_charged.coordinate))
            self.assigned_task = None
            return False
        else:
            return True
    
    def check_travel(self, simulation_rng):
        # 目的地と現在地が一致しないなら移動
        if not np.array_equal(self.target_coordinate, self.robot.coordinate):
            self.robot.state = RobotState.MOVE
            # バッテリー消耗
            for module in reversed(self.robot.component):
                if module.battery[1] >= 1:
                    module.battery = (module.battery[0], module.battery[1]-1) # バッテリー消耗
                    break
            return True
        else:
            return False

    def charge(self):
        self.robot.state = RobotState.CHARGE
        left_charge_power = self.to_be_charged.chargingSpeed
        # モジュールを順番に充電
        for module in self.robot.component:
            remaining_capacity = module.battery[0] - module.battery[1] 
            if remaining_capacity < left_charge_power:
                module.battery = (module.battery[0], module.battery[0]) # フル充電
                left_charge_power += -remaining_capacity
            else:
                module.battery = (module.battery[0], module.battery[1]+left_charge_power)
                break
        # 充電完了か確認(充電は前から，使用は後ろから)
        if self.robot.component[-1].battery[0] == self.robot.component[-1].battery[1]:
            self.to_be_charged = None
            self.target_coordinate = None

    def update_task(self, task_priority, tasks):
        self.assigned_task = None
        self.target_coordinate = None
        # タスクを更新
        for task_name in task_priority:
            if task_name in tasks: # 実行不可能タスクは除去済み
                self.assigned_task = tasks[task_name]
                self.target_coordinate = copy.deepcopy(self.assigned_task.coordinate)
                return 
