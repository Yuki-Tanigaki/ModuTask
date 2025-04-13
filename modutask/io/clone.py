from copy import deepcopy
from modutask.core import *
from modutask.utils.logger import raise_with_log

def clone_module_types(module_types: dict[str, ModuleType]) -> dict[str, ModuleType]:
    return deepcopy(module_types)

def clone_module(modules: dict[str, Module]) -> dict[str, Module]:
    return deepcopy(modules)

def clone_robots_types(robot_types: dict[str, RobotType]) -> dict[str, RobotType]:
    return deepcopy(robot_types)

def clone_simulation_map(simulation_map: SimulationMap) -> SimulationMap:
    return deepcopy(simulation_map)

def clone_risk_scenarios(risk_scenarios: dict[str, BaseRiskScenario]) -> dict[str, BaseRiskScenario]:
    return deepcopy(risk_scenarios)

def clone_task_priorities(task_priorities: dict[str, list[str]]) -> dict[str, list[str]]:
    return deepcopy(task_priorities)

def clone_robots(robots: dict[str, Robot], modules: dict[str, Module]) -> dict[str, Robot]:
    clone_robots = {}
    for robot_name, robot_data in robots.items():
        robot_type = robot_data.type
        name = robot_data.name
        coordinate = robot_data.coordinate
        component = []
        for module in robot_data.component_required:
            component.append(modules[module.name])
        clone_robots[robot_name] = Robot(
            robot_type=robot_type,
            name=name,
            coordinate=coordinate,
            component=component
        )
    return clone_robots

def clone_tasks(tasks: dict[str, BaseTask], modules: dict[str, Module], robots: dict[str, Robot]) -> dict[str, BaseTask]:
    clone_dependency = {}
    clone_tasks: dict[str, BaseTask] = {}
    for task_name, task in tasks.items():
        clone_dependency[task_name] = [t.name for t in task.task_dependency]
        if type(task) is Transport:
            clone = Transport(
                name=deepcopy(task_name),
                coordinate=deepcopy(task.coordinate),
                total_workload=deepcopy(task.total_workload),
                completed_workload=deepcopy(task.completed_workload),
                required_performance=deepcopy(task.required_performance),
                origin_coordinate=deepcopy(task.origin_coordinate),
                destination_coordinate=deepcopy(task.destination_coordinate),
                transport_resistance=deepcopy(task.transport_resistance),
            )
        elif type(task) is Manufacture:
            clone = Manufacture(
                name=deepcopy(task.name),
                coordinate=deepcopy(task.coordinate),
                total_workload=deepcopy(task.total_workload),
                completed_workload=deepcopy(task.completed_workload),
                required_performance=deepcopy(task.required_performance)
            )
        elif type(task) is TransportModule:
            module_name = task._target_module.name
            clone = TransportModule(
                name=deepcopy(task.name), 
                coordinate=deepcopy(task.coordinate),
                required_performance=deepcopy(task.required_performance),
                origin_coordinate=deepcopy(task.origin_coordinate),
                destination_coordinate=deepcopy(task.destination_coordinate),
                transport_resistance=deepcopy(task.transport_resistance),
                total_workload=deepcopy(task.total_workload),
                completed_workload=deepcopy(task.completed_workload),
                target_module=modules[module_name],
                )
        elif type(task) is Assembly:
            robot_name = task._target_robot.name
            clone = Assembly(
                name=deepcopy(task.name), 
                robot=robots[robot_name],
                )
        else:
            raise_with_log(ValueError, f"Clone of {task.__class__} is not defined {task_name}.")
        clone_tasks[task_name] = clone
    for name, task in clone_tasks.items():
        task_dependency = []
        for task_name in clone_dependency[name]:
            task_dependency.append(clone_tasks[task_name])
        task.initialize_task_dependency(task_dependency=task_dependency)
    return clone_tasks