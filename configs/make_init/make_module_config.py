import random
import numpy as np
from modutask.core import *
from modutask.io.output import Output
from config import Config

max_attempts = 100000  # 試行回数
tolerance = 0.05  # 許容誤差
seed = 1234

module_types = {}
for type_name in Config.MODULE.TYPE:
    module_types[type_name] = ModuleType(name=type_name, max_battery=Config.MODULE.BATTERY[type_name])

# cood_list = None
# for _ in range(max_attempts):
#     indices = random.choices(range(len(Config.COORDINATE_SET)), k=sum(Config.MODULE.NUMBER.values()))
#     variance = np.var(indices, ddof=0)  # インデックスの分散
#     if abs(variance - Config.MODULE.LOCATION_VARIANCE) < tolerance:
#         cood_list = [Config.COORDINATE_SET[i] for i in indices]
#         break
# if cood_list is None:
#     raise ValueError

modules = {}
i = 0
for module_type in Config.MODULE.TYPE:
    for _ in range(Config.MODULE.NUMBER[module_type]):
        module = Module(
            module_type = module_types[module_type],
            name=f"m_{i:03}",
            coordinate = [0.0, 0.0],
            battery=Config.MODULE.BATTERY[module_type],
            operating_time=0.0,
            state=ModuleState.ACTIVE
            )
        modules[f"m_{i:03}"] = module
        i += 1

output = Output()
output.save_module_types(module_types=module_types, filepath='./configs/sample001/module_type.yaml')
output.save_module(modules=modules, filepath='./configs/sample001/module.yaml')