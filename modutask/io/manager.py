import logging, yaml, copy
import numpy as np
from modutask.core import *
from modutask.io.input import *
from modutask.io.output import *
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)

class DataManager:
    """ タスク、モジュール、ロボットのデータを管理するクラス """

    def __init__(self, load_task_priorities: bool):
        self.tasks = None
        self.combined_tasks = None
        self.module_types = None
        self.modules = None
        self.robot_types = None
        self.robots = None
        self.simulation_map = None
        self.risk_scenarios = None
        self.task_priorities = None
        self.load_task_priorities = load_task_priorities

    def clone_for_simulation(self) -> "DataManager":
        clone = DataManager(load_task_priorities=self.load_task_priorities)
        clone.tasks = copy.deepcopy(self.tasks)
        clone.combined_tasks = copy.deepcopy(self.combined_tasks)
        clone.module_types = copy.deepcopy(self.module_types)
        clone.modules = copy.deepcopy(self.modules)
        clone.robot_types = copy.deepcopy(self.robot_types)
        robots = {}
        for robot_name, robot_data in self.robots.items():
            robot_type = robot_data.type
            name = robot_data.name
            coordinate = robot_data.coordinate
            component = []
            for module in robot_data.component_required:
                module_name = module.name
                component.append(clone.modules[module_name])
            robots[robot_name] = Robot(
                robot_type=robot_type,
                name=name,
                coordinate=coordinate,
                component=component
            )
        clone.robots = robots
        clone.simulation_map = copy.deepcopy(self.simulation_map)
        clone.risk_scenarios = copy.deepcopy(self.risk_scenarios)
        clone.task_priorities = copy.deepcopy(self.task_priorities)
        return clone

    def load(self, load_path: dict[str, str]):
        self.tasks = load_tasks(file_path=load_path['task'])
        self.tasks = load_task_dependency(file_path=load_path['task_dependency'], tasks=self.tasks)
        self.combined_tasks = self.tasks
        self.module_types = load_module_types(file_path=load_path['module_type'])
        self.modules = load_modules(file_path=load_path['module'], module_types=self.module_types)
        self.robot_types = load_robot_types(file_path=load_path['robot_type'], module_types=self.module_types)
        self.robots = load_robots(file_path=load_path['robot'], robot_types=self.robot_types, modules=self.modules)
        self.has_duplicate_module()
        self.add_assembly_task()
        self.simulation_map = load_simulation_map(file_path=load_path['map'])
        self.risk_scenarios = load_risk_scenarios(file_path=load_path['risk_scenario'])
        if self.load_task_priorities:
            self.task_priorities = load_task_priorities(file_path=load_path['task_priority'], robots=self.robots, tasks=self.combined_tasks)
            self.permutation_of_tasks()        

    def save(self, save_path: dict[str, str]):
        save_tasks(tasks=self.tasks, file_path=save_path['task'])
        save_task_dependency(tasks=self.tasks, file_path=save_path['task_dependency'])
        save_module_types(module_types=self.module_types, file_path=save_path['module_type'])
        save_module(modules=self.modules, file_path=save_path['module'])
        save_robot_types(robot_types=self.robot_types, file_path=save_path['robot_type'])
        save_robot(robots=self.robots, file_path=save_path['robot'])
        save_simulation_map(simulation_map=self.simulation_map, file_path=save_path['map'])
        save_risk_scenarios(risk_scenarios=self.risk_scenarios, file_path=save_path['risk_scenario'])
        save_task_priorities(task_priorities=self.task_priorities, file_path=save_path['task_priority'])
    
    def has_duplicate_module(self) -> None:
        """
        全ロボットのモジュール名の重複をチェックする関数
        """
        all_module_names = []
        for robot_name, robot in self.robots.items():
            module_names = [module.name for module in robot.component_required]
            duplicates = set(name for name in module_names if module_names.count(name) > 1)
            if duplicates:
                raise_with_log(ValueError, f"Robot has duplicate modules: {duplicates}.")
            all_module_names.extend(module_names)
    
    def add_assembly_task(self) -> None:
        """ モジュール不足のロボット用の組み立てタスクの追加 """
        for robot_name, robot in self.robots.items():
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
                    required_performance={},
                    origin_coordinate=origin_coordinate,
                    destination_coordinate=destination_coordinate,
                    transport_resistance=transport_resistance,
                    total_workload=total,
                    completed_workload=0
                    )
                self.combined_tasks[f'transport_{robot_name}_{module.name}'] = transport
                task_dependency.append(transport)
            if len(robot.missing_components()) != 0:
                assembly = Assembly(name=f'assembly__{robot_name}', robot=robot)
                assembly.initialize_task_dependency(task_dependency=task_dependency)
                self.combined_tasks[f'assembly__{robot_name}'] = assembly

    def permutation_of_tasks(self) -> None:
        """
        task_prioritiesが(全ロボット)と(全タスクの順列)で構成されているかチェックする関数
        """
        missing_robots = [robot_name for robot_name in self.robots if robot_name not in self.task_priorities]
        if missing_robots:
            raise_with_log(RuntimeError, f"Some robots are missing in task_priorities: {missing_robots}.")

        def is_permutation_of_tasks(task_list: list[str], all_tasks: dict[str, BaseTask]) -> bool:
            return set(task_list) == set(all_tasks.keys()) and len(task_list) == len(all_tasks)
        for robot, task_list in self.task_priorities.items():
            if not is_permutation_of_tasks(task_list, self.combined_tasks):
                raise_with_log(RuntimeError, f"The task list is not a permutation of the tasks. ")

def main():
    import argparse
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
    print(manager.tasks)
    print(manager.modules)
    print(manager.robots)
    print(manager.simulation_map)
    print(manager.risk_scenarios)
    print(manager.task_priorities)
    manager.save(save_path=prop["save"])

if __name__ == '__main__':
    main()
