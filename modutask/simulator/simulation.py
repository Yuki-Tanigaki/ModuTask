import argparse
from collections import defaultdict
from omegaconf import OmegaConf
import numpy as np
import copy
from modutask.robotic_system.core import *
from modutask.robotic_system.manager import *

class Simulator:
    def __init__(self, property_file):
        properties = OmegaConf.load(property_file)

        self.manager = DataManager(properties)
        self.module_types = self.manager.load_module_types()
        self.robot_types = self.manager.load_robot_types(self.module_types)
        self.tasks = self.manager.load_tasks()
        # self.modules = self.manager.load_modules(self.module_types)
        # self.robots = self.manager.load_robots(self.robot_types, self.modules, self.tasks)
        
        
        # シミュレーション設定
        self.seed = properties.simulation.seed  # シミュレーション内で使う乱数生成器用
        self.max_step = properties.simulation.maxSimulationStep # 
        self.battery_limit = properties.simulation.batteryLimit
        self.charge_station = properties.simulation.chargeStation

    # def run_simulation():
    #     # シミュレーションエージェントの生成
    #     agents = [SimulationAgent(robot, battery_limit) for _, robot in robots.items()]

    #     task_priority = []
    #     np.random.seed(1111)
    #     for _ in agents:
    #         keys = tasks.keys()
    #         # 辞書のキーをリストに変換してシャッフルする
    #         task_priority_ = np.array(list(keys))  # keysをリストに変換
    #         np.random.shuffle(task_priority_)  # その場で並び替え
    #         task_priority.append(copy.deepcopy(task_priority_))


def main():
    parser = argparse.ArgumentParser(description="Run the robotic system simulator.")
    parser.add_argument("property_file", type=str, help="Path to the property file")
    args = parser.parse_args()

    simulator = Simulator(args.property_file)
    # simulator.run_simulation()

if __name__ == '__main__':
    main()


