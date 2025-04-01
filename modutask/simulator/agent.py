from enum import Enum
from collections import Counter
import copy, sys, math
import numpy as np
import pandas as pd

from modutask.core import *

class AgentState(Enum):
    """ エージェントの状態を表す列挙型 """
    IDLE = (0, 'green')  # 待機中
    MOVE = (1, 'blue')  # 移動中
    CHARGE = (2, 'orange')  # 充電中
    ASSIGNED = (3, 'pink')  # 配置中
    WORK = (4, 'red')  # 仕事中
    NO_ENERGY = (5, 'gray')  # バッテリー不足で稼働不可
    DEFECTIVE = (6, 'purple')  # 部品不足で稼働不可

    @property
    def color(self):
        """ ロボットの状態に対応する色を取得 """
        return self.value[1]

class RobotAgent:
    def __init__(self, robot: Robot, task_priority: list[BaseTask]):
        self.robot = robot
        self.task_priority = task_priority
        self.assigned_task = None
        self.state = AgentState.IDLE

    def check_inactive(self):
        """ ロボットの稼働状態を確認 """
        if self.robot.state == RobotState.NO_ENERGY:
            self.state = AgentState.NO_ENERGY
            return True
        elif self.robot.state == RobotState.DEFECTIVE:
            self.state = AgentState.DEFECTIVE
            return True
        else:
            return False

    def decide_recharge(self, charge_stations: dict[str, Charge]):
        # 充電タスクが既に割り当て済みならスキップ
        if isinstance(self.assigned_task, Charge):
            return
        # バッテリーが設定以下なら充電に向かう
        if self.robot.total_battery() < self.robot.type.recharge_trigger:
            # 現在地から最も近くの充電スペースを探す
            min_dist = sys.float_info.max
            min_station = None
            for _, station in charge_stations.items():
                dist = math.sqrt(sum((x - y) ** 2 for x, y in zip(station.coordinate, self.robot.coordinate)))
                if min_dist > dist:
                    min_dist = dist
                    min_station = station
            self.assigned_task = min_station

    def update_task(self, tasks: dict[str, BaseTask]):
        # すでにタスクが割り当てられている場合はスキップ
        if self.assigned_task is not None:
            return
        # 優先順位で目標タスクを決定
        for task_name in self.task_priority:
            task = tasks[task_name]
            # タスクが完了済みなら次のタスクに
            if task.is_completed():
                continue
            self.assigned_task = task
            return

    def try_travel(self):
        if self.assigned_task.coordinate != self.robot.coordinate:
            # 目的地と現在の座標が異なるならエージェントを移動
            self.state = AgentState.MOVE
            self.robot.travel(self.assigned_task.coordinate)
        else:
            # 目的地と現在の座標が同じなら配置済みロボットのリストに追加
            self.assigned_task.assign_robot(self.robot)
            if isinstance(self.assigned_task, Charge):
                # 充電タスクならエージェントの状態を充電に変更
                self.state = AgentState.CHARGE
            else:
                # 通常タスクならエージェントの状態を配置中に変更
                self.state = AgentState.ASSIGNED
    
    def reset_task(self):
        if isinstance(self.assigned_task, Charge):
            # 充電タスクならフル充電までタスクを固定
            if self.robot.check_battery_full():
                self.assigned_task = None
        else:
            self.assigned_task = None

    def set_state_work(self):
        self.state = AgentState.WORK
    
    def set_state_idle(self):
        self.state = AgentState.IDLE
