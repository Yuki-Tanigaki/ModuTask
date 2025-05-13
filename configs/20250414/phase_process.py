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

from optimize_configuration import objective as config_obj
from task_allocation import maximal_operating_time, objective as task_obj, variance_remaining_workload


class Phase_process:
    def __init__(self, phase_index):
        """phaseインデックス"""
        self.phase_index = phase_index

        """propertyデータ展開"""
        self.module_types = None
        self.modules = None
        self.robot_types = None
        self.tasks = None

    def variance_remaining_workload(self, tasks: dict[str, BaseTask]) -> float:
        # 各タスクの座標と未完了仕事量を抽出
        coordinates = []
        weights = []
        remainings = []

        for task in tasks.values():
            remaining = task.total_workload - task.completed_workload
            coordinates.append(np.array(task.coordinate))
            weights.append(remaining)
            remainings.append((task.total_workload, task.completed_workload))   #デバッグ用

        coordinates = np.array(coordinates)
        weights = np.array(weights)

        # 重心（重み付き平均座標）を計算
        try:
            if np.sum(weights) == 0:
                # タイプ1:重心を原点にする。「何もタスクがないなら（＝全部完了しているなら）中心は原点でよい」という考え。
                # weighted_center = np.zeros(coordinates.shape[1])
                # タイプ2:単純平均にフォールバックする（重みなし平均）。「全タスクの中心をとる」という選択。重みが使えないなら、等価な重要度で平均。
                weighted_center = np.mean(coordinates, axis=0)
            else:
                weighted_center = np.average(coordinates, axis=0, weights=weights)
        except:
            print("tasks:", tasks)
            print("weights:", weights)
            print("coordinates:", coordinates)
            print("remainings:", remainings)
            exit(5)
        # 各点の重心からの距離の二乗 × 重み の合計を求める
        distances_squared = np.sum(weights * np.sum((coordinates - weighted_center) ** 2, axis=1))
        # 重み付き分散（距離に基づく残タスク分散）
        if np.sum(weights) == 0:
            # タイプ1:0にする。
            # distance_mean = 0
            # タイプ2:無限大にする。
            distance_mean = float('inf')
        else:
            distance_mean = float(distances_squared / np.sum(weights))
        return distance_mean

    def maximal_operating_time(self, modules: dict[str, Module]) -> float:
        operating_times = np.array([module.operating_time for module in modules.values()])
        return float(max(operating_times))

    def generate_assembly_task(self, robots: dict[str, Robot]) -> dict[str, BaseTask]:
        """ モジュール不足のロボット用の組み立てタスクの追加 """
        additional_tasks = {}
        for robot_name, robot in robots.items():
            task_dependency = []
            for module in robot.missing_components():
                required_performance = {}
                required_performance[PerformanceAttributes.TRANSPORT] = 1.0
                origin_coordinate = module.coordinate
                destination_coordinate = robot.coordinate
                transport_resistance = 1.0
                v = np.array(destination_coordinate) - np.array(origin_coordinate)
                total = transport_resistance * np.linalg.norm(v)
                transport = TransportModule(
                    name=f'transport_{robot_name}_{module.name}', 
                    coordinate=module.coordinate, 
                    required_performance=required_performance,
                    origin_coordinate=origin_coordinate,
                    destination_coordinate=destination_coordinate,
                    transport_resistance=transport_resistance,
                    total_workload=total,
                    completed_workload=0,
                    target_module=module,
                    )
                additional_tasks[f'transport_{robot_name}_{module.name}'] = transport
                task_dependency.append(transport)
            if len(robot.missing_components()) != 0:
                assembly = Assembly(name=f'assembly_{robot_name}', robot=robot)
                assembly.initialize_task_dependency(task_dependency=task_dependency)
                additional_tasks[f'assembly_{robot_name}'] = assembly
        return additional_tasks

    def objective(self, order: list[list[str]], modules: dict[str, Module], robots: dict[str, Robot], tasks: dict[str, BaseTask], additional_tasks: dict[str, BaseTask],
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
            local_additional_tasks = clone_tasks(tasks=additional_tasks, modules=local_modules, robots=local_robots)
            local_scenarios = clone_risk_scenarios(risk_scenarios=risk_scenarios)
            local_map = clone_simulation_map(simulation_map=simulation_map)
            task_priorities = {}
            for i, robot_name in enumerate(robots):
                task_priorities[robot_name] = order[i]
            # permutation_of_tasks(task_priorities=task_priorities, tasks=local_combined_tasks, robots=local_robots)
            local_merged_task = local_tasks | local_additional_tasks
            simulator = Simulator(
                tasks=local_merged_task, 
                robots=local_robots, 
                task_priorities=task_priorities, 
                scenarios=[local_scenarios[scenario_name] for scenario_name in scenario_names],
                simulation_map=local_map,
                )
            count = max_step * (max_step + 1) // 2 * len(local_robots)
            for current_step in range(max_step):
                simulator.run_simulation()
                for agent in simulator.agents.values():
                    if agent.robot.state == RobotState.ACTIVE:
                        count += -1 * (max_step - current_step)
                # print(current_step)
                # states = [robot.state for robot in local_robots.values()]
                # print(dict(Counter(states)))
                # print(local_combined_tasks)
                # print(current_step)
                # states = [(task.__class__, task.is_completed()) for task in local_combined_tasks.values()]
                # print(dict(Counter(states)))

            # f1.append(float(sum(task.total_workload - task.completed_workload for task in local_tasks.values())) * 1000 + 
            #           float(sum(task.total_workload - task.completed_workload for task in local_combined_tasks.values())) )
            active_ratio = float(count/(max_step * (max_step + 1) // 2 * len(local_robots)))
            # states = [(task.__class__, task.is_completed()) for task in local_tasks.values()]
            # print(dict(Counter(states)))
            f1.append(float(sum(task.total_workload - task.completed_workload for task in local_tasks.values())) + active_ratio)
            f2.append(float(self.variance_remaining_workload(tasks=local_tasks)))
            f3.append(float(self.maximal_operating_time(modules=local_modules)))
        del local_modules, local_robots, local_tasks, local_additional_tasks, local_scenarios, local_map, simulator
        gc.collect()
        # print(sum(f1) / len(f1))
        return [sum(f1) / len(f1), 
                sum(f2) / len(f2),
                sum(f3) / len(f3)]

    def varidate_results(self, order: list[list[str]], modules: dict[str, Module], robots: dict[str, Robot], tasks: dict[str, BaseTask], additional_tasks: dict[str, BaseTask],
                risk_scenarios: dict[str, BaseRiskScenario], simulation_map: SimulationMap, max_step: int, varidate_scenarios):
        # 残タスク総量　min
        # 残タスク分散　min
        # 最長モジュール使用時間 min
        local_modules = clone_module(modules=modules)
        local_robots = clone_robots(robots=robots, modules=local_modules)
        local_tasks = clone_tasks(tasks=tasks, modules=local_modules, robots=local_robots)
        local_additional_tasks = clone_tasks(tasks=additional_tasks, modules=local_modules, robots=local_robots)
        local_scenarios = clone_risk_scenarios(risk_scenarios=risk_scenarios)
        local_map = clone_simulation_map(simulation_map=simulation_map)
        task_priorities = {}
        for i, robot_name in enumerate(robots):
            task_priorities[robot_name] = order[i]
        local_merged_task = local_tasks | local_additional_tasks
        simulator = Simulator(
            tasks=local_merged_task, 
            robots=local_robots, 
            task_priorities=task_priorities, 
            scenarios=[local_scenarios[scenario_name] for scenario_name in varidate_scenarios],
            simulation_map=local_map,
            )
        count = max_step * (max_step + 1) // 2 * len(local_robots)
        for current_step in range(max_step):
            simulator.run_simulation()
            for agent in simulator.agents.values():
                if agent.robot.state == RobotState.ACTIVE:
                    count += -1 * (max_step - current_step)
        active_ratio = float(count/(max_step * (max_step + 1) // 2 * len(local_robots)))
        f1 = float(sum(task.total_workload - task.completed_workload for task in local_tasks.values())) + active_ratio
        f2 = float(self.variance_remaining_workload(tasks=local_tasks))
        f3 = float(self.maximal_operating_time(modules=local_modules))
        return f1, f2, f3, local_modules, local_tasks

    """ロボット構成最適化の実行"""
    def proc_robot_configuration(self, prop, module_types, modules, robot_types):

        """propertyデータ展開"""
        self.module_types = module_types
        self.modules = modules
        self.robot_types = robot_types
        seed_rng(prop['configuration']['seed'])     #先生に確認

        def config_func(order: list[list[int]]) -> list[float]:
            resutls = config_obj(order)
            return resutls

        encoding = ConfigurationVariable(modules=self.modules, robot_types=self.robot_types)

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
            robot_path = template.format(phase_index=self.phase_index, index=configuration_id)
            os.makedirs(os.path.dirname(robot_path), exist_ok=True)
            save_robot(robots=robots_dict, file_path=robot_path)

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

        return all_data

    """タスクアロケーションの実行"""
    def proc_task_allocation(self, prop, module_types, modules, robot_types, tasks):

        """propertyデータ展開"""
        self.module_types = module_types
        self.modules = modules
        self.robot_types = robot_types
        self.tasks = tasks

        # データ格納用のリスト
        task_data = []
        next_modules = None
        next_tasks = None
        best_fitness = float("inf")
        for configuration_id in range(prop['configuration']['kmeans']):
            if configuration_id > 0:
                continue
            template = prop['results']['robot']
            robot_path = template.format(phase_index=self.phase_index, index=configuration_id)
            robots = load_robots(file_path=robot_path, robot_types=self.robot_types, modules=self.modules)
            # tasks = load_tasks(file_path=prop["load"]["task"])        #先生に確認
            tasks = load_task_dependency(file_path=prop["load"]['task_dependency'], tasks=tasks)
            has_duplicate_module(robots=robots)
            additional_tasks = self.generate_assembly_task(robots=robots)
            simulation_map = load_simulation_map(file_path=prop["load"]['map'])
            risk_scenarios = load_risk_scenarios(file_path=prop["load"]['risk_scenario'])

            max_step = prop['simulation']['max_step']
            training_scenarios = prop['simulation']['training_scenarios']
            varidate_scenarios = prop['simulation']['varidate_scenarios']

            seed_rng(prop['task_allocation']['seed'])
            def task_func(order: list[list[int]]) -> list[float]:
                resutls = self.objective(
                    order, 
                    modules=self.modules, 
                    robots=robots,
                    additional_tasks=additional_tasks,
                    tasks=tasks,
                    risk_scenarios=risk_scenarios, 
                    simulation_map=simulation_map,
                    max_step=max_step, 
                    training_scenarios=training_scenarios
                    )
                return resutls
            
            merged_task = tasks | additional_tasks
            items = sorted([item for item in merged_task.keys() if not str(item).startswith('assembly_')])
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
                f1, f2, f3, local_modules, local_tasks = self.varidate_results(
                    ind.genome, 
                    modules=self.modules,
                    robots=robots,
                    additional_tasks=additional_tasks,
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

            return task_data, next_modules, next_tasks

