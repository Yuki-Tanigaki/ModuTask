import yaml
import networkx as nx
from typing import Dict, List
from modutask.core import *

class Output:
    def save_tasks(self, tasks: Dict[str, BaseTask], filepath: str = "task.yaml"):
        def task_to_yaml_dict(task: BaseTask) -> dict:
            base = {
                "name": task.name,
                "class": type(task).__name__,
                "coordinate": list(task.coordinate),
                "required_performance": {
                    attr.name: float(task.required_performance.get(attr, 0.0))
                    for attr in PerformanceAttributes
                }
            }

            if isinstance(task, Transport):
                base.update({
                    "origin_coordinate": list(task.origin_coordinate),
                    "destination_coordinate": list(task.destination_coordinate),
                    "transportability": float(task.transportability),
                    "total_workload": float(task.total_workload),
                    "completed_workload": float(task.completed_workload)
                })
            elif isinstance(task, Manufacture):
                base.update({
                    "total_workload": float(task.total_workload),
                    "completed_workload": float(task.completed_workload)
                })

            return {task.name: base}
        
        yaml_dict = {}
        for task_name, task in tasks.items():
            yaml_dict.update(task_to_yaml_dict(task))
        with open(filepath, "w") as f:
            yaml.dump(yaml_dict, f, sort_keys=False)
    
    def save_task_dependency(self, tasks: Dict[str, BaseTask], filepath: str = "task_dependency.yaml"):
        dependency_dict = {}
        for task_name, task in tasks.items():
            dependency_dict[task_name] = [t.name for t in task.task_dependency]

        print(dependency_dict)
        # DAGを構築（依存先 → タスク）
        G = nx.DiGraph()
        for task, deps in dependency_dict.items():
            for dep in deps:
                G.add_edge(dep, task)

        # ルートノード（入次数0）
        roots = [n for n in G.nodes if G.in_degree(n) == 0]

        # ノードを展開（何度でも再帰的に展開）
        def expand_node_full(node, G):
            children = list(G.successors(node))
            if not children:
                return []
            return [{child: expand_node_full(child, G)} for child in children]

        # ルートから再帰展開
        yaml_structure = {root: expand_node_full(root, G) for root in roots}
        print(yaml_structure)
        with open(filepath, "w") as f:
            yaml.dump(yaml_structure, f, sort_keys=False, allow_unicode=True)
    
    def save_module_types(self, module_types: Dict[str, ModuleType], filepath: str = "module_type.yaml"):
        data = {}
        for type_name, module_type in module_types.items():
            data[type_name] = {
                "name": module_type.name,
                "max_battery": module_type.max_battery
            }
        with open(filepath, "w") as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True)

    def save_module(self, modules: Dict[str, Module], filepath: str = "module.yaml"):
        data = {}
        for module_name, mod in modules.items():
            data[module_name] = {
                "name": mod.name,
                "module_type": mod.type.name if hasattr(mod.type, 'name') else str(mod.type),
                "coordinate": list(mod.coordinate),
                "battery": mod.battery,
                "operating_time": mod.operating_time,
                "state": mod.state.name if hasattr(mod.state, 'name') else str(mod.state),
            }
        with open(filepath, "w") as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True)
    
    def save_robot_types(self, robot_types: Dict[str, RobotType], filepath: str = "robot_type.yaml"):
        output = {}
        for name, robot_type in robot_types.items():
            output[name] = {
                "name": robot_type.name,
                "required_modules": robot_type.required_modules,
                "performance": {attr.name: value for attr, value in robot_type.performance.items()},
                "power_consumption": robot_type.power_consumption,
                "recharge_trigger": robot_type.recharge_trigger,
            }
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(output, f, allow_unicode=True, sort_keys=False)
    
    def save_robot(self, robots: Dict[str, Robot], filepath: str = "robot.yaml"):
        output = {}
        for name, robot in robots.items():
            output[name] = {
                "name": robot.name,
                "robot_type": robot.type.name,
                "coordinate": list(robot.coordinate),
                "component": [module.name for module in robot.component_required],
            }

        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(output, f, allow_unicode=True, sort_keys=False)

    def save_task_priority(self, task_priority: Dict[Robot, List[str]], filepath: str = "task_priority.yaml"):
        serializable_data = {robot.name: tasks for robot, tasks in task_priority.items()}
        with open(filepath, 'w') as f:
            yaml.dump(serializable_data, f, default_flow_style=False, sort_keys=False)