import unittest
from enum import Enum
import numpy as np
from typing import Dict
from modutask.robotic_system.core import *

class TestModuleType(unittest.TestCase):
    def test_hash_and_equality(self):
        type1 = ModuleType(name='Battery', max_battery=100)
        type2 = ModuleType(name='Battery', max_battery=100)
        type3 = ModuleType(name='Sensor', max_battery=50)
        self.assertEqual(hash(type1), hash(type2))
        self.assertNotEqual(hash(type1), hash(type3))
        self.assertEqual(type1, type2)
        self.assertNotEqual(type1, type3)

class TestRobotType(unittest.TestCase):
    def test_hash_and_equality(self):
        type1 = RobotType(name='Worker', required_modules={}, performance={}, power_consumption=10.0)
        type2 = RobotType(name='Worker', required_modules={}, performance={}, power_consumption=10.0)
        type3 = RobotType(name='Explorer', required_modules={}, performance={}, power_consumption=5.0)
        self.assertEqual(hash(type1), hash(type2))
        self.assertNotEqual(hash(type1), hash(type3))
        self.assertEqual(type1, type2)
        self.assertNotEqual(type1, type3)

class TestTask(unittest.TestCase):
    def setUp(self):
        pass

    def test_check_dependencies_completed(self):
        finished_task = Manufacture(name='Welding1', coordinate=(0, 0), total_workload=10, completed_workload=10, 
                                    task_dependency=[], required_performance={RobotPerformanceAttributes.MANUFACTURE: 2})
        ongoing_task = Manufacture(name='Welding2', coordinate=(0, 0), total_workload=10, completed_workload=5, 
                                    task_dependency=[], required_performance={RobotPerformanceAttributes.MANUFACTURE: 2})
        following_task1 = Manufacture(name='Assembling1', coordinate=(1, 1), total_workload=10, completed_workload=0, 
                                    task_dependency=[finished_task], required_performance={RobotPerformanceAttributes.MANUFACTURE: 2})
        following_task2 = Manufacture(name='Assembling2', coordinate=(1, 1), total_workload=10, completed_workload=0, 
                                    task_dependency=[ongoing_task], required_performance={RobotPerformanceAttributes.MANUFACTURE: 2})
        self.assertTrue(following_task1.check_dependencies_completed())
        self.assertFalse(following_task2.check_dependencies_completed())

    def test_check_assigned_performance(self):
        weak_robot_type=RobotType(name='Worker1', required_modules={}, performance={RobotPerformanceAttributes.MANUFACTURE: 1}, 
                                  power_consumption=0)
        good_robot_type=RobotType(name='Worker2', required_modules={}, performance={RobotPerformanceAttributes.MANUFACTURE: 2}, 
                                  power_consumption=0)
        weak_robot = Robot(robot_type=weak_robot_type, name='Robo1', coordinate=(0, 0), component=[], task_priority=[])
        good_robot = Robot(robot_type=good_robot_type, name='Robo2', coordinate=(0, 0), component=[], task_priority=[])
        task = Manufacture(name='Welding1', coordinate=(0, 0), total_workload=10, completed_workload=5,
                            task_dependency=[], required_performance={RobotPerformanceAttributes.MANUFACTURE: 2})
        task.try_assign_robot(weak_robot)
        self.assertFalse(task.check_assigned_performance())
        task.release_robot()
        task.try_assign_robot(good_robot)
        self.assertTrue(task.check_assigned_performance())

class TestTransport(unittest.TestCase):
    def setUp(self):
        """ テスト用の初期設定 """
        self.task_dependency = []  # 依存タスクなし
        self.required_performance = {RobotPerformanceAttributes.MOBILITY: 5}
        self.origin_coordinate = (0.0, 0.0)
        self.destination_coordinate = (10.0, 0.0)
        self.transportability = 0.8

        # ロボットタイプの設定
        self.robot_type = RobotType(
            name="TestBot",
            required_modules={},
            performance={RobotPerformanceAttributes.MOBILITY: 6},
            power_consumption=10.0
        )

        # モジュールの設定
        self.module_type = ModuleType(name="BatteryModule", max_battery=100)
        self.module = Module(module_type=self.module_type, name="Battery1", coordinate=(0.0, 0.0), battery=50)

        # ロボットの設定
        self.robot = Robot(
            robot_type=self.robot_type,
            name="TestRobot",
            coordinate=(0.0, 0.0),
            component=[self.module],
            task_priority=[]
        )

        # Transportタスクの設定
        self.transport_task = Transport(
            name="TransportTask1",
            coordinate=self.origin_coordinate,
            total_workload=10.0,
            completed_workload=0.0,
            task_dependency=self.task_dependency,
            required_performance=self.required_performance,
            origin_coordinate=self.origin_coordinate,
            destination_coordinate=self.destination_coordinate,
            transportability=self.transportability
        )
        self.transport_task.try_assign_robot(self.robot)

    def test_initial_conditions(self):
        """ 初期状態のテスト """
        self.assertEqual(self.transport_task.coordinate, self.origin_coordinate)
        self.assertEqual(self.transport_task.completed_workload, 0.0)
        self.assertIn(self.robot, self.transport_task.assigned_robot)

    def test_task_progression(self):
        """ タスクの進行が正しく処理されるかテスト """
        distance_traveled = self.transport_task.update()
        self.assertGreater(distance_traveled, 0.0)
        self.assertGreater(self.transport_task.completed_workload, 0.0)
        self.assertNotEqual(self.transport_task.coordinate, self.origin_coordinate)

    def test_task_completion(self):
        """ タスクが完了するかテスト """
        while self.transport_task.completed_workload < self.transport_task.total_workload:
            self.transport_task.update()
        self.assertEqual(self.transport_task.coordinate, self.destination_coordinate)
        self.assertGreaterEqual(self.transport_task.completed_workload, self.transport_task.total_workload)

    def test_robot_movement(self):
        """ ロボットがタスクとともに移動するかテスト """
        initial_position = np.array(self.robot.coordinate)
        self.transport_task.update()
        updated_position = np.array(self.robot.coordinate)
        self.assertFalse(np.array_equal(initial_position, updated_position))
        self.assertTrue(np.array_equal(updated_position, np.array(self.transport_task.coordinate)))
    
class TestManufacture(unittest.TestCase):
    def setUp(self):
        """ テスト用の初期設定 """
        self.task_dependency = []  # 依存タスクなし
        self.required_performance = {
            RobotPerformanceAttributes.MOBILITY: 5,
            RobotPerformanceAttributes.MANUFACTURE: 3  # 加工性能を要求
        }
        self.total_workload = 10.0
        self.completed_workload = 0.0
        
        # Manufactureタスクの設定
        self.manufacture_task = Manufacture(
            name="ManufactureTask1",
            coordinate=(0.0, 0.0),
            total_workload=self.total_workload,
            completed_workload=self.completed_workload,
            task_dependency=self.task_dependency,
            required_performance=self.required_performance
        )

        # モジュールの設定
        self.module_type = ModuleType(name="BatteryModule", max_battery=100)
        self.module = Module(module_type=self.module_type, name="Battery1", coordinate=(0.0, 0.0), battery=50)
        
        # ロボットタイプの設定
        self.robot_type = RobotType(
            name="TestBot",
            required_modules={self.module_type: 1},
            performance={
                RobotPerformanceAttributes.MOBILITY: 6,     # 移動性能
                RobotPerformanceAttributes.MANUFACTURE: 4   # 加工性能
            },
            power_consumption=1.0
        )
        
        # ロボットの設定
        self.robot = Robot(
            robot_type=self.robot_type,
            name="TestRobot",
            coordinate=(0.0, 0.0),
            component=[self.module],
            task_priority=[]
        )

    def test_initial_conditions(self):
        """ 初期状態のテスト """
        self.assertEqual(self.manufacture_task.completed_workload, 0.0)
        self.assertEqual(self.manufacture_task.total_workload, self.total_workload)

    def test_task_progression(self):
        """ タスクの進行が正しく処理されるかテスト """
        # 割り当てられていない状態では進捗は更新されないことを確認
        distance_traveled = self.manufacture_task.update()
        self.assertEqual(distance_traveled, 0.0)
        self.assertEqual(self.manufacture_task.completed_workload, 0.0)

        # ロボットをタスクに割り当てる
        self.manufacture_task.try_assign_robot(self.robot)  # ロボットを割り当てる

        # 実行可能な状態にした後の進捗更新をテスト
        self.manufacture_task.check_assigned_performance = lambda: True  # 擬似的に条件を満たす
        self.manufacture_task.check_dependencies_completed = lambda: True  # 擬似的に依存条件を満たす
        
        # 更新後の状態を確認
        distance_traveled = self.manufacture_task.update()
        self.assertEqual(distance_traveled, 1.0)
        self.assertEqual(self.manufacture_task.completed_workload, 1.0)

    def test_task_completion(self):
        """ タスクが完了するかテスト """
        # タスクの進捗を更新して完了させる
        self.manufacture_task.try_assign_robot(self.robot)  # ロボットを割り当てる
        self.manufacture_task.check_assigned_performance = lambda: True  # 条件を満たす
        self.manufacture_task.check_dependencies_completed = lambda: True  # 依存条件を満たす
        
        for _ in range(int(self.total_workload)):
            self.manufacture_task.update()

        self.assertEqual(self.manufacture_task.completed_workload, self.total_workload)

class TestModule(unittest.TestCase):
    def setUp(self):
        """ 各テストの前に共通のオブジェクトを作成 """
        self.module_type = ModuleType(name="BatteryModule", max_battery=100)
        self.module = Module(module_type=self.module_type, name="Mod1", coordinate=(0.0, 0.0), battery=50.0)

    def test_initialization(self):
        """ 正しく初期化されることを確認 """
        self.assertEqual(self.module.type, self.module_type)
        self.assertEqual(self.module.name, "Mod1")
        self.assertEqual(self.module.coordinate, (0.0, 0.0))
        self.assertEqual(self.module.battery, 50.0)
        self.assertEqual(self.module.state, ModuleState.ACTIVE)

        # バッテリーが上限を超えた場合にエラーが発生するか
        with self.assertRaises(ValueError):
            Module(self.module_type, "Mod2", (0, 0), 120.0)  # max_battery=100 を超える

    def test_update_coordinate(self):
        """ 座標更新のテスト """
        self.module.update_coordinate((10.0, 15.0))
        self.assertEqual(self.module.coordinate, (10.0, 15.0))

        self.module.update_coordinate([20.5, 30.5])
        self.assertEqual(self.module.coordinate, (20.5, 30.5))

        self.module.update_coordinate(np.array([5.5, 7.5]))
        self.assertEqual(self.module.coordinate, (5.5, 7.5))

        # 無効な座標データを渡した場合にエラーが発生するか
        with self.assertRaises(TypeError):
            self.module.update_coordinate(np.array([[1.0, 2.0], [3.0, 4.0]]))  # 2次元配列

        with self.assertRaises(TypeError):
            self.module.update_coordinate([1.0])  # 長さが2でないリスト

    def test_update_battery(self):
        """ バッテリー更新のテスト """
        self.module.update_battery(20.0)
        self.assertEqual(self.module.battery, 70.0)

        self.module.update_battery(-30.0)
        self.assertEqual(self.module.battery, 40.0)

        self.module.update_battery(100.0)  # 上限超え -> max_battery に制限
        self.assertEqual(self.module.battery, 100.0)

        self.module.update_battery(-150.0)  # 最小値0に制限
        self.assertEqual(self.module.battery, 0.0)

        # 故障モジュールのバッテリー更新は禁止されている
        self.module.update_state(ModuleState.ERROR)
        with self.assertRaises(ValueError):
            self.module.update_battery(10.0)

    def test_update_state(self):
        """ モジュール状態の更新 """
        self.module.update_state(ModuleState.ERROR)
        self.assertEqual(self.module.state, ModuleState.ERROR)

        self.module.update_state(ModuleState.ACTIVE)
        self.assertEqual(self.module.state, ModuleState.ACTIVE)

    def test_str_repr(self):
        """ 文字列表現のテスト """
        expected_str = f"Module(Mod1, ACTIVE, Battery: {self.module.battery}/{self.module.type.max_battery})"
        self.assertEqual(str(self.module), expected_str)

        expected_repr = f"Module(name=Mod1, type=BatteryModule, state=ACTIVE, battery=50.0)"
        self.assertEqual(repr(self.module), expected_repr)

class TestRobot(unittest.TestCase):
    def setUp(self):
        """ テスト用の初期設定 """
        self.robot_type = RobotType(
            name="TestBot",
            required_modules={},
            performance={RobotPerformanceAttributes.MOBILITY: 6},
            power_consumption=10.0
        )

        self.module_type = ModuleType(name="BatteryModule", max_battery=100)
        self.module = Module(module_type=self.module_type, name="Battery1", coordinate=(0.0, 0.0), battery=50)

        self.robot = Robot(
            robot_type=self.robot_type,
            name="TestRobot",
            coordinate=(0.0, 0.0),
            component=[self.module],
            task_priority=[]
        )

    def test_initial_conditions(self):
        """ 初期状態のテスト """
        self.assertEqual(self.robot.coordinate, (0.0, 0.0))
        self.assertEqual(self.robot.state, RobotState.ACTIVE)
        self.assertIn(self.module, self.robot.component)

    def test_update_coordinate(self):
        """ 座標の更新が正しく処理されるかテスト """
        new_coordinate = (5.0, 5.0)
        self.robot.update_coordinate(new_coordinate)
        self.assertEqual(self.robot.coordinate, new_coordinate)
        for module in self.robot.component:
            self.assertEqual(module.coordinate, new_coordinate)

    def test_try_assign_module(self):
        """ モジュールの搭載が正しく処理されるかテスト """
        new_module = Module(module_type=self.module_type, name="Battery2", coordinate=(0.0, 0.0), battery=50)
        result = self.robot.try_assign_module(new_module)
        self.assertTrue(result)
        self.assertIn(new_module, self.robot.component)

    def test_malfunction(self):
        """ モジュールの故障が正しく処理されるかテスト """
        self.robot.malfunction(self.module)
        self.assertNotIn(self.module, self.robot.component)
        self.assertEqual(self.module.state, ModuleState.ERROR)

    def test_update_state(self):
        """ ロボットの状態更新が正しく処理されるかテスト """
        self.robot.update_state()
        self.assertEqual(self.robot.state, RobotState.ACTIVE)

    def test_update_task_priority(self):
        """ タスクの優先順位リストの更新が正しく処理されるかテスト """
        task = Transport(
            name="TestTask", 
            coordinate=(0.0, 0.0), 
            total_workload=10.0,
            completed_workload=0.0, 
            task_dependency=[], 
            required_performance={}, 
            origin_coordinate=(0.0, 0.0),
            destination_coordinate=(10.0, 0.0), 
            transportability=0.8)
    