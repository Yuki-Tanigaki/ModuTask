import os
import time
from typing import Counter
import numpy as np
import pandas as pd
import argparse, yaml, logging
from modutask.io.input import load_module_types, load_modules, load_robot_types
from modutask.io.output import save_robot
from modutask.optimizer.my_moo import *
from modutask.optimizer.my_moo.core.encoding.configuration import ConfigurationVariable
from modutask.io import *
from modutask.core import *
from modutask.simulator.simulation import Simulator
from modutask.utils import raise_with_log
from modutask.visualization.objective import plot_objective_scatter
from simulation_launcher import add_assembly_task, permutation_of_tasks
from optimize_configuration import objective as config_obj
from task_allocation import maximal_operating_time, objective as task_obj, variance_remaining_workload

logger = logging.getLogger(__name__)


def varidate_results(order: list[list[str]], modules: dict[str, Module], robots: dict[str, Robot], tasks: dict[str, BaseTask], combined_tasks: dict[str, BaseTask],
              risk_scenarios: dict[str, BaseRiskScenario], simulation_map: SimulationMap, max_step: int, varidate_scenarios):
    # 残タスク総量　min
    # 残タスク分散　min
    # 最長モジュール使用時間 min
    local_modules = clone_module(modules=modules)
    local_robots = clone_robots(robots=robots, modules=local_modules)
    local_tasks = clone_tasks(tasks=tasks, modules=local_modules, robots=local_robots)
    local_combined_tasks = clone_tasks(tasks=combined_tasks, modules=local_modules, robots=local_robots)
    local_scenarios = clone_risk_scenarios(risk_scenarios=risk_scenarios)
    local_map = clone_simulation_map(simulation_map=simulation_map)
    task_priorities = {}
    for i, robot_name in enumerate(robots):
        task_priorities[robot_name] = order[i]
    permutation_of_tasks(task_priorities=task_priorities, tasks=local_combined_tasks, robots=local_robots)
    simulator = Simulator(
        tasks=local_combined_tasks, 
        robots=local_robots, 
        task_priorities=task_priorities, 
        scenarios=[local_scenarios[scenario_name] for scenario_name in varidate_scenarios],
        simulation_map=local_map,
        )
    for current_step in range(max_step):
        simulator.run_simulation()
    f1 = float(sum(task.total_workload - task.completed_workload for task in tasks.values()))
    f2 = float(variance_remaining_workload(tasks=local_tasks))
    f3 = float(maximal_operating_time(modules=local_modules))
    return f1, f2, f3, local_modules, local_tasks

def main():
    """ロボット構成最適化の実行"""
    parser = argparse.ArgumentParser(description="Run the robotic system simulator.")
    parser.add_argument("--property_file", type=str, help="Path to the property file")
    args = parser.parse_args()

    try:
        with open(args.property_file, 'r') as f:
            prop = yaml.safe_load(f)
    except FileNotFoundError as e:
        raise_with_log(FileNotFoundError, f"File not found: {e}.")

    module_types = load_module_types(file_path=prop['load']['module_type'])
    modules = load_modules(file_path=prop['load']['module'], module_types=module_types)
    robot_types = load_robot_types(file_path=prop['load']['robot_type'], module_types=module_types)

    seed_rng(prop['configuration']['seed'])
    def config_func(order: list[list[int]]) -> list[float]:
        resutls = config_obj(order)
        return resutls

    encoding = ConfigurationVariable(modules=modules, robot_types=robot_types)

    algo = NSGAII(
        func=config_func,
        encoding=encoding,
        population_size=prop['configuration']['population_size'],
        generations=prop['configuration']['generations'],
    )
    start = time.time()
    algo.evolve()
    end = time.time()
    print(end - start)
    nds = get_non_dominated_individuals(algo.get_result())
    kmeans = select_kmeans_representatives(pareto_individuals=nds, k=prop['configuration']['kmeans'])
    for configuration_id, ind in enumerate(kmeans):
        # ロボットの保存
        robots_dict = {}
        for robot_id, robot in enumerate(ind.genome):
            robot.name = f"robot_{robot_id:03}"
            robots_dict[robot.name] = robot
        has_duplicate_module(robots_dict)
        template = prop['results']['robot']
        file_path = template.format(index=configuration_id)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        save_robot(robots=robots_dict, file_path=file_path)

    # データ格納用のリスト
    nd_data = []
    kmeans_data = []
    # Non-Dominatedデータを整形
    for ind in nds:
        types = [robot.type.name for robot in ind.genome]
        states = [robot.state for robot in ind.genome]
        type_counts = dict(Counter(types))
        state_counts = dict(Counter(states))
        nd_data.append({
            "Group": "Non-Dominated",
            "TypeCounts": type_counts,
            "Objectives": ind.objectives,
            "StateCounts": state_counts
        })

    # K-meansデータを整形
    for ind in kmeans:
        types = [robot.type.name for robot in ind.genome]
        states = [robot.state for robot in ind.genome]
        type_counts = dict(Counter(types))
        state_counts = dict(Counter(states))
        kmeans_data.append({
            "Group": "K-means",
            "TypeCounts": type_counts,
            "Objectives": ind.objectives,
            "StateCounts": state_counts
        })

    # データフレームにまとめる
    all_data = nd_data + kmeans_data
    df = pd.DataFrame(all_data)
    file_path = prop['results']['configuration']
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False)

if __name__ == '__main__':
    main()
