import unittest
from collections import defaultdict
from modutask.robotic_system.core import *

class TestRobotModuleSystem(unittest.TestCase):
    def setUp(self):
        """テストの前に共通のオブジェクトを作成"""
        self.module_type = ModuleType(name="Battery", max_battery=100.0)
        self.module = Module(type=self.module_type, name="Module1", coordinate=(0, 0))
        
        self.robot_type = RobotType(
            name="TransportBot",
            required_modules={self.module_type: 1},
            ability={RobotPerformanceAttributes.TRANSPORT: 5},
            redundancy={}
        )
        self.robot = Robot(
            type=self.robot_type,
            name="Robot1",
            coordinate=(0, 0),
            component=[self.module]
        )
        
        self.task = Task(
            name="Task1",
            coordinate=(10, 10),
            workload=(100, 0),
            task_dependency=[],
            required_abilities={RobotPerformanceAttributes.TRANSPORT: 3},
            other_attrs={}
        )
        
        self.transport_task = Transport(
            name="Transport1",
            coordinate=(0, 0),
            workload=(50, 0),
            task_dependency=[],
            required_abilities={RobotPerformanceAttributes.TRANSPORT: 2},
            other_attrs={},
            origin_destination=((0, 0), (10, 10), 1.0)
        )
        
        self.manufacture_task = Manufacture(
            name="Manufacture1",
            coordinate=(5, 5),
            workload=(20, 0),
            task_dependency=[],
            required_abilities={RobotPerformanceAttributes.MANUFACTURE: 2},
            other_attrs={}
        )

    def test_module_initialization(self):
        """ モジュールの初期化確認 """
        self.assertEqual(self.module.type, self.module_type)
        self.assertEqual(self.module.battery, (100.0, 100.0))
        self.assertEqual(self.module.state, ModuleState.SPARE)

    def test_robot_initialization(self):
        """ ロボットの初期化確認 """
        self.assertEqual(self.robot.type, self.robot_type)
        self.assertEqual(self.robot.component[0], self.module)
        self.assertEqual(self.robot.state, RobotState.INACTIVE)
        self.assertEqual(self.robot.coordinate, (0, 0))

    def test_task_initialization(self):
        """ タスクの初期化確認 """
        self.assertEqual(self.task.name, "Task1")
        self.assertEqual(self.task.coordinate, (10, 10))
        self.assertEqual(self.task.workload, (100, 0))
        self.assertEqual(self.task.task_dependency, [])

    def test_transport_task_movement(self):
        """ 運搬タスクの移動確認 """
        initial_coordinate = self.transport_task.coordinate
        self.transport_task.update()
        self.assertNotEqual(initial_coordinate, self.transport_task.coordinate)
        self.assertGreater(self.transport_task.workload[1], 0)

    def test_manufacture_task_update(self):
        """ 加工タスクの進捗更新確認 """
        initial_progress = self.manufacture_task.workload[1]
        self.manufacture_task.update()
        self.assertEqual(self.manufacture_task.workload[1], initial_progress + 1)

    def test_robot_coordinate_update(self):
        """ ロボットの座標更新確認 """
        new_coordinate = (5, 5)
        self.robot.update_coordinate(new_coordinate)
        self.assertEqual(self.robot.coordinate, new_coordinate)
        for module in self.robot.component:
            self.assertEqual(module.coordinate, new_coordinate)

if __name__ == "__main__":
    unittest.main()
