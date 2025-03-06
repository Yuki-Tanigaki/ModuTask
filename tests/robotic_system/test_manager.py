import unittest
from unittest.mock import MagicMock
from omegaconf import OmegaConf
import numpy as np
from modutask.robotic_system.core import *
from modutask.robotic_system.manager import *

class TestManager(unittest.TestCase):
    def setUp(self):
        """ 各テスト前に実行する初期化処理 """
        self.mock_properties = MagicMock()
        self.mock_properties.taskConfigFile = "task.yaml"
        self.mock_properties.moduleTypeConfigFile = "module_type.yaml"
        self.mock_properties.robotTypeConfigFile = "robot_type.yaml"
        self.mock_properties.moduleConfigFile = "module.yaml"
        self.mock_properties.robotConfigFile = "robot.yaml"

        self.mock_data = {
            "task.yaml": {
                "task1": {
                    "class": "Transport",
                    "coordinate": [0, 0],
                    "workload": [100, 0],
                    "task_dependency": [],
                    "required_performance": {"TRANSPORT": 10},
                    "deployed_robot": [],
                    "other_attrs": {"category": "Inflatable"},
                    "origin_destination": [[0.0, 0.0], [5.0, 5.0], 0.5]
                },
                "task2": {
                    "class": "Manufacture",
                    "coordinate": [0, 0],
                    "workload": [100, 0],
                    "task_dependency": [],
                    "required_performance": {"MANUFACTURE": 10},
                    "deployed_robot": [],
                    "other_attrs": {"category": "Inflatable"}
                }
            },
            "module_type.yaml": {
                "ModuleA": {"max_battery": 100}
            },
            "robot_type.yaml": {
                "RobotX": {
                    "required_modules": {"ModuleA": 2},
                    "performance": {"TRANSPORT": 5}
                }
            },
            "module.yaml": {
                "mod1": {"module_type": "ModuleA", "coordinate": [1, 1]}
            },
            "robot.yaml": {
                "rob1": {"robot_type": "RobotX", "component": ["mod1"], "coordinate": [2, 2]}
            }
        }

        OmegaConf.load = MagicMock(side_effect=lambda filename: self.mock_data[filename])

        self.manager = Manager(self.mock_properties)

    def test_find_subclasses_by_name(self):
        """ `find_subclasses_by_name` が正しく機能するかをテスト """
        subclasses = find_subclasses_by_name(Task)
        self.assertIn("Transport", subclasses)
        self.assertIn("Manufacture", subclasses)

    def test_str_to_enum(self):
        """ `str_to_enum` の変換が正しく機能するかをテスト """
        self.assertEqual(str_to_enum(RobotPerformanceAttributes, "TRANSPORT"), RobotPerformanceAttributes.TRANSPORT)
        self.assertEqual(str_to_enum(RobotPerformanceAttributes, "MANUFACTURE"), RobotPerformanceAttributes.MANUFACTURE)
        self.assertEqual(str_to_enum(RobotPerformanceAttributes, "INVALID"), None)

    def test_read_module_type(self):
        """ `read_module_type` が ModuleType インスタンスを正しく読み込むかをテスト """
        module_types = self.manager.read_module_type()
        self.assertIn("ModuleA", module_types)
        self.assertEqual(module_types["ModuleA"].name, "ModuleA")
        self.assertEqual(module_types["ModuleA"].max_battery, 100)

    def test_read_robot_type(self):
        """ `read_robot_type` が RobotType インスタンスを正しく読み込むかをテスト """
        module_types = self.manager.read_module_type()
        robot_types = self.manager.read_robot_type(module_types)
        self.assertIn("RobotX", robot_types)
        self.assertEqual(robot_types["RobotX"].name, "RobotX")
        self.assertEqual(robot_types["RobotX"].performance[RobotPerformanceAttributes.TRANSPORT], 5)

    def test_read_module(self):
        """ `read_module` が Module インスタンスを正しく読み込むかをテスト """
        module_types = self.manager.read_module_type()
        modules = self.manager.read_module(module_types)
        self.assertIn("mod1", modules)
        self.assertEqual(modules["mod1"].type.name, "ModuleA")
        np.testing.assert_array_equal(modules["mod1"].coordinate, np.array([1, 1]))

    def test_read_robot(self):
        """ `read_robot` が Robot インスタンスを正しく読み込むかをテスト """
        module_types = self.manager.read_module_type()
        robot_types = self.manager.read_robot_type(module_types)
        modules = self.manager.read_module(module_types)
        robots = self.manager.read_robot(robot_types, modules)
        
        self.assertIn("rob1", robots)
        self.assertEqual(robots["rob1"].type.name, "RobotX")
        np.testing.assert_array_equal(robots["rob1"].coordinate, np.array([2, 2]))
        self.assertEqual(len(robots["rob1"].component), 1)
        self.assertEqual(robots["rob1"].component[0].name, "mod1")

    def test_read_task(self):
        """ `read_task` が Task インスタンスを正しく読み込むかをテスト """
        module_types = self.manager.read_module_type()
        robot_types = self.manager.read_robot_type(module_types)
        modules = self.manager.read_module(module_types)
        robots = self.manager.read_robot(robot_types, modules)
        tasks = self.manager.read_task(robots)
        
        self.assertIn("task1", tasks)
        task = tasks["task1"]

        self.assertIsInstance(task, Transport)
        self.assertEqual(task.name, "task1")
        np.testing.assert_array_equal(task.coordinate, np.array([0, 0]))
        self.assertEqual(task.total_workload, 100)
        self.assertEqual(task.completed_workload, 0)
        self.assertEqual(task.required_performance[RobotPerformanceAttributes.TRANSPORT], 10)
        self.assertEqual(task.deployed_robot, [])

if __name__ == '__main__':
    unittest.main()
