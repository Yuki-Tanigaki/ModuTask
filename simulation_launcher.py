import random
import numpy as np
import argparse, yaml, pickle, os, logging
from modutask.simulator.simulation import Simulator
from modutask.core import *
from modutask.io import *
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)

def add_assembly_task(tasks: dict[str, BaseTask], robots: dict[str, Robot]) -> dict[str, BaseTask]:
    """ モジュール不足のロボット用の組み立てタスクの追加 """
    combined_tasks = dict(tasks)
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
            combined_tasks[f'transport_{robot_name}_{module.name}'] = transport
            task_dependency.append(transport)
        if len(robot.missing_components()) != 0:
            assembly = Assembly(name=f'assembly_{robot_name}', robot=robot)
            assembly.initialize_task_dependency(task_dependency=task_dependency)
            combined_tasks[f'assembly_{robot_name}'] = assembly
    return combined_tasks

def permutation_of_tasks(task_priorities: dict[str, list[str]], tasks: dict[str, BaseTask], robots: dict[str, Robot]) -> None:
    """
    task_prioritiesが(全ロボット)と(全タスクの順列)で構成されているかチェックする関数
    """
    missing_robots = [robot_name for robot_name in robots if robot_name not in task_priorities]
    if missing_robots:
        raise_with_log(RuntimeError, f"Some robots are missing in task_priorities: {missing_robots}.")

    def is_permutation_of_tasks(task_list: list[str], all_tasks: dict[str, BaseTask]) -> bool:
        return set(task_list) == set(all_tasks.keys()) and len(task_list) == len(all_tasks)
    for robot, task_list in task_priorities.items():
        if not is_permutation_of_tasks(task_list, tasks):
            raise_with_log(RuntimeError, f"The task list is not a permutation of the tasks. ")

def main():
    """シミュレータの実行"""
    parser = argparse.ArgumentParser(description="Run the robotic system simulator.")
    parser.add_argument("--property_file", type=str, help="Path to the property file")
    args = parser.parse_args()

    try:
        with open(args.property_file, 'r') as f:
            prop = yaml.safe_load(f)
    except FileNotFoundError as e:
        raise_with_log(FileNotFoundError, f"File not found: {e}.")

    random.seed(prop['simulation']['seed'])

    tasks = load_tasks(file_path=prop["load"]["task"])
    tasks = load_task_dependency(file_path=prop["load"]['task_dependency'], tasks=tasks)
    module_types = load_module_types(file_path=prop["load"]['module_type'])
    modules = load_modules(file_path=prop["load"]['module'], module_types=module_types)
    robot_types = load_robot_types(file_path=prop["load"]['robot_type'], module_types=module_types)
    robots = load_robots(file_path=prop["load"]['robot'], robot_types=robot_types, modules=modules)
    has_duplicate_module(robots=robots)
    combined_tasks = add_assembly_task(tasks=tasks, robots=robots)
    simulation_map = load_simulation_map(file_path=prop["load"]['map'])
    risk_scenarios = load_risk_scenarios(file_path=prop["load"]['risk_scenario'])
    task_priorities = {}
    for r_name in robots.keys():
        shuffled_array = list(combined_tasks.keys())
        random.shuffle(shuffled_array)
        task_priorities[r_name] = shuffled_array
    # task_priorities = load_task_priorities(file_path=prop["load"]['task_priority'], robots=robots, tasks=combined_tasks)
    permutation_of_tasks(task_priorities=task_priorities, tasks=combined_tasks, robots=robots)

    max_step = prop['simulation']['max_step']
    training_scenarios = prop['simulation']['training_scenarios']
    varidate_scenarios = prop['simulation']['varidate_scenarios']

    total_remaining_workload = []
    variance_remaining_workload = []
    variance_operating_time = []

    for scenario_names in training_scenarios:
        local_modules = clone_module(modules=modules)
        local_robots = clone_robots(robots=robots, modules=local_modules)
        local_tasks = clone_tasks(tasks=combined_tasks, modules=local_modules, robots=local_robots)
        local_scenarios = clone_risk_scenarios(risk_scenarios=risk_scenarios)
        local_map = clone_simulation_map(simulation_map=simulation_map)
        simulator = Simulator(
            tasks=local_tasks, 
            robots=local_robots, 
            task_priorities=task_priorities, 
            scenarios=[local_scenarios[scenario_name] for scenario_name in scenario_names],
            simulation_map=local_map,
            )
        for current_step in range(max_step):
            simulator.run_simulation()
        total_remaining_workload.append(simulator.total_remaining_workload())
        variance_remaining_workload.append(simulator.variance_remaining_workload())
        variance_operating_time.append(simulator.variance_operating_time())
    print(
        float(sum(total_remaining_workload) / len(total_remaining_workload)), 
        float(sum(variance_remaining_workload) / len(variance_remaining_workload)),
        float(sum(variance_operating_time) / len(variance_operating_time))
        )

    # tasks = manager.combined_tasks
    # robots = manager.robots
    # task_priorities=manager.task_priorities
    # scenarios = [manager.risk_scenarios[scenario_name] for scenario_name in varidate_scenarios]
    # simulator = Simulator(
    #     tasks=tasks, 
    #     robots=robots, 
    #     task_priorities=task_priorities, 
    #     scenarios=scenarios,
    #     simulation_map=manager.simulation_map,
    #     )
    
    # for current_step in range(max_step):
    #     simulator.run_simulation()
    #     task_template = prop['results']['task']
    #     task_path = task_template.format(index=current_step)
    #     os.makedirs(os.path.dirname(task_path), exist_ok=True)
    #     with open(task_path, "wb") as f:
    #         pickle.dump(manager.tasks, f)
    # print("Varidate scenario evaluation:")
    # print([simulator.total_remaining_workload(), 
    #         simulator.variance_remaining_workload(),
    #         simulator.variance_operating_time()])


if __name__ == '__main__':
    main()
