import argparse, yaml
from modutask.simulator.simulation import Simulator
from modutask.io import *

def main():
    parser = argparse.ArgumentParser(description="Run the robotic system simulator.")
    parser.add_argument("--property_file", type=str, help="Path to the property file")
    parser.add_argument("--scenario", type=str, help="Scenarios used in simulations")
    parser.add_argument("--max_step", type=int, help="Maximum number of steps to run the simulation")
    args = parser.parse_args()

    manager = DataManager(args.property_file)
    tasks = manager.load_tasks()
    module_types = manager.load_module_types()
    modules = manager.load_modules(module_types=module_types)
    scenarios = manager.load_scenarios()
    robot_types = manager.load_robot_types(module_types=module_types)
    robots = manager.load_robots(robot_types=robot_types, modules=modules)
    task_priority = manager.load_task_priority(robots=robots, tasks=tasks)

    # charge_stations = []  # 充電タスク
    # for _, station in properties.simulation.chargeStation.items():
    #     charge = Charge(name=station.name, coordinate=station.coordinate,
    #                     total_workload=0, completed_workload=0,
    #                     task_dependency=[],
    #                     required_performance={},
    #                     other_attrs={},
    #                     charging_speed=station.chargingSpeed)
    #     self.charge_stations.append(charge)
    #     chargeStation
    #     base_00: # 基地
    #     name: base_00
    #     coordinate: [0.0, 0.0]
    #     chargingSpeed: 10


    simulator = Simulator(tasks=tasks, robots=robots, task_priority=task_priority, scenario=scenarios[args.scenario])
    simulator.run_simulation()

if __name__ == '__main__':
    main()
