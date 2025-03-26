

class DataLoader:
    def __init__(self):
        


    def load_robot_types(self, module_types: Dict[str, ModuleType]) -> Dict[str, RobotType]:
        """ ロボットタイプを読み込む """
        robot_types = {}
        for type_name, type_data in self._robot_type_config.items():
            required_modules = {}
            for module_name, count in type_data["required_modules"].items():
                if module_name not in module_types:
                    raise ValueError(f"Unknown module type: {module_name}")
                required_modules[module_types[module_name]] = count
            performance = {}
            for name, value in type_data["performance"].items():
                if name not in RobotPerformanceAttributes.__members__:
                    raise ValueError(f"Unknown performance attribute: {name}")
                performance[RobotPerformanceAttributes[name]] = value
            robot_types[type_name] = RobotType(
                name=type_name,
                required_modules=required_modules,
                performance=performance,
                power_consumption=type_data["power_consumption"]
            )
        return robot_types

    def load_robots(self, robot_types: Dict[str, RobotType], modules: Dict[str, Module], 
                    tasks: Dict[str, Task]) -> Dict[str, Robot]:
        """ ロボットを読み込む """
        robots = {}
        for robot_id, robot_data in self._robot_config.items():
            robot_type = robot_types.get(robot_data["robot_type"])
            if robot_type is None:
                raise ValueError(f"Unknown robot type: {robot_data['robot_type']}")
            component = []
            for module_name in robot_data["component"]:
                if module_name not in modules:  # 存在しないモジュールはエラーを発生させる
                    raise ValueError(f"Unknown module: {module_name}")
                component.append(modules[module_name])
            task_priority = []
            for task_name in robot_data["task_priority"]:
                if task_name not in tasks:  # 存在しないタスクはエラーを発生させる
                    raise ValueError(f"Unknown task: {task_name}")
                task_priority.append(tasks[task_name])
                task_priority.append(task_name)
            """ 配列の順列が正しく作成されているかチェックする """
            if sorted(task.name for task in task_priority) != sorted(task.name for task in tasks.values()):
            if sorted(task_priority) != sorted(task.name for task in tasks.values()):
                raise ValueError(f"Invalid task priority: {robot_id} {robot_data['task_priority']}")

            robots[robot_id] = Robot(
                robot_type=robot_type,
                name=robot_id,
                coordinate=tuple(robot_data["coordinate"]),
                component=component,
                task_priority=task_priority
            )