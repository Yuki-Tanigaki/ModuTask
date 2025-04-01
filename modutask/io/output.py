import yaml, os
import networkx as nx
from modutask.core import *

class TaggedPerformanceAttributes(dict):
    pass

def performance_attributes_representer(dumper, data):
    return dumper.represent_mapping('!PerformanceAttributes', data)

yaml.add_representer(TaggedPerformanceAttributes, performance_attributes_representer)

def save_tasks(tasks: dict[str, BaseTask], file_path: str = "task.yaml"):
    def task_to_yaml_dict(task: BaseTask) -> dict:
        required_perf = TaggedPerformanceAttributes({
                attr.name: float(task.required_performance.get(attr, 0.0))
                for attr in PerformanceAttributes
            })
        base = {
            "class": type(task).__name__,
            "coordinate": list(task.coordinate),
            "required_performance": required_perf
        }

        if isinstance(task, Transport):
            base.update({
                "origin_coordinate": list(task.origin_coordinate),
                "destination_coordinate": list(task.destination_coordinate),
                "transport_resistance": float(task.transport_resistance),
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
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        yaml.dump(yaml_dict, f, sort_keys=False)

def save_task_dependency(tasks: dict[str, BaseTask], file_path: str = "task_dependency.yaml"):
    dependency_dict = {}
    for task_name, task in tasks.items():
        dependency_dict[task_name] = [t.name for t in task.task_dependency]

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
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        yaml.dump(yaml_structure, f, sort_keys=False, allow_unicode=True)

def save_module_types(module_types: dict[str, ModuleType], file_path: str = "module_type.yaml"):
    output = {}
    for type_name, module_type in module_types.items():
        output[type_name] = {
            "max_battery": module_type.max_battery
        }
    with open(file_path, "w") as f:
        yaml.dump(output, f, sort_keys=False, allow_unicode=True)

def save_module(modules: dict[str, Module], file_path: str = "module.yaml"):
    output = {}
    for module_name, mod in modules.items():
        output[module_name] = {
            "module_type": mod.type.name if hasattr(mod.type, 'name') else str(mod.type),
            "coordinate": list(mod.coordinate),
            "battery": mod.battery,
            "operating_time": mod.operating_time,
            "state": mod.state.name if hasattr(mod.state, 'name') else str(mod.state),
        }
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        yaml.dump(output, f, sort_keys=False, allow_unicode=True)

def save_robot_types(robot_types: dict[str, RobotType], file_path: str = "robot_type.yaml"):
    output = {}
    for name, robot_type in robot_types.items():
        perf = TaggedPerformanceAttributes({
                    attr.name: float(robot_type.performance.get(attr, 0.0))
                    for attr in PerformanceAttributes
                })
        required_modules = {
            module_type.name: count
            for module_type, count in robot_type.required_modules.items()
        }
        output[name] = {
            "required_modules": required_modules,
            "performance": perf,
            "power_consumption": robot_type.power_consumption,
            "recharge_trigger": robot_type.recharge_trigger,
        }
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f, allow_unicode=True, sort_keys=False)

def save_robot(robots: dict[str, Robot], file_path: str = "robot.yaml"):
    output = {}
    for name, robot in robots.items():
        output[name] = {
            "robot_type": robot.type.name,
            "coordinate": list(robot.coordinate),
            "component": [module.name for module in robot.component_required],
        }
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f, allow_unicode=True, sort_keys=False)

def save_simulation_map(simulation_map: SimulationMap, file_path: str = "map.yaml"):
    output = {}
    for name, station in simulation_map.charge_stations.items():
        output[name] = {
            "coordinate": list(station.coordinate),
            "charging_speed": station.charging_speed,
        }
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f, allow_unicode=True, sort_keys=False)

def save_risk_scenarios(risk_scenarios: dict[str, BaseRiskScenario], file_path: str = "_risk_scenario.yaml"):
    output = {}
    for name, scenario in risk_scenarios.items():
        output[name] = {
            "class": type(scenario).__name__,
            "failure_rate": scenario.failure_rate,
            "seed": scenario.seed
        }
        if isinstance(scenario, ExponentialFailure):
            output.update({"failure_rate": scenario.failure_rate})
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f, allow_unicode=True, sort_keys=False)

def save_task_priorities(task_priorities: dict[str, list[str]], file_path: str = "task_priority.yaml"):
    output = {}
    for robot_name, task_names in task_priorities.items():
        output[robot_name] = [task_name for task_name in task_names]
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)