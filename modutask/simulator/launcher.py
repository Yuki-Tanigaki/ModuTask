import argparse, yaml, copy, os , logging
from modutask.simulator.simulation import Simulator
from modutask.io import *
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)

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

    manager = DataManager(load_task_priorities=True)
    manager.load(load_path=prop["load"])

    max_step = prop['simulation']['max_step']
    training_scenarios = prop['simulation']['training_scenarios']
    test_scenarios = prop['simulation']['test_scenarios']

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
            max_step=max_step,
            )
        simulator.run_simulation()

if __name__ == '__main__':
    main()
