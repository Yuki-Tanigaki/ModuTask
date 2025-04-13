import argparse
import os
import random
import yaml
from modutask.core import *
from modutask.io.output import save_module_types, save_module, save_robot_types

parser = argparse.ArgumentParser(description="")
parser.add_argument("--setting_file", type=str, help="Path to the setting file")
args = parser.parse_args()

enum_classes = {
    'PerformanceAttributes': PerformanceAttributes,
}
def _enum_constructor(loader, tag_suffix, node):
    """ Enum辞書の読み込みハンドラ """
    tag_name = tag_suffix.lstrip('!')
    enum_class = enum_classes.get(tag_name)
    
    if isinstance(node, yaml.ScalarNode):
        key = loader.construct_scalar(node)
        return enum_class[key]

    elif isinstance(node, yaml.MappingNode):
        raw_mapping = loader.construct_mapping(node)
        return {
            enum_class[key]: raw_mapping.get(key, 0.0) for key in enum_class.__members__
        }
yaml.add_multi_constructor("!", lambda loader, suffix, node: _enum_constructor(loader, suffix, node))  # PyYAMLにカスタムタグを登録

# YAMLファイルの読み込み
with open(args.setting_file, "r", encoding="utf-8") as f:
    yaml_data = yaml.load(f, Loader=yaml.FullLoader)

random.seed(yaml_data["module"]["seed"])

module_types: dict[str, ModuleType] = {}
types_battery = {
    "Body": 1,
    "Limb": 5,
    "EndE": 1,
    "Wheel": 15
}
for type_name, battery in types_battery.items():
    module_types[type_name] = ModuleType(name=type_name, max_battery=battery)

cood_list = None
oper_list = None
state_list = None
states = [ModuleState.ACTIVE, ModuleState.ERROR]
# states = [ModuleState.ACTIVE]
indices = random.choices(range(len(yaml_data["module"]["coodinate_set"])), k=yaml_data["module"]["total_modules"])
cood_list = [yaml_data["module"]["coodinate_set"][i] for i in indices]
indices = random.choices(range(len(yaml_data["module"]["operating_time_set"])), k=yaml_data["module"]["total_modules"])
oper_list = [yaml_data["module"]["operating_time_set"][i] for i in indices]
indices = random.choices(range(len(states)), k=yaml_data["module"]["total_modules"])
state_list = [states[i] for i in indices]


modules = {}
i = 0
for module_type, ratio in yaml_data["module"]["module_ratio"].items():
    n = int(yaml_data["module"]["total_modules"]* ratio[0] / ratio[1])
    for _ in range(n):
        module = Module(
            module_type = module_types[module_type],
            name=f"m_{i:03}",
            coordinate=cood_list[i],
            battery=module_types[module_type].max_battery,
            operating_time=oper_list[i],
            state=state_list[i],
            )
        modules[f"m_{i:03}"] = module
        i += 1

robot_types: dict[str, RobotType] = {}
types_required = {
    "TWSH": {
        "required_modules": {
            "Body": 1,
            "Limb": 4,
            "EndE": 1,
            "Wheel": 3,
        },
        "power_consumption": 1,
        "recharge_trigger": 10,
    },
    "TWDH": {
        "required_modules": {
            "Body": 1,
            "Limb": 5,
            "EndE": 2,
            "Wheel": 3,
        },
        "power_consumption": 1,
        "recharge_trigger": 10,
    },
    "QWSH": {
        "required_modules": {
            "Body": 1,
            "Limb": 5,
            "EndE": 1,
            "Wheel": 4,
        },
        "power_consumption": 1,
        "recharge_trigger": 10,
    },
    "QWDH": {
        "required_modules": {
            "Body": 1,
            "Limb": 6,
            "EndE": 2,
            "Wheel": 4,
        },
        "power_consumption": 1,
        "recharge_trigger": 10,
    },
    "Dragon": {
        "required_modules": {
            "Body": 0,
            "Limb": 2,
            "EndE": 1,
            "Wheel": 2,
        },
        "power_consumption": 1,
        "recharge_trigger": 10,
    },
    "Minimal": {
        "required_modules": {
            "Body": 0,
            "Limb": 1,
            "EndE": 1,
            "Wheel": 1,
        },
        "power_consumption": 1,
        "recharge_trigger": 10,
    },
}

for type_name, type_data in types_required.items():
    required_modules = {}
    for name, value in type_data["required_modules"].items():
        required_modules[module_types[name]] = value
    performance = yaml_data["robot"][type_name]["performance"]
    power_consumption: float  # ロボットの消費電力
    recharge_trigger: float  # 充電に戻るバッテリー量の基準
    robot_types[type_name] = RobotType(name=type_name,
                                       required_modules=required_modules,
                                       performance=performance,
                                       power_consumption=type_data["power_consumption"],
                                       recharge_trigger=type_data["recharge_trigger"]
                                       )


os.makedirs(os.path.dirname(yaml_data["config_dir"]["module_type"]), exist_ok=True)
os.makedirs(os.path.dirname(yaml_data["config_dir"]["module"]), exist_ok=True)
os.makedirs(os.path.dirname(yaml_data["config_dir"]["robot_type"]), exist_ok=True)
save_module_types(module_types=module_types, file_path=yaml_data["config_dir"]["module_type"])
save_module(modules=modules, file_path=yaml_data["config_dir"]["module"])
save_robot_types(robot_types=robot_types, file_path=yaml_data["config_dir"]["robot_type"])