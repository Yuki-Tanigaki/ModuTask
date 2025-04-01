from typing import Type, Any
from enum import Enum
import inspect, logging, yaml
import networkx as nx
from modutask.core import *
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)

CLASS = 'class'
NAME = 'name'
MODULE_TYPE = 'module_type'
REQUIRED_MODULES = 'required_modules'
ROBOT_TYPE = 'robot_type'
COMPONENT = 'component'

enum_classes = {
    'PerformanceAttributes': PerformanceAttributes,
    'ModuleState': ModuleState,
}

yaml.add_multi_constructor("!", lambda loader, suffix, node: _enum_constructor(loader, suffix, node))  # PyYAMLにカスタムタグを登録

def load_tasks(file_path: str) -> dict[str, BaseTask]:
    """ タスクを読み込む """
    try:
        with open(file_path, 'r') as f:
            task_config = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError as e:
        raise_with_log(FileNotFoundError, f"File not found: {e}.")

    task_classes = _find_subclasses_by_name(base_class=BaseTask)
    tasks = {}
    for task_name, task_data in task_config.items():
        task_class = task_classes.get(task_data[CLASS])
        if task_class is None:
            raise_with_log(ValueError, f"Unknown task class: {task_data[CLASS]} in {task_name}.")

        filtered_args = _get_class_init_args(cls=task_class, input_data=task_data, name=task_name)
        tasks[task_name] = task_class(**filtered_args)
    
    return tasks

def load_task_dependency(file_path: str, tasks: dict[str, BaseTask]) -> dict[str, BaseTask]:
    """ タスク依存関係を読み込む """
    try:
        with open(file_path, 'r') as f:
            dependencies = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError as e:
        raise_with_log(FileNotFoundError, f"File not found: {e}.")

    def build_graph(graph, name, content):
        """ 有向グラフ作成 """
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
    
    task_dependency_g = nx.DiGraph()
    for node_name, content in dependencies.items():
        if node_name not in tasks:
            raise_with_log(ValueError, f"Unknown task name: '{node_name}'")
        build_graph(task_dependency_g, node_name, content)
    if not nx.is_directed_acyclic_graph(task_dependency_g):  # 非巡回
        raise_with_log(RuntimeError, f"Cyclic task dependency detected.")
    
    for name, task in tasks.items():
        ancestors = nx.ancestors(task_dependency_g, name)
        task_dependency = []
        for ancestor in ancestors:
            task_dependency.append(tasks[ancestor])
        task.initialize_task_dependency(task_dependency=task_dependency)
    return tasks
    
def load_module_types(file_path: str) -> dict[str, ModuleType]:
    """ モジュールタイプを読み込む """
    try:
        with open(file_path, 'r') as f:
            module_type_config = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError as e:
        raise_with_log(FileNotFoundError, f"File not found: {e}.")

    module_types = {}
    for type_name, type_data in module_type_config.items():
        filtered_args = _get_class_init_args(cls=ModuleType, input_data=type_data, name=type_name)
        module_types[type_name] = ModuleType(**filtered_args)
    return module_types

def load_modules(file_path: str, module_types: dict[str, ModuleType]) -> dict[str, Module]:
    """ モジュールを読み込む """
    try:
        with open(file_path, 'r') as f:
            module_config = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError as e:
        raise_with_log(FileNotFoundError, f"File not found: {e}.")

    modules = {}
    for module_name, module_data in module_config.items():
        filtered_args = _get_class_init_args(cls=Module, input_data=module_data, name=module_name)
                
        module_type = module_types.get(module_data[MODULE_TYPE])
        if module_type is None:
            raise_with_log(ValueError, f"Unknown module type: {module_data[MODULE_TYPE]}.")
        filtered_args.update({MODULE_TYPE: module_type})
        modules[module_name] = Module(**filtered_args)
    return modules

def load_robot_types(file_path: str, module_types: dict[str, ModuleType]) -> dict[str, RobotType]:
    """ ロボットタイプを読み込む """
    try:
        with open(file_path, 'r') as f:
            robot_type_config = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError as e:
        raise_with_log(FileNotFoundError, f"File not found: {e}.")
    
    robot_types = {}
    for type_name, type_data in robot_type_config.items():
        filtered_args = _get_class_init_args(cls=RobotType, input_data=type_data, name=type_name)
        
        required_modules = {}
        for name, value in type_data[REQUIRED_MODULES].items():
            if name in module_types:
                required_modules[module_types[name]] = value
            else:
                raise_with_log(ValueError, f"Invalid module-type name: '{name}' in {type_name}.")
        filtered_args.update({REQUIRED_MODULES: required_modules})

        robot_types[type_name] = RobotType(**filtered_args)
    return robot_types

def load_robots(file_path: str, robot_types: dict[str, RobotType], modules: dict[str, Module]) -> dict[str, Robot]:
    """ ロボットを読み込む """
    try:
        with open(file_path, 'r') as f:
            robot_config = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError as e:
        raise_with_log(FileNotFoundError, f"File not found: {e}.")
    robots = {}
    for robot_name, robot_data in robot_config.items():
        filtered_args = _get_class_init_args(cls=Robot, input_data=robot_data, name=robot_name)
        
        robot_type = robot_types.get(robot_data[ROBOT_TYPE])
        if robot_type is None:
            raise_with_log(ValueError, f"Unknown robot type: {robot_data[ROBOT_TYPE]}.")
        component = []
        for module_name in robot_data[COMPONENT]:
            if module_name not in modules:  # 存在しないモジュールはエラーを発生させる
                raise_with_log(ValueError, f"Unknown module: {module_name}.")
            component.append(modules[module_name])
        filtered_args.update({
            ROBOT_TYPE: robot_type,
            COMPONENT: component
            })
        robots[robot_name] = Robot(**filtered_args)
    return robots

def load_simulation_map(file_path: str) -> SimulationMap:
    """ ロボットを読み込む """
    try:
        with open(file_path, 'r') as f:
            map_config = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError as e:
        raise_with_log(FileNotFoundError, f"File not found: {e}.")
    
    charge_stations = {}
    for location_name, location_data in map_config.items():
        filtered_args = _get_class_init_args(cls=Charge, input_data=location_data, name=location_name)
        charge_stations[location_name] = Charge(**filtered_args)
    return SimulationMap(charge_stations=charge_stations)

def load_risk_scenarios(file_path: str) -> dict[str, BaseRiskScenario]:
    """ 故障シナリオを読み込む """
    try:
        with open(file_path, 'r') as f:
            scenario_config = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError as e:
        raise_with_log(FileNotFoundError, f"File not found: {e}.")
    
    scenario_classes = _find_subclasses_by_name(BaseRiskScenario)
    scenarios = {}
    for scenario_name, scenario_data in scenario_config.items():
        scenario_class = scenario_classes.get(scenario_data["class"])
        if scenario_class is None:
            raise_with_log(ValueError, f"Unknown task class: {scenario_data['class']}.")

        filtered_args = _get_class_init_args(cls=scenario_class, input_data=scenario_data, name=scenario_name)
        scenarios[scenario_name] = scenario_class(**filtered_args)

    return scenarios

def load_task_priorities(file_path: str, robots: dict[str, Robot], tasks: dict[str, BaseTask]) -> dict[str, list[str]]:
    """ 各ロボットのタスク優先順位を読み込む """
    try:
        with open(file_path, 'r') as f:
            priority_config = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError as e:
        raise_with_log(FileNotFoundError, f"File not found: {e}.")

    task_priorities = {}
    for k, v in priority_config.items():
        if not isinstance(v, list):
            raise_with_log(ValueError, "Task_priority only accepts list of task_name.")
        task_priorities[robots[k].name] = [task_name for task_name in v]
    return task_priorities

def _find_subclasses_by_name(base_class: Type) -> dict[str, Type]:
    """
    指定された基底クラスのすべてのサブクラスを探索し、クラス名をキーとする辞書を返す

    :param base_class: 基底クラス
    :return: クラス名をキー、クラスオブジェクトを値とする辞書
    """
    subclasses = {}
    for cls in base_class.__subclasses__():
        subclasses[cls.__name__] = cls  # クラス名 (__name__) をキーとして登録
    return subclasses

def _get_class_init_args(cls: Type, input_data: dict[str, Any], name) -> dict[str, Any]:
    """ clsの __init__ 引数にinput_dataを成形 """
    signature = inspect.signature(cls.__init__)
    init_args = [param for param in signature.parameters]
    # 渡すべき引数をフィルタリング
    filtered_args = {
        k: v for k, v in input_data.items() if k in init_args
    }
    filtered_args.update({NAME: name})

    return filtered_args

def _enum_constructor(loader, tag_suffix, node):
    """ Enum辞書の読み込みハンドラ """
    tag_name = tag_suffix.lstrip('!')
    enum_class = enum_classes.get(tag_name)
    if not isinstance(enum_class, type) or not issubclass(enum_class, Enum):
        raise_with_log(ValueError, f"!{tag_name} is not a valid Enum type")
    
    if isinstance(node, yaml.ScalarNode):
        key = loader.construct_scalar(node)
        return enum_class[key]

    elif isinstance(node, yaml.MappingNode):
        raw_mapping = loader.construct_mapping(node)
        return {
            enum_class[key]: raw_mapping.get(key, 0.0) for key in enum_class.__members__
        }

    else:
        raise raise_with_log(TypeError, f"Unsupported YAML node type for tag '!{tag_name}': {type(node)}")
