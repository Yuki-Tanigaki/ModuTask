from enum import Enum
from collections import Counter
import copy, sys, math
import numpy as np
import pandas as pd

from modutask.robotic_system.core import RobotState, ModuleState, RobotPerformanceAttributes

class RobotAgent:
    def __init__(self, robot, battery_level_to_recharge):
        self.robot = robot
        self.battery_level_to_recharge = battery_level_to_recharge
        self.target_coordinate = None
        self.assigned_task = None
        self.to_be_charged = None
        self.movement = 0  # 移動量積算

    def decide_recharge(self, charge_station):
        # 充電中ならスキップ
        if self.assigned_task == "Charge":
            return
        # バッテリーが設定以下なら充電に向かう
        if self.robot.total_battery() < self.battery_level_to_recharge:
            # 現在地から最も近くの充電スペースを探す
            min_dist = sys.float_info.max
            min_station = None
            for _, station in charge_station.items():
                dist = math.sqrt(sum((x - y) ** 2 for x, y in zip(station.coordinate, self.robot.coordinate)))
                if min_dist > dist:
                    min_dist = dist
                    min_station = station
            self.target_coordinate = copy.deepcopy(tuple(map(float, min_station.coordinate)))
            self.assigned_task = "Charge"

    def update_task(self, task_priority, tasks):
        # すでにタスクが割り当てられている場合はスキップ
        if self.assigned_task is not None:
            return
        for task_name in self.robot.task_priority:
            task = tasks[task_name]
            # タスクが完了済みなら次のタスクに
            if task.completed_workload >= task.total_workload:
                continue
            # 依存タスクが完了していなければ次のタスクに
            tasks[task_name].check_dependencies_completed()
            if tasks[task_name].check_dependencies_completed():
                self.assigned_task = task
                return

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

    def check_inactive(self):
        """ ロボットの稼働状態を確認 """
        if self.robot.state == RobotState.NO_ENERGY or self.robot.state == RobotState.DEFECTIVE:
            return True
        else:
            return False
    
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
