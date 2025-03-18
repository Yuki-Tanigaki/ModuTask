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

    def test_try_release_assign_robot(self):
        robot_type=RobotType(name='Worker', required_modules={}, performance={RobotPerformanceAttributes.MANUFACTURE: 2}, 
                             power_consumption=0)
        robot1 = Robot(robot_type=robot_type, name='Robo1', coordinate=(0, 0), component=[], task_priority=[])
        robot2 = Robot(robot_type=robot_type, name='Robo2', coordinate=(0, 0), component=[], task_priority=[])
        task = Manufacture(name='Welding1', coordinate=(0, 0), total_workload=10, completed_workload=5,
                            task_dependency=[], required_performance={RobotPerformanceAttributes.MANUFACTURE: 2})

        self.assertTrue(task.try_assign_robot(robot1))
        self.assertIn(robot1, task.assigned_robot)
        self.assertTrue(task.try_release_robot(robot1))
        self.assertFalse(task.try_release_robot(robot2))

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
        task.try_release_robot(weak_robot)
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
        import sys
        print(f"\n{self.transport_task.coordinate}")
        print(f"\n{self.destination_coordinate}")
        sys.stdout.flush()
        self.assertEqual(self.transport_task.coordinate, self.destination_coordinate)
        self.assertGreaterEqual(self.transport_task.completed_workload, self.transport_task.total_workload)

    def test_robot_movement(self):
        """ ロボットがタスクとともに移動するかテスト """
        initial_position = np.array(self.robot.coordinate)
        self.transport_task.update()
        updated_position = np.array(self.robot.coordinate)
        self.assertFalse(np.array_equal(initial_position, updated_position))
        self.assertTrue(np.array_equal(updated_position, np.array(self.transport_task.coordinate)))
    
    
    