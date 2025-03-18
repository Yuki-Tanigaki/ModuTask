import pytest
import yaml
from pathlib import Path
from omegaconf import OmegaConf
from modutask.robotic_system.manager import DataManager
from modutask.robotic_system.core import ModuleType, RobotType, Task, Module, Robot

@pytest.fixture
def config_files(tmp_path: Path):
    """ 設定ファイルを一時ディレクトリに作成して返す """
    config_data = {
        "task.yaml": {
            "task1": {
                "class": "Manufacture",
                "coordinate": [0, 0],
                "total_workload": 10,
                "completed_workload": 0,
                "task_dependency": [],
                "required_performance": {"MANUFACTURE": 1},
                "other_attrs": {}
            },
            "task2": {
                "class": "Transport",
                "coordinate": [0, 0],
                "total_workload": 10,
                "completed_workload": 0,
                "task_dependency": [],
                "required_performance": {"MANUFACTURE": 1},
                "other_attrs": {},
                "origin_coordinate": [0.0, 0.0],
                "destination_coordinate": [5.0, 5.0],
                "transportability": 0.5
            }
        },
        "module_type.yaml": {
            "battery": {"max_battery": 100}
        },
        "robot_type.yaml": {
            "worker": {
                "required_modules": {"battery": 1},
                "performance": {"MANUFACTURE": 1},
                "power_consumption": 5
            }
        },
        "module.yaml": {
            "battery1": {
                "module_type": "battery",
                "coordinate": [0, 0],
                "battery": 100,
                "state": "FUNCTIONAL"
            }
        },
        "robot.yaml": {
            "robot1": {
                "robot_type": "worker",
                "coordinate": [0, 0],
                "components": ["battery1"],
                "task_priority": ["task2", "task1"]
            }
        }
    }

    file_paths = {}
    for filename, content in config_data.items():
        file_path = tmp_path / filename
        with file_path.open("w", encoding="utf-8") as f:
            yaml.dump(content, f)  # YAMLファイルとして保存
        file_paths[filename.split(".")[0]] = str(file_path)

    return file_paths


def test_load_module_types(config_files):
    manager = DataManager(config_files)
    module_types = manager.load_module_types()
    assert "battery" in module_types
    assert isinstance(module_types["battery"], ModuleType)
    assert module_types["battery"].max_battery == 100


def test_load_robot_types(config_files):
    manager = DataManager(config_files)
    module_types = manager.load_module_types()
    robot_types = manager.load_robot_types(module_types)
    assert "worker" in robot_types
    assert isinstance(robot_types["worker"], RobotType)
    assert robot_types["worker"].power_consumption == 5


def test_load_tasks(config_files):
    manager = DataManager(config_files)
    tasks = manager.load_tasks()
    assert "task1" in tasks
    assert isinstance(tasks["task1"], Task)
    assert tasks["task1"].total_workload == 10


def test_load_modules(config_files):
    manager = DataManager(config_files)
    module_types = manager.load_module_types()
    modules = manager.load_modules(module_types)
    assert "battery1" in modules
    assert isinstance(modules["battery1"], Module)
    assert modules["battery1"].battery == 100


def test_load_robots(config_files):
    manager = DataManager(config_files)
    module_types = manager.load_module_types()
    robot_types = manager.load_robot_types(module_types)
    tasks = manager.load_tasks()
    modules = manager.load_modules(module_types)
    robots = manager.load_robots(robot_types, modules, tasks)
    assert "robot1" in robots
    assert isinstance(robots["robot1"], Robot)
    assert robots["robot1"].coordinate == (0, 0)
