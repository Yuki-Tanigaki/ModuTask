

class DataLoader:
    def __init__(self):
        

    def load_module_types(self) -> Dict[str, ModuleType]:
        """ モジュールタイプを読み込む """
        return {
            type_name: ModuleType(name=type_name, max_battery=type_data["max_battery"])
            for type_name, type_data in self._module_type_config.items()
        }

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

    def load_tasks(self) -> Dict[str, Task]:
        """ タスクを読み込む """
        task_classes = find_subclasses_by_name(Task)
        tasks = {}
        for task_name, task_data in self._task_config.items():
            task_class = task_classes.get(task_data["class"])
            if task_class is None:
                raise ValueError(f"Unknown task class: {task_data['class']}")

            # 依存するタスクの取得
            task_dependency = [tasks[dep_name] for dep_name in task_data["task_dependency"] if dep_name in tasks]

            # 必要なロボット能力の取得
            required_performance = {
                RobotPerformanceAttributes[name]: value
                for name, value in task_data["required_performance"].items()
                if name in RobotPerformanceAttributes.__members__
            }

            # `task_class` の `__init__` で必要な引数を取得
            task_init_args = get_class_init_args(task_class)

            # 渡すべき引数をフィルタリング
            filtered_args = {
                k: v for k, v in task_data.items() if k in task_init_args
            }

            # 必須の共通引数を追加
            filtered_args.update({
                "name": task_name,
                "coordinate": np.array(task_data['coordinate']),
                "total_workload": task_data["total_workload"],
                "completed_workload": task_data["completed_workload"],
                "task_dependency": task_dependency,
                "required_performance": required_performance,
                "other_attrs": task_data.get("other_attrs", {})
            })

            # クラスのコンストラクタに必要な引数だけを渡してインスタンス化
            tasks[task_name] = task_class(**filtered_args)
        return tasks

    def load_modules(self, module_types: Dict[str, ModuleType]) -> Dict[str, Module]:
        """ モジュールを読み込む """
        modules = {}
        for module_id, module_data in self._module_config.items():
            module_type = module_types.get(module_data["module_type"])
            if module_type is None:
                raise ValueError(f"Unknown module type: {module_data['module_type']}")
            modules[module_id] = Module(
                module_type=module_type,
                name=module_id,
                coordinate=tuple(module_data["coordinate"]),
                battery=module_data["battery"],
                state=ModuleState.from_value(module_data["state"])
            )
        return modules

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