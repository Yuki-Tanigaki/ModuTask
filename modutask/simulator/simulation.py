import argparse
from collections import defaultdict
from omegaconf import OmegaConf
import numpy as np
import copy
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
        self.charge_station = properties.simulation.chargeStation  # 充電ステーションの情報
        
        # シミュレーションの結果保存用
        self.agent_history = []
        self.task_history = []

    def run_simulation(self):
        simulation_rng = np.random.default_rng(self.seed)  # 乱数器にシード値を設定
        
        # シミュレーションエージェントの生成
        agents = [RobotAgent(robot, self.battery_level_to_recharge) for _, robot in self.robots.items()]

        for current_step in range(self.max_step):
            # 各エージェントのループ
            # ready_task = {} # 1ターンの仕事リスト
            for r, agent in enumerate(agents):
                # 稼働不可ならスキップ
                if agent.check_inactive():
                    continue
                # 充電が必要かチェック
                agent.decide_recharge(self.charge_station)
                # タスクの割り当て
                agent.update_task(self.tasks)
                
    #                 if agent.check_travel(simulation_rng):
    #                     agent.travel()
    #                 else:
    #                     agent.charge()
    #                 continue
                
    #             agent.assigned_task
    #             # 既に充電に割り当てられている場合
    #             if agent.to_be_charged is not None:
    #                 if agent.check_travel(simulation_rng):
    #                     agent.travel()
    #                 else:
    #                     agent.charge()
    #                 continue
    #             # 充電が必要かチェック
    #             if not agent.check_battery(charge_station):
    #                 if agent.check_travel(simulation_rng):
    #                     agent.travel()
    #                 else:
    #                     agent.charge()
    #                 continue
    #             # タスクの割り当て
    #             agent.update_task(task_priority[r], filtered_tasks)
    #             if agent.assigned_task is None:
    #                 continue
    #             # タスク地点に到着していないなら移動
    #             if agent.check_travel(simulation_rng):
    #                 agent.travel()
    #                 continue
    #             if agent.assigned_task.name not in ready_task:
    #                 ready_task[agent.assigned_task.name] = []
    #             ready_task[agent.assigned_task.name].append(agent)
    #             agent.set_work()

            
    # def check_task_finish(self, task):
    #     if task.total_workload <= task.completed_workload:
    #         return True
    #     return False

def main():
    parser = argparse.ArgumentParser(description="Run the robotic system simulator.")
    parser.add_argument("property_file", type=str, help="Path to the property file")
    args = parser.parse_args()

    simulator = Simulator(args.property_file)
    # simulator.run_simulation()

if __name__ == '__main__':
    main()


