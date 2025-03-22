import unittest
from unittest.mock import MagicMock
from modutask.robotic_system import *
from modutask.robotic_system.utils import make_coodinate_to_tuple

class DummyRobot:
    def __init__(self, coord, state, performance):
        self.name = MagicMock()
        self.coordinate = make_coodinate_to_tuple(coord)
        self.state = state
        self.type = MagicMock()
        self.type.performance = performance
        self.update_coordinate = MagicMock()
        self.draw_battery_power = MagicMock()
        self.charge_battery_power = MagicMock()

class TestTask(unittest.TestCase):

    def test_are_dependencies_completed(self):
        """
        依存タスクが完了しているかを判断
        依存タスクが終了済み: True
        依存タスクが未完了: False
        """
        finished_task = Manufacture(name='Welding1', coordinate=(0, 0), total_workload=10, completed_workload=10, 
                                    task_dependency=[], required_performance={PerformanceAttributes.MANUFACTURE: 2})
        ongoing_task = Manufacture(name='Welding2', coordinate=(0, 0), total_workload=10, completed_workload=5, 
                                    task_dependency=[], required_performance={PerformanceAttributes.MANUFACTURE: 2})
        following_task_finished = Manufacture(name='Assembling1', coordinate=(1, 1), total_workload=10, completed_workload=0, 
                                    task_dependency=[finished_task], required_performance={PerformanceAttributes.MANUFACTURE: 2})
        following_task_ongoing = Manufacture(name='Assembling2', coordinate=(1, 1), total_workload=10, completed_workload=0, 
                                    task_dependency=[ongoing_task], required_performance={PerformanceAttributes.MANUFACTURE: 2})
        self.assertTrue(following_task_finished.are_dependencies_completed())
        self.assertFalse(following_task_ongoing.are_dependencies_completed())

    def test_is_performance_satisfied(self):
        """
        割り当てられたロボットの能力が十分かどうかチェック
        パフォーマンスが足りないとき: False
        パフォーマンスが足りているとき: True
        座標, 状態が一致しないとき: 例外
        """
        task = Manufacture(
            name="Establishment",
            coordinate=(0.0, 0.0),
            total_workload=10.0,
            completed_workload=0.0,
            task_dependency=[],
            required_performance={PerformanceAttributes.MANUFACTURE: 5}
        )
        weak_robot = DummyRobot((0.0, 0.0), RobotState.ACTIVE, {PerformanceAttributes.MANUFACTURE: 3})
        good_robot = DummyRobot((0.0, 0.0), RobotState.ACTIVE, {PerformanceAttributes.MANUFACTURE: 10})

        task.assign_robot(weak_robot)
        self.assertFalse(task.is_performance_satisfied())
        task.release_robot()
        task.assign_robot(good_robot)
        self.assertTrue(task.is_performance_satisfied())
    
    def test_assigned_robot(self):
        """
        割り当てられたロボットの能力が十分かどうかチェック
        パフォーマンスが足りないとき: False
        パフォーマンスが足りているとき: True
        座標, 状態が一致しないとき: 例外
        """
        task = Manufacture(
            name="Establishment",
            coordinate=(0.0, 0.0),
            total_workload=10.0,
            completed_workload=0.0,
            task_dependency=[],
            required_performance={PerformanceAttributes.MANUFACTURE: 5}
        )
        failure_robot = DummyRobot((1.0, 0.0), RobotState.DEFECTIVE, {PerformanceAttributes.MANUFACTURE: 10})
        stray_robot = DummyRobot((1.0, 0.0), RobotState.ACTIVE, {PerformanceAttributes.MANUFACTURE: 10})

        with self.assertRaises(RuntimeError):
            task.assign_robot(failure_robot)
        with self.assertRaises(RuntimeError):
            task.assign_robot(stray_robot)
    
    def test_release_robot(self):
        # タスク作成
        task = Manufacture(
            name="Establishment",
            coordinate=(0.0, 0.0),
            total_workload=10.0,
            completed_workload=0.0,
            task_dependency=[],
            required_performance={PerformanceAttributes.MANUFACTURE: 5}
        )

        # ロボット割り当て
        robot = DummyRobot((0.0, 0.0), RobotState.ACTIVE, {PerformanceAttributes.MANUFACTURE: 2})
        task.assign_robot(robot)

        # 確認：1体割り当てられている
        self.assertEqual(len(task.assigned_robot), 1)

        # release_robot() を呼ぶ
        task.release_robot()

        # 確認：空になっていること
        self.assertEqual(task.assigned_robot, [])

    def test_manufacture_update(self):
        task = Manufacture(
            name="加工1",
            coordinate=(0.0, 0.0),
            total_workload=10.0,
            completed_workload=0.0,
            task_dependency=[],
            required_performance={PerformanceAttributes.MANUFACTURE: 5}
        )
        robot = DummyRobot((0.0, 0.0), RobotState.ACTIVE, {PerformanceAttributes.MANUFACTURE: 10})
        robot.state = MagicMock()
        robot.state.name = "ACTIVE"
        task.assign_robot(robot)
        self.assertTrue(task.update())
        self.assertEqual(task.completed_workload, 1.0)

    def test_transport_init(self):
        task = Transport(
            name="運搬1",
            coordinate=(0.0, 0.0),
            task_dependency=[],
            required_performance={PerformanceAttributes.TRANSPORT: 3},
            origin_coordinate=(0.0, 0.0),
            destination_coordinate=(3.0, 4.0),
            transportability=1.0,
            total_workload=None,
            completed_workload=None
        )
        self.assertAlmostEqual(task.total_workload, 5.0)

    def test_charge_update(self):
        task = Charge(
            name="充電1",
            coordinate=(1.0, 1.0),
            charging_speed=2.0
        )
        robot = DummyRobot((1.0, 1.0), RobotState.ACTIVE, {})
        task.assign_robot(robot)
        task.update()
        robot.charge_battery_power.assert_called_with(2.0)

if __name__ == '__main__':
    unittest.main()


# import unittest
# import numpy as np

# from modutask.robotic_system import *


# class TestTask(unittest.TestCase):
#     def setUp(self):
#         pass

#     def test_are_dependencies_completed(self):
#         finished_task = Manufacture(name='Welding1', coordinate=(0, 0), total_workload=10, completed_workload=10, 
#                                     task_dependency=[], required_performance={PerformanceAttributes.MANUFACTURE: 2})
#         ongoing_task = Manufacture(name='Welding2', coordinate=(0, 0), total_workload=10, completed_workload=5, 
#                                     task_dependency=[], required_performance={PerformanceAttributes.MANUFACTURE: 2})
#         following_task1 = Manufacture(name='Assembling1', coordinate=(1, 1), total_workload=10, completed_workload=0, 
#                                     task_dependency=[finished_task], required_performance={PerformanceAttributes.MANUFACTURE: 2})
#         following_task2 = Manufacture(name='Assembling2', coordinate=(1, 1), total_workload=10, completed_workload=0, 
#                                     task_dependency=[ongoing_task], required_performance={PerformanceAttributes.MANUFACTURE: 2})
#         self.assertTrue(following_task1.are_dependencies_completed())
#         self.assertFalse(following_task2.are_dependencies_completed())

#     def test_check_assigned_performance(self):
#         weak_robot_type=RobotType(name='Worker1', required_modules={}, performance={PerformanceAttributes.MANUFACTURE: 1}, 
#                                   power_consumption=0)
#         good_robot_type=RobotType(name='Worker2', required_modules={}, performance={PerformanceAttributes.MANUFACTURE: 2}, 
#                                   power_consumption=0)
#         weak_robot = Robot(robot_type=weak_robot_type, name='Robo1', coordinate=(0, 0), component=[], task_priority=[])
#         good_robot = Robot(robot_type=good_robot_type, name='Robo2', coordinate=(0, 0), component=[], task_priority=[])
#         task = Manufacture(name='Welding1', coordinate=(0, 0), total_workload=10, completed_workload=5,
#                             task_dependency=[], required_performance={PerformanceAttributes.MANUFACTURE: 2})
#         task.try_assign_robot(weak_robot)
#         self.assertFalse(task.check_assigned_performance())
#         task.release_robot()
#         task.try_assign_robot(good_robot)
#         self.assertTrue(task.check_assigned_performance())

# class TestTransport(unittest.TestCase):
#     def setUp(self):
#         """ テスト用の初期設定 """
#         self.task_dependency = []  # 依存タスクなし
#         self.required_performance = {PerformanceAttributes.MOBILITY: 5}
#         self.origin_coordinate = (0.0, 0.0)
#         self.destination_coordinate = (10.0, 0.0)
#         self.transportability = 0.8

#         # ロボットタイプの設定
#         self.robot_type = RobotType(
#             name="TestBot",
#             required_modules={},
#             performance={PerformanceAttributes.MOBILITY: 6},
#             power_consumption=10.0
#         )

#         # モジュールの設定
#         self.module_type = ModuleType(name="BatteryModule", max_battery=100)
#         self.module = Module(module_type=self.module_type, name="Battery1", coordinate=(0.0, 0.0), battery=50)

#         # ロボットの設定
#         self.robot = Robot(
#             robot_type=self.robot_type,
#             name="TestRobot",
#             coordinate=(0.0, 0.0),
#             component=[self.module],
#             task_priority=[]
#         )

#         # Transportタスクの設定
#         self.transport_task = Transport(
#             name="TransportTask1",
#             coordinate=self.origin_coordinate,
#             total_workload=10.0,
#             completed_workload=0.0,
#             task_dependency=self.task_dependency,
#             required_performance=self.required_performance,
#             origin_coordinate=self.origin_coordinate,
#             destination_coordinate=self.destination_coordinate,
#             transportability=self.transportability
#         )
#         self.transport_task.try_assign_robot(self.robot)

#     def test_initial_conditions(self):
#         """ 初期状態のテスト """
#         self.assertEqual(self.transport_task.coordinate, self.origin_coordinate)
#         self.assertEqual(self.transport_task.completed_workload, 0.0)
#         self.assertIn(self.robot, self.transport_task.assigned_robot)

#     def test_task_progression(self):
#         """ タスクの進行が正しく処理されるかテスト """
#         distance_traveled = self.transport_task.update()
#         self.assertGreater(distance_traveled, 0.0)
#         self.assertGreater(self.transport_task.completed_workload, 0.0)
#         self.assertNotEqual(self.transport_task.coordinate, self.origin_coordinate)

#     def test_task_completion(self):
#         """ タスクが完了するかテスト """
#         while self.transport_task.completed_workload < self.transport_task.total_workload:
#             self.transport_task.update()
#         self.assertEqual(self.transport_task.coordinate, self.destination_coordinate)
#         self.assertGreaterEqual(self.transport_task.completed_workload, self.transport_task.total_workload)

#     def test_robot_movement(self):
#         """ ロボットがタスクとともに移動するかテスト """
#         initial_position = np.array(self.robot.coordinate)
#         self.transport_task.update()
#         updated_position = np.array(self.robot.coordinate)
#         self.assertFalse(np.array_equal(initial_position, updated_position))
#         self.assertTrue(np.array_equal(updated_position, np.array(self.transport_task.coordinate)))
    
# class TestManufacture(unittest.TestCase):
#     def setUp(self):
#         """ テスト用の初期設定 """
#         self.task_dependency = []  # 依存タスクなし
#         self.required_performance = {
#             PerformanceAttributes.MOBILITY: 5,
#             PerformanceAttributes.MANUFACTURE: 3  # 加工性能を要求
#         }
#         self.total_workload = 10.0
#         self.completed_workload = 0.0
        
#         # Manufactureタスクの設定
#         self.manufacture_task = Manufacture(
#             name="ManufactureTask1",
#             coordinate=(0.0, 0.0),
#             total_workload=self.total_workload,
#             completed_workload=self.completed_workload,
#             task_dependency=self.task_dependency,
#             required_performance=self.required_performance
#         )

#         # モジュールの設定
#         self.module_type = ModuleType(name="BatteryModule", max_battery=100)
#         self.module = Module(module_type=self.module_type, name="Battery1", coordinate=(0.0, 0.0), battery=50)
        
#         # ロボットタイプの設定
#         self.robot_type = RobotType(
#             name="TestBot",
#             required_modules={self.module_type: 1},
#             performance={
#                 PerformanceAttributes.MOBILITY: 6,     # 移動性能
#                 PerformanceAttributes.MANUFACTURE: 4   # 加工性能
#             },
#             power_consumption=1.0
#         )
        
#         # ロボットの設定
#         self.robot = Robot(
#             robot_type=self.robot_type,
#             name="TestRobot",
#             coordinate=(0.0, 0.0),
#             component=[self.module],
#             task_priority=[]
#         )

#     def test_initial_conditions(self):
#         """ 初期状態のテスト """
#         self.assertEqual(self.manufacture_task.completed_workload, 0.0)
#         self.assertEqual(self.manufacture_task.total_workload, self.total_workload)

#     def test_task_progression(self):
#         """ タスクの進行が正しく処理されるかテスト """
#         # 割り当てられていない状態では進捗は更新されないことを確認
#         distance_traveled = self.manufacture_task.update()
#         self.assertEqual(distance_traveled, 0.0)
#         self.assertEqual(self.manufacture_task.completed_workload, 0.0)

#         # ロボットをタスクに割り当てる
#         self.manufacture_task.try_assign_robot(self.robot)  # ロボットを割り当てる

#         # 実行可能な状態にした後の進捗更新をテスト
#         self.manufacture_task.check_assigned_performance = lambda: True  # 擬似的に条件を満たす
#         self.manufacture_task.are_dependencies_completed = lambda: True  # 擬似的に依存条件を満たす
        
#         # 更新後の状態を確認
#         distance_traveled = self.manufacture_task.update()
#         self.assertEqual(distance_traveled, 1.0)
#         self.assertEqual(self.manufacture_task.completed_workload, 1.0)

#     def test_task_completion(self):
#         """ タスクが完了するかテスト """
#         # タスクの進捗を更新して完了させる
#         self.manufacture_task.try_assign_robot(self.robot)  # ロボットを割り当てる
#         self.manufacture_task.check_assigned_performance = lambda: True  # 条件を満たす
#         self.manufacture_task.are_dependencies_completed = lambda: True  # 依存条件を満たす
        
#         for _ in range(int(self.total_workload)):
#             self.manufacture_task.update()

#         self.assertEqual(self.manufacture_task.completed_workload, self.total_workload)