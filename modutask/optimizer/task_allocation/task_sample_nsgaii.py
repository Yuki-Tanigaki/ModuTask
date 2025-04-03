import argparse, yaml, copy, pickle, os, logging
from modutask.optimizer.my_moo import *
from modutask.simulator.simulation import Simulator
from modutask.io import *
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)


def objective(order: list[int], manager: DataManager, max_step: int, training_scenarios) -> list[float]:
    for scenario_names in training_scenarios:
        tasks = copy.deepcopy(manager.combined_tasks)
        robots = copy.deepcopy(manager.robots)
        task_priorities=manager.task_priorities
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
    return [dist1, dist2]

def main():
    """
    property_fileの設定でシミュレーションを実行
    training_scenarioの平均評価とtest_scenarioの評価を出力
    test_scenarioの履歴を可視化
    """
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
    def sim_func(order: list[int]) -> list[float]:
        return objective(order, manager=manager, max_step=max_step, training_scenarios=training_scenarios)

    encoding = PermutationVariable(items=list(range(30)))

    algo = NSGAII(
        simulation_func=sim_func,
        encoding=encoding,
        population_size=100,
        generations=200,
    )
    algo.evolve()

    nds = get_non_dominated_individuals(algo.get_result())
    print("\n非支配解:")
    for ind in nds:
        print(ind.objectives)
    
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

if __name__ == '__main__':
    main()
