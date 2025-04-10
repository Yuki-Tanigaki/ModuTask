import os
from typing import Counter
import numpy as np
import argparse, yaml, logging
from modutask.io.input import load_module_types, load_modules, load_robot_types
from modutask.io.output import save_robot
from modutask.optimizer.my_moo import *
from modutask.optimizer.my_moo.core.encoding.configuration import ConfigurationVariable
from modutask.io import *
from modutask.core import *
from modutask.utils import raise_with_log
from modutask.visualization.objective import plot_objective_scatter

logger = logging.getLogger(__name__)


def objective(order: list[Robot], modules: dict[str, Module], robot_types: dict[str, RobotType]) -> list[float]:
    """目的関数の計算"""
    # Transportの総量 max
    # Manufactureの総量 max
    # Mobirityの総量 max
    # 使用モジュールの合計使用時間 min
    # モジュール運搬距離 min

    sum_transport = 0.0
    sum_manufacture = 0.0
    sum_mobility = 0.0
    sum_operating_time = 0.0
    sum_module_distance = 0.0
    for robot in order:
        robot_type = robot.type
        sum_transport += robot_type.performance[PerformanceAttributes.TRANSPORT]
        sum_manufacture += robot_type.performance[PerformanceAttributes.MANUFACTURE]
        sum_mobility += robot_type.performance[PerformanceAttributes.MOBILITY]

        for module in robot.component_required:
            sum_operating_time += module.operating_time
            sum_module_distance += float(np.linalg.norm(np.array(module.coordinate) - np.array(robot.coordinate)))
    return [-1 * sum_transport, 
            -1 * sum_manufacture, 
            -1 * sum_mobility, 
            sum_operating_time, 
            sum_module_distance
            ]

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

    seed_rng(prop['robot_configuration']['seed'])
    def sim_func(order: list[list[int]]) -> list[float]:
        resutls = objective(order, modules=modules, robot_types=robot_types)
        return resutls

    encoding = ConfigurationVariable(modules=modules, robot_types=robot_types)

    algo = NSGAII(
        simulation_func=sim_func,
        encoding=encoding,
        population_size=prop['robot_configuration']['population_size'],
        generations=prop['robot_configuration']['generations'],
    )
    algo.evolve()

    nds = get_non_dominated_individuals(algo.get_result())
    for configuration_id, ind in enumerate(nds):
        # ロボットの保存
        robots_dict = {}
        for robot_id, robot in enumerate(ind.genome):
            robot.name = f"robot_{robot_id:03}"
            robots_dict[robot.name] = robot
        task_template = prop['results']['robot']
        file_path = task_template.format(index=configuration_id)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        save_robot(robots=robots_dict, file_path=file_path)

    print("NonD solutions:")
    for ind in nds:
        types = [robot.type.name for robot in ind.genome]
        # カウント
        type_counts = Counter(types)
        print(f"Robots: {type_counts}")
        print(f"Objectives: {ind.objectives}")
    objectives = [ind.objectives for ind in nds]
    plot_objective_scatter(objectives=objectives, 
                           file_path=prop['figures']['pareto_front'],
                           labels=['Transport', 'Manufacture', 'Mobility', 'Operating Time', 'Module Distance']
                           )


if __name__ == '__main__':
    main()
