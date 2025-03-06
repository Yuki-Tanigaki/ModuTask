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

        self.manager = Manager(properties)
        self.module_types = self.manager.read_module_type()
        self.robot_types = self.manager.read_robot_type(self.module_types)
        self.modules = self.manager.read_module(self.module_types)
        self.robots = self.manager.read_robot(self.robot_types, self.modules)
        self.tasks = self.manager.read_task(self.robots)
        
        # シミュレーション設定
        self.seed = properties.simulation.seed # シミュレーション内で使う乱数生成器用
        self.max_step = properties.simulation.maxSimulationStep # 
        self.battery_limit = properties.simulation.batteryLimit
        self.charge_station = properties.simulation.chargeStation

    def run_simulation():
        # シミュレーションエージェントの生成
        agents = [SimulationAgent(robot, battery_limit) for _, robot in robots.items()]

        task_priority = []
        np.random.seed(1111)
        for _ in agents:
            keys = tasks.keys()
            # 辞書のキーをリストに変換してシャッフルする
            task_priority_ = np.array(list(keys))  # keysをリストに変換
            np.random.shuffle(task_priority_)  # その場で並び替え
            task_priority.append(copy.deepcopy(task_priority_))


def main():
    parser = argparse.ArgumentParser(description="Run the robotic system simulator.")
    parser.add_argument("property_file", type=str, help="Path to the property file")
    args = parser.parse_args()

    simulator = Simulator(args.property_file)
    simulator.run_simulation()

if __name__ == '__main__':
    main()


# def run_simulation(task_priority, agents, tasks, seed, max_step, charge_station, break_prob):
#     # シミュレーション内で使う乱数生成器
#     simulation_rng = np.random.default_rng(seed)  # シード値を設定

#     # シミュレーションを実行
#     finished_tasks = []
#     agent_history_ = []
#     task_history_ = []

#     break_limbs = []
#     for t in range(max_step):
#         break_limbs_ = []
#         for r, agent in enumerate(agents):
#             if simulation_rng.random() < break_prob:
#                 break_limbs_.append(True)
#             else:
#                 break_limbs_.append(False)
#         break_limbs.append(break_limbs_)

#     agent_history_.append([copy.deepcopy(agent) for agent in agents])
#     task_history_.append(copy.deepcopy(tasks))
#     for t in range(max_step):
#         # タスクの完了をチェック
#         for task_name, task in tasks.items():
#             if task_name in finished_tasks:
#                 continue
#             # タスクがすでに完了しているかチェック
#             workload = task.workload # 仕事量[全体, 完了済み]
#             if workload[0] <= workload[1]:
#                 finished_tasks.append(task_name)

#         # finished_tasksに含まれないtasks
#         filtered_tasks = {k: v for k, v in tasks.items() if k not in finished_tasks}
#         # 前提タスクの終了を確認
#         tasks_to_remove = []
#         for task_name, task in filtered_tasks.items():
#             for dependency_task in task.task_dependency:
#                 if dependency_task.name not in finished_tasks:
#                     tasks_to_remove.append(task_name)
#                     break
#         for task_name in tasks_to_remove:
#             filtered_tasks.pop(task_name)

#         # 各エージェントのループ
#         ready_task = {} # 1ターンの仕事リスト
#         for r, agent in enumerate(agents):
#             if break_limbs[t][r]:
#                 agent.break_limb()

#             # 働けるかチェック
#             # 各モジュールの位置をチェック
#             agent.update_active()
#             if agent.robot.state == RobotState.INACTIVE: # 稼働不可ならスキップ
#                 continue
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

#         # 仕事を実行
#         for task_name, agent_list in ready_task.items():
#             required_abilities = tasks[task_name].required_abilities
#             if check_abilities(agent_list, required_abilities):
#                 # 仕事を実行
#                 if isinstance(tasks[task_name], Transport):
#                     tasks[task_name].update()
#                     # タスクに合わせて移動
#                     for agent in agent_list:
#                         agent.work(simulation_rng)
#                         agent.travel()
#                 elif isinstance(tasks[task_name], Manufacture):
#                     tasks[task_name].update()
#                     for agent in agent_list:
#                         agent.work(simulation_rng)
#         agent_history = []
#         for r, agent in enumerate(agents):
#             agent_history.append(copy.deepcopy(agent))
#         agent_history_.append(agent_history)
#         task_history_.append(copy.deepcopy(tasks))

#     return agent_history_, task_history_