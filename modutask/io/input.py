from typing import Dict, Type, List
import inspect, logging, yaml
import networkx as nx
from modutask.core import *
from modutask.io.config_variable import *

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

class Input:
    """ タスク、モジュール、ロボットのデータをyamlから読み込むクラス """

    def __init__(self, prop: Dict[str, str]):
        self.prop = prop
    
    def load_tasks(self) -> Dict[str, BaseTask]:
        """ タスクを読み込む """
        try:
            with open(self.prop[Variable.PROPERTY.TASK], 'r') as f:
                task_config = yaml.safe_load(f)
        except FileNotFoundError as e:
            logging.error(f"File not found: {e}")
            raise
        task_classes = find_subclasses_by_name(BaseTask)
        tasks = {}
        for task_name, task_data in task_config.items():
            task_class = task_classes.get(task_data[Variable.TASK.CLASS])
            if task_class is None:
                logging.error(f"Unknown task class: {task_data[Variable.TASK.CLASS]} in {task_name}")
                raise ValueError(f"Unknown task class: {task_data[Variable.TASK.CLASS]} in {task_name}")

            # `task_class` の `__init__` で必要な引数を取得
            init_args = get_class_init_args(task_class)

            # 渡すべき引数をフィルタリング
            filtered_args = {
                k: v for k, v in task_data.items() if k in init_args
            }

            # required_performanceを PerformanceAttributes のdictに変更
            required_performance = {}
            for name, value in task_data[Variable.TASK.REQUIRED_PERFORMANCE].items():
                if name in PerformanceAttributes.__members__:
                    required_performance[PerformanceAttributes[name]] = value
                else:
                    logging.error(f"Invalid performance attribute: '{name}' in {task_name}")
                    raise ValueError(f"{task_name}: Invalid performance attribute: '{name}' in {task_name}")
            filtered_args.update({
                Variable.TASK.REQUIRED_PERFORMANCE: required_performance
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
            with open(self.prop[Variable.PROPERTY.TASK_DEPENDENCY], 'r') as f:
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
            with open(self.prop[Variable.PROPERTY.MODULE_TYPE], 'r') as f:
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
            with open(self.prop[Variable.PROPERTY.MODULE], 'r') as f:
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
            
            
            module_type = module_types.get(module_data[Variable.MODULE.TYPE])
            module_state = ModuleState[module_data[Variable.MODULE.STATE]]
            if module_type is None:
                logging.error(f"Unknown module type: {module_data[Variable.MODULE.TYPE]}")
                raise ValueError(f"Unknown module type: {module_data[Variable.MODULE.TYPE]}")
            filtered_args.update({
                Variable.MODULE.TYPE: module_type,
                Variable.MODULE.STATE: module_state
                })

            modules[module_name] = Module(**filtered_args)
        return modules
    
    def load_robot_types(self, module_types: Dict[str, ModuleType]) -> Dict[str, RobotType]:
        """ ロボットタイプを読み込む """
        try:
            with open(self.prop[Variable.PROPERTY.ROBOT_TYPE], 'r') as f:
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
            
            required_modules = {}
            for name, value in type_data[Variable.ROBOT_TYPE.REQUIRED_MODULES].items():
                if name in module_types:
                    required_modules[module_types[name]] = value
                else:
                    logging.error(f"Invalid module-type name: '{name}' in {type_name}.")
                    raise ValueError(f"Invalid module-type name: '{name}' in {type_name}.")
            performance = {}
            for name, value in type_data[Variable.ROBOT_TYPE.PERFORMANCE].items():
                if name in PerformanceAttributes.__members__:
                    performance[PerformanceAttributes[name]] = value
                else:
                    logging.error(f"Invalid performance attribute: '{name}' in {type_name}.")
                    raise ValueError(f"Invalid performance attribute: '{name}' in {type_name}.")
            filtered_args.update({
                Variable.ROBOT_TYPE.REQUIRED_MODULES: required_modules,
                Variable.ROBOT_TYPE.PERFORMANCE: performance
                })

            robot_types[type_name] = RobotType(**filtered_args)
        return robot_types
    
    def load_robots(self, robot_types: Dict[str, RobotType], modules: Dict[str, Module]) -> Dict[str, Robot]:
        """ ロボットを読み込む """
        try:
            with open(self.prop[Variable.PROPERTY.ROBOT], 'r') as f:
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
            
            robot_type = robot_types.get(robot_data[Variable.ROBOT.TYPE])
            if robot_type is None:
                logging.error(f"Unknown robot type: {robot_data[Variable.ROBOT.TYPE]}")
                raise ValueError(f"Unknown robot type: {robot_data[Variable.ROBOT.TYPE]}")
            component = []
            for module_name in robot_data[Variable.ROBOT.COMPONENT]:
                if module_name not in modules:  # 存在しないモジュールはエラーを発生させる
                    raise ValueError(f"Unknown module: {module_name}")
                component.append(modules[module_name])
            filtered_args.update({
                Variable.ROBOT.TYPE: robot_type,
                Variable.ROBOT.COMPONENT: component
                })
            robots[robot_name] = Robot(**filtered_args)
        return robots
    
    def load_task_priority(self, robots: Dict[str, Robot], tasks: Dict[str, BaseTask]) -> Dict[Robot, List[str]]:
        """ 各ロボットのタスク優先順位を読み込む """
        try:
            with open(self.prop[Variable.PROPERTY.TASK_PRIORITY], 'r') as f:
                priority_config = yaml.safe_load(f)
        except FileNotFoundError as e:
            logging.error(f"File not found: {e}")
            raise
        # 型チェック（すべての値が list であること）
        task_priority = {}
        for k, v in priority_config.items():
            if not isinstance(v, list):
                logging.error("Task_priority only accepts list of task_name.")
                raise ValueError("Task_priority only accepts list of task_name.")
            task_priority[robots[k]] = v
        return task_priority
    
    def load_scenarios(self) -> Dict[str, BaseScenario]:
        """ 故障シナリオを読み込む """
        try:
            with open(self.prop[Variable.PROPERTY.SCENARIO], 'r') as f:
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