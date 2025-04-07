import argparse, yaml, pickle, os, logging
from modutask.simulator.simulation import Simulator
from modutask.io import *
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)

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

    manager = DataManager(load_task_priorities=True)
    manager.load(load_path=prop["load"])

    max_step = prop['simulation']['max_step']
    training_scenarios = prop['simulation']['training_scenarios']
    varidate_scenarios = prop['simulation']['varidate_scenarios']

    total_remaining_workload = []
    variance_remaining_workload = []
    variance_operating_time = []

    for scenario_names in training_scenarios:
        local_manager = manager.clone_for_simulation()
        tasks = local_manager.combined_tasks
        robots = local_manager.robots
        task_priorities = local_manager.task_priorities
        scenarios = local_manager.risk_scenarios
        scenarios = [manager.risk_scenarios[scenario_name] for scenario_name in scenario_names]
        simulator = Simulator(
            tasks=tasks, 
            robots=robots, 
            task_priorities=task_priorities, 
            scenarios=scenarios,
            simulation_map=manager.simulation_map,
            )
        for current_step in range(max_step):
            simulator.run_simulation()
        total_remaining_workload.append(simulator.total_remaining_workload())
        variance_remaining_workload.append(simulator.variance_remaining_workload())
        variance_operating_time.append(simulator.variance_operating_time())
    
    print("Training scenarios average:")
    print([sum(total_remaining_workload) / len(total_remaining_workload), 
            sum(variance_remaining_workload) / len(variance_remaining_workload),
            sum(variance_operating_time) / len(variance_operating_time)])

    tasks = manager.combined_tasks
    robots = manager.robots
    task_priorities=manager.task_priorities
    scenarios = [manager.risk_scenarios[scenario_name] for scenario_name in varidate_scenarios]
    simulator = Simulator(
        tasks=tasks, 
        robots=robots, 
        task_priorities=task_priorities, 
        scenarios=scenarios,
        simulation_map=manager.simulation_map,
        )
    
    for current_step in range(max_step):
        simulator.run_simulation()
        task_template = prop['results']['task']
        task_path = task_template.format(index=current_step)
        os.makedirs(os.path.dirname(task_path), exist_ok=True)
        with open(task_path, "wb") as f:
            pickle.dump(manager.tasks, f)
    print("Varidate scenario evaluation:")
    print([simulator.total_remaining_workload(), 
            simulator.variance_remaining_workload(),
            simulator.variance_operating_time()])


if __name__ == '__main__':
    main()
