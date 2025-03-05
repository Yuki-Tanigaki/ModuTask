import unittest
from modutask.robotic_system.core import *

class TestRobotSystem(unittest.TestCase):
    def setUp(self):
        """テスト用の基本設定"""
        self.module_type = ModuleType(name="BatteryModule", max_battery=100.0)
        self.module = Module(type=self.module_type, name="ModuleA", coordinate=(0, 0))
        
        self.robot_type = RobotType(
            name="TransportRobot",
            required_modules={self.module_type: 1},
            performance={RobotPerformanceAttributes.MOBILITY: 5},
            redundancy={}
        )
        self.robot = Robot(type=self.robot_type, name="RobotA", coordinate=(0, 0), component=[self.module])

    def test_module_initialization(self):
        """モジュールの初期化をテスト"""
        self.assertEqual(self.module.battery, (100.0, 100.0))
        self.assertEqual(self.module.state, ModuleState.SPARE)

    def test_robot_coordinate_update(self):
        """ロボットの座標更新をテスト"""
        self.robot.update_coordinate((5, 5))
        self.assertEqual(self.robot.coordinate, (5, 5))
        self.assertEqual(self.robot.component[0].coordinate, (5, 5))

    def test_transport_task_update(self):
        """運搬タスクの更新をテスト"""
        task = Transport(
            name="MoveTask",
            coordinate=(0, 0),
            total_workload=10.0,
            completed_workload=0.0,
            task_dependency=[],
            required_performance={RobotPerformanceAttributes.MOBILITY: 1},
            deployed_robot=[self.robot],
            other_attrs={},
            origin_destination=((0, 0), (10, 0), 1.0)
        )
        
        task.update()
        self.assertGreater(task.completed_workload, 0)

    def test_manufacture_task_update(self):
        """加工タスクの更新をテスト"""
        task = Manufacture(
            name="BuildTask",
            coordinate=(1, 1),
            total_workload=5.0,
            completed_workload=0.0,
            task_dependency=[],
            required_performance={RobotPerformanceAttributes.MANUFACTURE: 1},
            deployed_robot=[self.robot],
            other_attrs={}
        )
        
        task.update()
        self.assertEqual(task.completed_workload, 1)

if __name__ == '__main__':
    unittest.main()
