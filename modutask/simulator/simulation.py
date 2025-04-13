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
            # 移動が必要なエージェントは移動
            if agent.is_on_site():
                agent.ready()
            else:
                agent.travel(self.scenarios)

        # 各タスクを一斉に実行
        for _, task in self.tasks.items():
            # if isinstance(task, Assembly):
            total_assigned_performance = {attr: 0 for attr in PerformanceAttributes}
            for robot in task.assigned_robot:
                for attr, value in robot.type.performance.items():
                    total_assigned_performance[attr] += value
            if task.update():
                for robot in task.assigned_robot:
                    self.agents[robot.name].set_state_work(self.scenarios)  # タスクを実行したエージェントのみ
            task.release_robot()
        # 充電を実行
        for _, station in self.simulation_map.charge_stations.items():
            station.update()

        # タスクをエージェントの目標から消す
        # 充電以外
        for _, agent in self.agents.items():
            agent.reset_task()
            agent.set_state_idle()
            agent.robot.update_state()  # ロボット状態更新
    
    def total_remaining_workload(self) -> float:
        # 各タスクの未完了仕事量を合計
        return sum(task.total_workload - task.completed_workload for task in self.tasks.values()) 

    def variance_remaining_workload(self) -> float:
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
        return float(distances_squared / np.sum(weights))

    def variance_operating_time(self) -> float:
        all_modules = []
        for agent in self.agents.values():
            for module in agent.robot.component_mounted:
                all_modules.append(module)
        operating_times = np.array([module.operating_time for module in all_modules])
        return float(np.var(operating_times))

