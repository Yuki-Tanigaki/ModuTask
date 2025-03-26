import unittest
import numpy as np
from unittest.mock import MagicMock
from modutask.core.task.transport import Transport
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.robot.robot import Robot, RobotState

class TestTransportTask(unittest.TestCase):

    def setUp(self):
        self.name = "transport1"
        self.origin = (0.0, 0.0)
        self.destination = (3.0, 4.0)  # 距離 = 5.0
        self.coordinate = (0.0, 0.0)
        self.transportability = 2.0
        self.required_perf = {PerformanceAttributes.MOBILITY: 1.0}

    def create_mock_robot(self, mobility=2.0):
        robot_type = MagicMock()
        robot_type.performance = {PerformanceAttributes.MOBILITY: mobility}
        
        robot = MagicMock(spec=Robot)
        robot.state = RobotState.ACTIVE
        robot.type = robot_type
        robot.name = "TestRobot"
        robot.coordinate = (0.0, 0.0)
        def travel_mock(target):
            robot.coordinate = target
        robot.travel.side_effect = travel_mock
        
        return robot

    def test_initialization_success(self):
        t = Transport(
            name=self.name,
            coordinate=self.coordinate,
            required_performance=self.required_perf,
            origin_coordinate=self.origin,
            destination_coordinate=self.destination,
            transportability=self.transportability
        )
        self.assertAlmostEqual(t.total_workload, 10.0)
        self.assertEqual(t.completed_workload, 0.0)

    def test_invalid_transportability(self):
        with self.assertRaises(ValueError):
            Transport(
                name=self.name,
                coordinate=self.coordinate,
                required_performance=self.required_perf,
                origin_coordinate=self.origin,
                destination_coordinate=self.destination,
                transportability=0.5
            )

    def test_update_progress(self):
        t = Transport(
            name=self.name,
            coordinate=self.coordinate,
            required_performance=self.required_perf,
            origin_coordinate=self.origin,
            destination_coordinate=self.destination,
            transportability=self.transportability
        )
        robot = self.create_mock_robot(mobility=2.0)
        t._task_dependency = []  # 依存タスクなしとする
        t._assigned_robot = [robot]

        updated = t.update()
        self.assertTrue(updated)
        self.assertEqual(t.coordinate, (0.6, 0.8))
        self.assertEqual(t.completed_workload, 2.0)

    def test_update_fails_due_to_unsatisfied_performance(self):
        t = Transport(
            name=self.name,
            coordinate=self.coordinate,
            required_performance={PerformanceAttributes.MOBILITY: 10.0},  # 高すぎて満たせない
            origin_coordinate=self.origin,
            destination_coordinate=self.destination,
            transportability=self.transportability
        )
        robot = self.create_mock_robot(mobility=1.0)
        t._task_dependency = []
        t._assigned_robot = [robot]

        self.assertFalse(t.update())

    def test_update_fails_due_to_unfinished_dependency(self):
        t = Transport(
            name=self.name,
            coordinate=self.coordinate,
            required_performance=self.required_perf,
            origin_coordinate=self.origin,
            destination_coordinate=self.destination,
            transportability=self.transportability
        )
        robot = self.create_mock_robot()
        dependency = MagicMock()
        dependency.is_completed.return_value = False

        t._task_dependency = [dependency]
        t._assigned_robot = [robot]

        self.assertFalse(t.update())


if __name__ == '__main__':
    unittest.main()
