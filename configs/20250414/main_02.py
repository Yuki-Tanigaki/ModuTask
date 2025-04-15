import gc
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

logger = logging.getLogger(__name__)


def variance_remaining_workload(tasks: dict[str, BaseTask]) -> float:
    # 各タスクの座標と未完了仕事量を抽出
    coordinates = []
    weights = []

    for task in tasks.values():
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

def maximal_operating_time(modules: dict[str, Module]) -> float:
    operating_times = np.array([module.operating_time for module in modules.values()])
    return float(max(operating_times))

def objective(order: list[list[str]], modules: dict[str, Module], robots: dict[str, Robot], tasks: dict[str, BaseTask], combined_tasks: dict[str, BaseTask],
              risk_scenarios: dict[str, BaseRiskScenario], simulation_map: SimulationMap, max_step: int, training_scenarios) -> list[float]:
    # 残タスク総量　min
    # 残タスク分散　min
    # 最長モジュール使用時間 min
    f1 = []
    f2 = []
    f3 = []

    for scenario_names in training_scenarios:
        local_modules = clone_module(modules=modules)
        local_robots = clone_robots(robots=robots, modules=local_modules)
        local_tasks = clone_tasks(tasks=tasks, modules=local_modules, robots=local_robots)
        local_combined_tasks = clone_tasks(tasks=combined_tasks, modules=local_modules, robots=local_robots)
        local_scenarios = clone_risk_scenarios(risk_scenarios=risk_scenarios)
        local_map = clone_simulation_map(simulation_map=simulation_map)
        task_priorities = {}
        for i, robot_name in enumerate(robots):
            task_priorities[robot_name] = order[i]
        # permutation_of_tasks(task_priorities=task_priorities, tasks=local_combined_tasks, robots=local_robots)
        simulator = Simulator(
            tasks=local_combined_tasks, 
            robots=local_robots, 
            task_priorities=task_priorities, 
            scenarios=[local_scenarios[scenario_name] for scenario_name in scenario_names],
            simulation_map=local_map,
            )
        for current_step in range(max_step):
            simulator.run_simulation()
            # print()
            # states = [robot.state for robot in local_robots.values()]
            # print(dict(Counter(states)))
            # print(local_combined_tasks)
        f1.append(float(sum(task.total_workload - task.completed_workload for task in tasks.values())))
        f2.append(float(variance_remaining_workload(tasks=local_tasks)))
        f3.append(float(maximal_operating_time(modules=local_modules)))
    del local_modules, local_robots, local_tasks, local_combined_tasks, local_scenarios, local_map, simulator
    gc.collect()
    return [sum(f1) / len(f1), 
            sum(f2) / len(f2),
            sum(f3) / len(f3)]

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

    """タスクアロケーションの実行"""
    # データ格納用のリスト
    task_data = []
    next_modules = None
    next_tasks = None
    best_fitness = float("inf")
    for configuration_id in range(prop['configuration']['kmeans']):
        template = prop['results']['robot']
        robot_path = template.format(index=configuration_id)
        robots = load_robots(file_path=robot_path, robot_types=robot_types, modules=modules)
        tasks = load_tasks(file_path=prop["load"]["task"])
        tasks = load_task_dependency(file_path=prop["load"]['task_dependency'], tasks=tasks)
        has_duplicate_module(robots=robots)
        combined_tasks = add_assembly_task(tasks=tasks, robots=robots)
        simulation_map = load_simulation_map(file_path=prop["load"]['map'])
        risk_scenarios = load_risk_scenarios(file_path=prop["load"]['risk_scenario'])

        max_step = prop['simulation']['max_step']
        training_scenarios = prop['simulation']['training_scenarios']
        varidate_scenarios = prop['simulation']['varidate_scenarios']

        seed_rng(prop['task_allocation']['seed'])
        def task_func(order: list[list[int]]) -> list[float]:
            resutls = objective(
                order, 
                modules=modules, 
                robots=robots,
                combined_tasks=combined_tasks,
                tasks=tasks,
                risk_scenarios=risk_scenarios, 
                simulation_map=simulation_map,
                max_step=max_step, 
                training_scenarios=training_scenarios
                )
            return resutls

        items = sorted([item for item in combined_tasks.keys() if not str(item).startswith('assembly_')])
        # items = sorted(combined_tasks.keys())
        encoding = MultiPermutationVariable(items=items, n_multi=len(robots))

        algo = NSGAII(
            func=task_func,
            encoding=encoding,
            population_size=prop['task_allocation']['population_size'],
            generations=prop['task_allocation']['generations'],
        )
        start = time.time()
        algo.evolve()
        end = time.time()
        print(end - start)

        nds = get_non_dominated_individuals(algo.get_result())
        for ind in nds:
            f1, f2, f3, local_modules, local_tasks = varidate_results(
                ind.genome, 
                modules=modules, 
                robots=robots,
                combined_tasks=combined_tasks,
                tasks=tasks,
                risk_scenarios=risk_scenarios, 
                simulation_map=simulation_map,
                max_step=max_step, 
                varidate_scenarios=varidate_scenarios
                )
            results = [f1, f2, f3]
            if sum(results) < best_fitness:
                # 最良の適応度を持つ個体の情報を保存
                next_modules = local_modules
                next_tasks = local_tasks
                best_fitness = sum(results)
            task_data.append({
                "ConfigurationID": configuration_id,
                "Priority": ind.genome,
                "Objectives": results,
            })
        task_df = pd.DataFrame(task_data)
        file_path = prop['results']['scheduling']
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        task_df.to_csv(file_path, index=False)
        
        # taskとモジュールの状態を保存
        file_path = prop['results']['module']
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        save_module(modules=next_modules, file_path=file_path)
        file_path = prop['results']['task']
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        save_tasks(tasks=next_tasks, file_path=file_path)


if __name__ == '__main__':
    main()
