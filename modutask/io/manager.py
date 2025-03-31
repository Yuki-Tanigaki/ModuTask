import logging, yaml, os
from modutask.core import *
from modutask.io.input import *
from modutask.io.output import *

logger = logging.getLogger(__name__)

class DataManager:
    """ タスク、モジュール、ロボットのデータを管理するクラス """

    def __init__(self, prop_file: str):
        try:
            with open(prop_file, 'r') as f:
                self.prop = yaml.safe_load(f)
        except FileNotFoundError as e:
            raise_with_log(FileNotFoundError, f"File not found: {e}.")
            
        self.tasks = None
        self.module_types = None
        self.modules = None
        self.robot_types = None
        self.robots = None
        self.map = None
        self.risk_scenarios = None
        self.task_priorities = None

    def load(self):
        self.tasks = load_tasks(file_path=self.prop['load']['task'])
        self.tasks = load_task_dependency(file_path=self.prop['load']['task_dependency'], tasks=self.tasks)
        self.module_types = load_module_types(file_path=self.prop['load']['module_type'])
        self.modules = load_modules(file_path=self.prop['load']['module'], module_types=self.module_types)
        self.robot_types = load_robot_types(file_path=self.prop['load']['robot_type'], module_types=self.module_types)
        self.robots = load_robots(file_path=self.prop['load']['robot'], robot_types=self.robot_types, modules=self.modules)
        self.check_duplicate_modules(robots=self.robots)
        self.simulation_map = load_simulation_map(file_path=self.prop['load']['map'])
        self.risk_scenarios = load_risk_scenarios(file_path=self.prop['load']['risk_scenario'])
        if os.path.exists(self.prop['load']['task_priority']):
            self.task_priorities = load_task_priorities(file_path=self.prop['load']['task_priority'], robots=self.robots, tasks=self.tasks)
        else:
            logger.info(f"{self.prop['load']['task_priority']} does not exist. Skipping load_task_priorities.")        

    def save(self):
        save_tasks(tasks=self.tasks, file_path=self.prop['save']['task'])
        save_task_dependency(tasks=self.tasks, file_path=self.prop['save']['task_dependency'])
        save_module_types(module_types=self.module_types, file_path=self.prop['save']['module_type'])
        save_module(modules=self.modules, file_path=self.prop['save']['module'])
        save_robot_types(robot_types=self.robot_types, file_path=self.prop['save']['robot_type'])
        save_robot(robots=self.robots, file_path=self.prop['save']['robot'])
        save_simulation_map(simulation_map=self.simulation_map, file_path=self.prop['save']['map'])
        save_risk_scenarios(risk_scenarios=self.risk_scenarios, file_path=self.prop['save']['risk_scenario'])
        save_task_priorities(task_priorities=self.task_priorities, file_path=self.prop['save']['task_priority'])
    
    def check_duplicate_modules(self, robots: dict[str, Robot]) -> bool:
        """
        ロボットごとのモジュール名の重複をチェックする関数。
        重複がある場合はエラーを出力し、Falseを返す。
        """
        all_module_names = []
        for robot_name, robot in robots.items():
            module_names = [module.name for module in robot.component_required]
            duplicates = set(name for name in module_names if module_names.count(name) > 1)
            if duplicates:
                logging.error(f"Robot '{robot_name}' has duplicate modules: {duplicates}.")
                raise ValueError(f"Robot '{robot_name}' has duplicate modules: {duplicates}.")
            all_module_names.extend(module_names)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run the robotic system simulator.")
    parser.add_argument("--property_file", type=str, help="Path to the property file")
    args = parser.parse_args()

    manager = DataManager(args.property_file)
    manager.load()
    print(manager.tasks)
    print(manager.modules)
    print(manager.robots)
    print(manager.map)
    print(manager.risk_scenarios)
    print(manager.task_priorities)
    manager.save()

if __name__ == '__main__':
    main()
