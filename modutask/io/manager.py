from typing import Dict, Type
import inspect, logging, yaml
import networkx as nx
from modutask.core import *
from modutask.io import Variable
 
logger = logging.getLogger(__name__)

def find_subclasses_by_name(base_class: Type) -> Dict[str, Type]:
    """
    指定された基底クラスのすべてのサブクラスを探索し、クラス名をキーとする辞書を返す

    :param base_class: 基底クラス
    :return: クラス名をキー、クラスオブジェクトを値とする辞書
    """
    subclasses = {}
    for cls in base_class.__subclasses__():
        subclasses[cls.__name__] = cls  # クラス名 (__name__) をキーとして登録
    return subclasses

def get_class_init_args(cls):
    """ クラスの __init__ メソッドの引数を取得 """
    signature = inspect.signature(cls.__init__)
    return [param for param in signature.parameters]

class DataManager:
    """ タスク、モジュール、ロボットのデータを管理するクラス """

    def __init__(self, prop_file: str):
        try:
            with open(prop_file, 'r') as f:
                self.prop = yaml.safe_load(f)
        except FileNotFoundError as e:
            logging.error(f"File not found: {e}")
            raise
    
    def load_tasks(self) -> Dict[str, BaseTask]:
        """ タスクを読み込む """
        try:
            with open(self.prop[Variable.Property.TASK], 'r') as f:
                task_config = yaml.safe_load(f)
        except FileNotFoundError as e:
            logging.error(f"File not found: {e}")
            raise
        task_classes = find_subclasses_by_name(BaseTask)
        tasks = {}
        for task_name, task_data in task_config.items():
            task_class = task_classes.get(task_data[Variable.Task.CLASS])
            if task_class is None:
                logging.error(f"Unknown task class: {task_data[Variable.Task.CLASS]} in {task_name}")
                raise ValueError(f"Unknown task class: {task_data[Variable.Task.CLASS]} in {task_name}")

            # `task_class` の `__init__` で必要な引数を取得
            init_args = get_class_init_args(task_class)

            # 渡すべき引数をフィルタリング
            filtered_args = {
                k: v for k, v in task_data.items() if k in init_args
            }

            # 引数に name を追加
            # required_performanceを PerformanceAttributes のdictに変更
            required_performance = {}
            for name, value in task_data[Variable.Task.REQUIRED_PERFORMANCE].items():
                if name in PerformanceAttributes.__members__:
                    required_performance[PerformanceAttributes[name]] = value
                else:
                    logging.error(f"Invalid performance attribute: '{name}' in {task_name}")
                    raise ValueError(f"{task_name}: Invalid performance attribute: '{name}' in {task_name}")
            filtered_args.update({
                Variable.Task.REQUIRED_PERFORMANCE: required_performance
                })

            # クラスのコンストラクタに必要な引数だけを渡してインスタンス化
            tasks[task_name] = task_class(**filtered_args)

        task_dependency_g = self.load_task_dependency(tasks=tasks)
        for name, task in tasks.items():
           ancestors = nx.ancestors(task_dependency_g, name)
           task_dependency = []
           for ancestor in ancestors:
               task_dependency.append(tasks[ancestor])
           task.initialize_task_dependency(task_dependency)
        
        return tasks
    
    def load_task_dependency(self, tasks: Dict[str, BaseTask]) -> nx.DiGraph:
        """ タスク依存関係を読み込む """
        try:
            with open(self.prop[Variable.Property.TASK_DEPENDENCY], 'r') as f:
                dependencies = yaml.safe_load(f)
        except FileNotFoundError as e:
            logging.error(f"File not found: {e}")
            raise

        def build_graph(graph, name, content):
            if not graph.has_node(name):
                graph.add_node(name)
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        for child_name, child_content in item.items():
                            graph.add_edge(name, child_name)
                            build_graph(graph, child_name, child_content)
                    else:
                        graph.add_edge(name, item)
            elif isinstance(content, dict):
                for child_name, child_content in content.items():
                    graph.add_edge(name, child_name)
                    build_graph(graph, child_name, child_content)
        
        # 有向グラフ作成
        task_dependency_g = nx.DiGraph()
        for node_name, content in dependencies.items():
            if node_name not in tasks:
                logging.error(f"Unknown task name: '{node_name}'")
                raise ValueError(f"Unknown task name: '{node_name}'")
            build_graph(task_dependency_g, node_name, content)
        if not nx.is_directed_acyclic_graph(task_dependency_g):
            logging.error(f"Cyclic dependency detected in the task_dependency'")
            raise RuntimeError(f"Cyclic dependency detected in the task_dependency'")
        
        return task_dependency_g
        
    def load_module_types(self) -> Dict[str, ModuleType]:
        """ モジュールタイプを読み込む """
        try:
            with open(self.prop[Variable.Property.MODULE_TYPE], 'r') as f:
                module_type_config = yaml.safe_load(f)
        except FileNotFoundError as e:
            logging.error(f"File not found: {e}")
            raise
        # 必要な引数を取得
        init_args = get_class_init_args(ModuleType)
        module_types = {}
        for type_name, type_data in module_type_config.items():
            filtered_args = {
                k: v for k, v in type_data.items() if k in init_args
            }
            module_types[type_name] = ModuleType(**filtered_args)
        return module_types

    def load_modules(self, module_types: Dict[str, ModuleType]) -> Dict[str, Module]:
        """ モジュールを読み込む """
        try:
            with open(self.prop[Variable.Property.MODULE], 'r') as f:
                module_config = yaml.safe_load(f)
        except FileNotFoundError as e:
            logging.error(f"File not found: {e}")
            raise
        # 必要な引数を取得
        init_args = get_class_init_args(Module)
        modules = {}
        for module_name, module_data in module_config.items():
            filtered_args = {
                k: v for k, v in module_data.items() if k in init_args
            }
            # 引数に name を追加
            
            module_type = module_types.get(module_data[Variable.Module.TYPE])
            if module_type is None:
                logging.error(f"Unknown module type: {module_data[Variable.Module.TYPE]}")
                raise ValueError(f"Unknown module type: {module_data[Variable.Module.TYPE]}")
            filtered_args.update({
                Variable.Module.TYPE: module_type}
                )

            modules[module_name] = Module(**filtered_args)
        return modules

    def load_scenarios(self) -> Dict[str, BaseScenario]:
        """ 故障シナリオを読み込む """
        try:
            with open(self.prop[Variable.Property.SCENARIO], 'r') as f:
                scenario_config = yaml.safe_load(f)
        except FileNotFoundError as e:
            logging.error(f"File not found: {e}")
            raise
        scenario_classes = find_subclasses_by_name(BaseScenario)
        scenarios = {}
        for scenario_name, scenario_data in scenario_config.items():
            scenario_class = scenario_classes.get(scenario_data["class"])
            if scenario_class is None:
                logging.error(f"{scenario_name}: Unknown task class: {scenario_data['class']}")
                raise ValueError(f"{scenario_name}: Unknown task class: {scenario_data['class']}")

            # `tscenario_classes` の `__init__` で必要な引数を取得
            init_args = get_class_init_args(scenario_class)
            # 渡すべき引数をフィルタリング
            filtered_args = {
                k: v for k, v in scenario_data.items() if k in init_args
            }

            # クラスのコンストラクタに必要な引数だけを渡してインスタンス化
            scenarios[scenario_name] = scenario_class(**filtered_args)

        return scenarios
    
    def load_robot_types(self, module_types: Dict[str, ModuleType]) -> Dict[str, RobotType]:
        """ ロボットタイプを読み込む """
        try:
            with open(self.prop[Variable.Property.ROBOT_TYPE], 'r') as f:
                robot_type_config = yaml.safe_load(f)
        except FileNotFoundError as e:
            logging.error(f"File not found: {e}")
            raise
        # 必要な引数を取得
        init_args = get_class_init_args(RobotType)
        robot_types = {}
        for type_name, type_data in robot_type_config.items():
            filtered_args = {
                k: v for k, v in type_data.items() if k in init_args
            }
            # 引数に name を追加
            required_modules = {}
            for name, value in type_data[Variable.RobotType.REQUIRED_MODULES].items():
                if name in module_types:
                    required_modules[module_types[name]] = value
                else:
                    logging.error(f"Invalid module-type name: '{name}' in {type_name}.")
                    raise ValueError(f"Invalid module-type name: '{name}' in {type_name}.")
            performance = {}
            for name, value in type_data[Variable.RobotType.PERFORMANCE].items():
                if name in PerformanceAttributes.__members__:
                    performance[PerformanceAttributes[name]] = value
                else:
                    logging.error(f"Invalid performance attribute: '{name}' in {type_name}.")
                    raise ValueError(f"Invalid performance attribute: '{name}' in {type_name}.")
            filtered_args.update({
                Variable.RobotType.REQUIRED_MODULES: required_modules,
                Variable.RobotType.PERFORMANCE: performance
                })

            robot_types[type_name] = RobotType(**filtered_args)
        return robot_types
    
    def load_robots(self, robot_types: Dict[str, RobotType], modules: Dict[str, Module]) -> Dict[str, Robot]:
        """ ロボットを読み込む """
        try:
            with open(self.prop[Variable.Property.ROBOT], 'r') as f:
                robot_config = yaml.safe_load(f)
        except FileNotFoundError as e:
            logging.error(f"File not found: {e}")
            raise
        # 必要な引数を取得
        init_args = get_class_init_args(Robot)
        robots = {}
        for robot_name, robot_data in robot_config.items():
            filtered_args = {
                k: v for k, v in robot_data.items() if k in init_args
            }
            # 引数に name を追加
            robot_type = robot_types.get(robot_data[Variable.Robot.TYPE])
            if robot_type is None:
                logging.error(f"Unknown robot type: {robot_data[Variable.Robot.TYPE]}")
                raise ValueError(f"Unknown robot type: {robot_data[Variable.Robot.TYPE]}")
            component = []
            for module_name in robot_data[Variable.Robot.COMPONENT]:
                if module_name not in modules:  # 存在しないモジュールはエラーを発生させる
                    raise ValueError(f"Unknown module: {module_name}")
                component.append(modules[module_name])
            filtered_args.update({
                Variable.Robot.TYPE: robot_type,
                Variable.Robot.COMPONENT: component
                })
            robots[robot_name] = Robot(**filtered_args)
        return robots

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run the robotic system simulator.")
    parser.add_argument("--property-file", type=str, help="Path to the property file")
    args = parser.parse_args()

    manager = DataManager(args.property_file)
    tasks = manager.load_tasks()
    module_types = manager.load_module_types()
    modules = manager.load_modules(module_types)
    scenarios = manager.load_scenarios()
    robot_types = manager.load_robot_types(module_types)
    robots = manager.load_robots(robot_types, modules)
    for _, robot in robots.items():
        _, first_value = next(iter(scenarios.items()))
        robot.update_state([first_value])
    print(tasks)
    print(robots)

if __name__ == '__main__':
    main()
