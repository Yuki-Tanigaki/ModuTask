import argparse
import numpy as np
from typing import Dict, Type, List
from modutask.core import *
from modutask.simulator.agent import RobotAgent


class Initializer:
     def __init__(self, tasks: Dict[str, BaseTask], robots: Dict[str, Robot]):
         pass

class Simulator:
    def __init__(self, tasks: Dict[str, BaseTask], robots: Dict[str, Robot], task_priority: Dict[Robot, List[str]]):

        # シミュレーションの結果保存用
        self.agent_history = []
        self.task_history = []

    def run_simulation(self):
        simulation_rng = np.random.default_rng(self.seed)  # 乱数器にシード値を設定
        
        # シミュレーションエージェントの生成
        agents = {robot.name: RobotAgent(robot, self.battery_level_to_recharge) for _, robot in self.robots.items()}

        for current_step in range(self.max_step):
            # 各エージェントのループ
            for _, agent in agents.items():
                # 稼働不可ならスキップ
                if agent.check_inactive():
                    continue
                # 充電が必要かチェック
                agent.decide_recharge(self.charge_stations)
                # タスクの割り当て
                agent.update_task(self.tasks)
                # 移動が必要なエージェントは移動
                agent.try_travel()
            # 各タスクを一斉に実行
            for t, task in self.tasks.items():
                if task.update():
                    for robot in task.assigned_robot:
                        agents[robot.name].set_state_work()  # タスクを実行したエージェントのみ
                task.release_robot()
            # 充電を実行
            for station in self.charge_stations:
                station.update()
            
            # TODO: 故障を実装


            # タスクをエージェントの目標から消す
            # 充電以外
            for _, agent in agents.items():
                agent.reset_task()
                agent.set_state_idle()
                agent.robot.update_state()



