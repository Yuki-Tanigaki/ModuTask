import unittest
import numpy as np
from unittest.mock import MagicMock
from modutask.core.task.manufacture import Manufacture
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.robot.robot import Robot, RobotState

class TestManufactureTask(unittest.TestCase):

    def setUp(self):
        self.name = "manufacture1"
        self.coordinate = (0.0, 0.0)
        self.total_workload=10.0
        self.completed_workload=5.0
        self.required_perf = {PerformanceAttributes.MOBILITY: 1.0}

    def create_mock_robot(self, mobility=2.0, battery_power=10.0, coordinate=None):
        robot_type = MagicMock()
        robot_type.performance = {PerformanceAttributes.MOBILITY: mobility}
        
        robot = MagicMock(spec=Robot)
        robot.coordinate = coordinate
        robot.state = RobotState.ACTIVE
        robot.type = robot_type
        robot.name = "TestRobot"
        robot.update_coordinate = MagicMock()
        robot.draw_battery_power = MagicMock()
        return robot

    def test_initialization_success(self):
        t = Manufacture(
            name=self.name,
            coordinate=self.coordinate,
            total_workload=self.total_workload,
            completed_workload=self.completed_workload,
            required_performance=self.required_perf
        )
        self.assertAlmostEqual(t.total_workload, 10.0)
        self.assertEqual(t.completed_workload, 5.0)

    def test_update_progress(self):
        t = Manufacture(
            name=self.name,
            coordinate=self.coordinate,
            required_performance=self.required_perf,
            total_workload=self.total_workload,
            completed_workload=self.completed_workload
        )
        robot = self.create_mock_robot(mobility=2.0)
        t.set_task_dependency([])  # 依存タスクなしとする
        t._assigned_robot = [robot]

        updated = t.update()
        self.assertTrue(updated)
        self.assertGreater(t.completed_workload, 5.0)

    def test_update_fails_due_to_unsatisfied_performance(self):
        t = Manufacture(
            name=self.name,
            coordinate=self.coordinate,
            total_workload=self.total_workload,
            completed_workload=self.completed_workload,
            required_performance={PerformanceAttributes.MOBILITY: 10.0}  # 高すぎて満たせない
        )
        robot = self.create_mock_robot(mobility=1.0)
        t.set_task_dependency([])  
        t._assigned_robot = [robot]

        self.assertFalse(t.update())

    def test_update_fails_due_to_unfinished_dependency(self):
        t = Manufacture(
            name=self.name,
            coordinate=self.coordinate,
            required_performance=self.required_perf,
            total_workload=self.total_workload,
            completed_workload=self.completed_workload
        )
        robot = self.create_mock_robot()
        dependency = MagicMock()
        dependency.is_completed.return_value = False

        t.set_task_dependency([dependency])
        t._assigned_robot = [robot]

        self.assertFalse(t.update())


if __name__ == '__main__':
    unittest.main()
