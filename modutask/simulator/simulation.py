import numpy as np
from modutask.core import *
from modutask.simulator.agent import RobotAgent


class Simulator:
    def __init__(self, tasks: dict[str, BaseTask], robots: dict[str, Robot], task_priorities: dict[str, list[str]], 
                 scenarios: list[BaseRiskScenario], simulation_map: SimulationMap):
        self.tasks = tasks
        self.agents = {robot.name: RobotAgent(robot, task_priorities[robot.name]) for _, robot in robots.items()}
        self.simulation_map = simulation_map
        self.scenarios = scenarios
        for scenario in self.scenarios:
            scenario.initialize()

    def run_simulation(self):
        # 各エージェントのループ
        for _, agent in self.agents.items():
            # 稼働不可ならスキップ
            if agent.is_inactive():
                continue
            # 充電が必要かチェック
            agent.decide_recharge(self.simulation_map.charge_stations)
            # タスクの割り当て
            agent.update_task(self.tasks)
            if agent.assigned_task is None:  # 全タスク終了
                continue
            # 移動が必要なエージェントは移動
            if agent.is_on_site():
                agent.ready()
            else:
                agent.travel(self.scenarios)

        # 各タスクを一斉に実行
        for _, task in self.tasks.items():
            # if isinstance(task, Manufacture):
            #     print(task.name)
            #     print(task.required_performance)
            #     print(len(task.assigned_robot))
            #     total_assigned_performance = {attr: 0 for attr in PerformanceAttributes}
            #     for robot in task.assigned_robot:
            #         for attr, value in robot.type.performance.items():
            #             total_assigned_performance[attr] += value
            #     print(total_assigned_performance)
            if task.update():
                for robot in task.assigned_robot:
                    self.agents[robot.name].set_state_work(self.scenarios)  # タスクを実行したエージェントのみ
            # else:
            #     if not isinstance(task, TransportModule):
            #         print(task.name)
            #         print(task.required_performance)
            #         print(task.assign_robot)
            task.release_robot()
        # 充電を実行
        for _, station in self.simulation_map.charge_stations.items():
            station.update()
            station.release_robot()

        # タスクをエージェントの目標から消す
        # 充電以外
        for _, agent in self.agents.items():
            agent.reset_task()
            agent.set_state_idle()
            agent.robot.update_state()  # ロボット状態更新


