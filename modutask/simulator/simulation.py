import argparse
from omegaconf import OmegaConf
import numpy as np
from modutask.robotic_system.core import *
from modutask.robotic_system.manager import *
from modutask.simulator.agent import RobotAgent

class Simulator:
    def __init__(self, property_file):
        properties = OmegaConf.load(property_file)

        self.manager = DataManager(properties)
        self.module_types = self.manager.load_module_types()
        self.robot_types = self.manager.load_robot_types(self.module_types)
        self.tasks = self.manager.load_tasks()
        self.modules = self.manager.load_modules(self.module_types)
        self.robots = self.manager.load_robots(self.robot_types, self.modules, self.tasks)
        
        # シミュレーション設定
        self.seed = properties.simulation.seed  # シミュレーション内で使う乱数生成器用
        self.max_step = properties.simulation.maxSimulationStep  # シミュレーションの最大ステップ
        self.battery_level_to_recharge = properties.simulation.batteryLevel2Recharge  # バッテリー切れ防止に充電に戻る基準となるバッテリー残量
        self.charge_stations = []  # 充電タスク
        for _, station in properties.simulation.chargeStation.items():
            charge = Charge(name=station.name, coordinate=station.coordinate,
                            total_workload=0, completed_workload=0,
                            task_dependency=[],
                            required_performance={},
                            other_attrs={},
                            charging_speed=station.chargingSpeed)
            self.charge_stations.append(charge)

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



