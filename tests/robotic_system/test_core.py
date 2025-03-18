import unittest
from modutask.robotic_system.core import (
    Task, Transport, Manufacture, Module, Robot, 
    ModuleType, RobotType, ModuleState, RobotState, RobotPerformanceAttributes
)

class TestCore(unittest.TestCase):
    def setUp(self):
        """ テストのセットアップ """
        # モジュールタイプを作成
        self.module_type = ModuleType(name="BatteryModule", max_battery=100)

        # モジュールを作成
        self.module = Module(
            module_type=self.module_type,
            name="Battery1",
            coordinate=(0, 0),
            battery=50,
            state=ModuleState.FUNCTIONAL
        )

        # ロボットタイプを作成
        self.robot_type = RobotType(
            name="TransportRobot",
            required_modules={self.module_type: 1},
            performance={
                RobotPerformanceAttributes.MOBILITY: 10,
                RobotPerformanceAttributes.TRANSPORT: 5
            },
            power_consumption=20
        )

        # ロボットを作成
        self.robot = Robot(
            robot_type=self.robot_type,
            name="Robot1",
            coordinate=(0, 0),
            component=[self.module],
            state=RobotState.IDLE
        )

        # タスクを作成
        self.transport_task = Transport(
            name="TransportTask",
            coordinate=(0, 0),
            total_workload=100,
            completed_workload=0,
            task_dependency=[],
            required_performance={RobotPerformanceAttributes.MOBILITY: 5},
            assigned_robot=[self.robot],
            origin_coordinate=(0, 0),
            destination_coordinate=(10, 0),
            transportability=0.8
        )

        self.manufacture_task = Manufacture(
            name="ManufactureTask",
            coordinate=(0, 0),
            total_workload=50,
            completed_workload=0,
            task_dependency=[],
            required_performance={RobotPerformanceAttributes.MANUFACTURE: 3},
            assigned_robots=[self.robot]
        )

    def test_module_initialization(self):
        """ Module クラスの初期化をテスト """
        self.assertEqual(self.module.name, "Battery1")
        self.assertEqual(self.module.battery, 50)
        self.assertEqual(self.module.state, ModuleState.FUNCTIONAL)

    def test_robot_initialization(self):
        """ Robot クラスの初期化をテスト """
        self.assertEqual(self.robot.name, "Robot1")
        self.assertEqual(self.robot.coordinate, (0, 0))
        self.assertEqual(len(self.robot.component), 1)
        self.assertEqual(self.robot.state, RobotState.IDLE)

    def test_transport_task_update(self):
        """ Transport クラスの update メソッドをテスト """
        self.assertEqual(self.transport_task.completed_workload, 0)
        self.transport_task.update()
        self.assertGreater(self.transport_task.completed_workload, 0)

    def test_manufacture_task_update(self):
        """ Manufacture クラスの update メソッドをテスト """
        self.assertEqual(self.manufacture_task.completed_workload, 0.0)
        self.manufacture_task.update()
        self.assertEqual(self.manufacture_task.completed_workload, 1.0)

    def test_robot_assign_module(self):
        """ Robot クラスの try_assign_module メソッドをテスト """
        new_module = Module(
            module_type=self.module_type,
            name="Battery2",
            coordinate=(0, 0),
            battery=80,
            state=ModuleState.FUNCTIONAL
        )
        result = self.robot.try_assign_module(new_module)
        self.assertTrue(result)
        self.assertIn(new_module, self.robot.component)

    def test_robot_malfunction(self):
        """ Robot クラスの malfunction メソッドをテスト """
        self.robot.malfunction(self.module)
        self.assertNotIn(self.module, self.robot.component)
        self.assertEqual(self.module.state, ModuleState.MALFUNCTION)

    def test_robot_update_state(self):
        """ Robot クラスの update_state メソッドをテスト """
        self.robot.update_state(RobotState.WORK)
        self.assertEqual(self.robot.state, RobotState.WORK)

    def test_module_update_battery(self):
        """ Module クラスの update_battery メソッドをテスト """
        self.module.update_battery(-10)
        self.assertEqual(self.module.battery, 40)
        self.module.update_battery(20)
        self.assertEqual(self.module.battery, 60)

    def test_module_update_state(self):
        """ Module クラスの update_state メソッドをテスト """
        self.module.update_state(ModuleState.MALFUNCTION)
        self.assertEqual(self.module.state, ModuleState.MALFUNCTION)

    def test_robot_update_coordinate(self):
        """ Robot クラスの update_coordinate メソッドをテスト """
        new_coordinate = (10, 10)
        self.robot.update_coordinate(new_coordinate)
        self.assertEqual(self.robot.coordinate, new_coordinate)
        for module in self.robot.component:
            self.assertEqual(module.coordinate, new_coordinate)

if __name__ == "__main__":
    unittest.main()