import numpy as np
from modutask.core import *
from modutask.simulator.agent import RobotAgent


class Simulator:
    def __init__(self, tasks: dict[str, BaseTask], robots: dict[str, Robot], 
                 task_priorities: dict[str, list[str]], 
                 scenarios: list[BaseRiskScenario], simulation_map: SimulationMap, 
                 max_step: int):
        self.tasks = tasks
        self.agents = {robot.name: RobotAgent(robot, task_priorities[robot.name]) for _, robot in robots.items()}
        self.simulation_map = simulation_map
        self.scenarios = scenarios
        for scenario in self.scenarios:
            scenario.initialize()
        self.max_step = max_step
        # シミュレーションの結果保存用
        self.agent_history = []
        self.task_history = []

    def run_simulation(self):
        for current_step in range(self.max_step):
            # 各エージェントのループ
            for _, agent in self.agents.items():
                # 稼働不可ならスキップ
                if agent.check_inactive():
                    continue
                # 充電が必要かチェック
                agent.decide_recharge(self.simulation_map.charge_stations)
                # タスクの割り当て
                agent.update_task(self.tasks)
                # 移動が必要なエージェントは移動
                agent.try_travel()
            # 各タスクを一斉に実行
            for _, task in self.tasks.items():
                if task.update():
                    for robot in task.assigned_robot:
                        self.agents[robot.name].set_state_work()  # タスクを実行したエージェントのみ
                task.release_robot()
            # 充電を実行
            for _, station in self.simulation_map.charge_stations.items():
                station.update()

            # タスクをエージェントの目標から消す
            # 充電以外
            for _, agent in self.agents.items():
                agent.reset_task()
                agent.set_state_idle()
                agent.robot.update_state(scenarios=self.scenarios)  # モジュールの故障判定



