import argparse, yaml, copy, pickle, os, logging
from modutask.optimizer.my_moo import *
from modutask.simulator.simulation import Simulator
from modutask.io import *
from modutask.core import *
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)


def objective(order: list[list[str]], manager: DataManager, max_step: int, training_scenarios) -> list[float]:
    # 残タスク総量　min
    # 残タスク分散　min
    # モジュール使用時間分散 min
    total_remaining_workload = []
    variance_remaining_workload = []
    variance_operating_time = []

    for scenario_names in training_scenarios:
        local_manager = manager.clone_for_simulation()
        tasks = local_manager.combined_tasks
        robots = local_manager.robots
        scenarios = local_manager.risk_scenarios
        task_priorities = {}
        for i, robot_name in enumerate(robots):
            task_priorities[robot_name] = order[i]
        simulator = Simulator(
            tasks=tasks, 
            robots=robots, 
            task_priorities=task_priorities, 
            scenarios=[scenarios[scenario_name] for scenario_name in scenario_names],
            simulation_map=manager.simulation_map,
            )
        for current_step in range(max_step):
            simulator.run_simulation()
        total_remaining_workload.append(simulator.total_remaining_workload())
        variance_remaining_workload.append(simulator.variance_remaining_workload())
        variance_operating_time.append(simulator.variance_operating_time())
    return [sum(total_remaining_workload) / len(total_remaining_workload), 
            sum(variance_remaining_workload) / len(variance_remaining_workload),
            sum(variance_operating_time) / len(variance_operating_time)]

def main():
    """タスクアロケーションの実行"""
    parser = argparse.ArgumentParser(description="Run the robotic system simulator.")
    parser.add_argument("--property_file", type=str, help="Path to the property file")
    args = parser.parse_args()

    try:
        with open(args.property_file, 'r') as f:
            prop = yaml.safe_load(f)
    except FileNotFoundError as e:
        raise_with_log(FileNotFoundError, f"File not found: {e}.")

    manager = DataManager(load_task_priorities=False)
    manager.load(load_path=prop["load"])

    max_step = prop['simulation']['max_step']
    training_scenarios = prop['simulation']['training_scenarios']
    varidate_scenarios = prop['simulation']['varidate_scenarios']

    seed_rng(prop['task_allocation']['seed'])
    def sim_func(order: list[list[int]]) -> list[float]:
        resutls = objective(order, manager=manager, max_step=max_step, training_scenarios=training_scenarios)
        return resutls

    items = list(manager.combined_tasks.keys())
    encoding = MultiPermutationVariable(items=items, n_multi=len(manager.robots))

    algo = NSGAII(
        simulation_func=sim_func,
        encoding=encoding,
        population_size=prop['task_allocation']['population_size'],
        generations=prop['task_allocation']['generations'],
    )
    algo.evolve()

    nds = get_non_dominated_individuals(algo.get_result())
    print("NonD solutions:")
    for ind in nds:
        local_manager = manager.clone_for_simulation()
        tasks = local_manager.combined_tasks
        robots = local_manager.robots
        scenarios = local_manager.risk_scenarios
        task_priorities = {}
        for i, robot_name in enumerate(robots):
            task_priorities[robot_name] = ind.genome[i]
        simulator = Simulator(
            tasks=tasks, 
            robots=robots, 
            task_priorities=task_priorities, 
            scenarios=[scenarios[scenario_name] for scenario_name in varidate_scenarios],
            simulation_map=manager.simulation_map,
            )
        for current_step in range(max_step):
            simulator.run_simulation()
        varidate_objectives = [simulator.total_remaining_workload(),
                               simulator.variance_remaining_workload(),
                               simulator.variance_operating_time()]

        # print(f"Priority: {ind.genome}")
        print(f"Training: {ind.objectives}")
        print(f"Varidation: {varidate_objectives}")
if __name__ == '__main__':
    main()
