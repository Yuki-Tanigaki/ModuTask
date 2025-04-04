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
    
    def total_remaining_workload(self):
        return sum(task.total_workload - task.completed_workload for task in self.tasks.values()) 

    def variance_remaining_workload(self):
        # 各タスクの座標と未完了仕事量を抽出
        coordinates = []
        weights = []

        for task in self.tasks.values():
            remaining = task.total_workload - task.completed_workload
            coordinates.append(np.array(task.coordinate))
            weights.append(remaining)

        coordinates = np.array(coordinates)
        weights = np.array(weights)

        # 重心（重み付き平均座標）を計算
        weighted_center = np.average(coordinates, axis=0, weights=weights)

        # 各点の重心からの距離の二乗 × 重み の合計を求める
        distances_squared = np.sum(weights * np.sum((coordinates - weighted_center) ** 2, axis=1))

        # 重み付き分散（距離に基づく残タスク分散）
        return distances_squared / np.sum(weights)

    def variance_operating_time(self):
        all_modules = []
        for agent in self.agents.values():
            for module in agent.robot.component_mounted:
                all_modules.append(module)
        operating_times = np.array([module.operating_time for module in all_modules])
        return np.var(operating_times)

