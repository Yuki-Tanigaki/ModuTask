import unittest
from unittest.mock import MagicMock
from modutask.robotic_system import *

class DummyRobotType:
    def __init__(self, performance):
        self.performance = performance

class DummyRobot:
    def __init__(self, coordinate, performance, state="ACTIVE"):
        self.type = DummyRobotType(performance)
        self.name = MagicMock()
        self._coordinate = coordinate
        self.state = state
        self.draw_battery_power = MagicMock()

    @property
    def coordinate(self):
        return self._coordinate

class TestManufactureTask(unittest.TestCase):

    def test_manufacture_update_success(self):
        task = Manufacture(
            name="M1",
            coordinate=(1, 2),
            total_workload=5.0,
            completed_workload=0.0,
            task_dependency=[],
            required_performance={PerformanceAttributes.MANUFACTURE: 2}
        )
        robot = DummyRobot(
            coordinate=(1, 2),
            performance={PerformanceAttributes.MANUFACTURE: 2}
        )
        task.assign_robot(robot)
        updated = task.update()
        self.assertTrue(updated)
        self.assertEqual(task.completed_workload, 1.0)
        robot.draw_battery_power.assert_called_once()

    def test_insufficient_performance(self):
        task = Manufacture(
            name="M2",
            coordinate=(0, 0),
            total_workload=3.0,
            completed_workload=0.0,
            task_dependency=[],
            required_performance={PerformanceAttributes.MANUFACTURE: 3}
        )
        robot = DummyRobot(
            coordinate=(0, 0),
            performance={PerformanceAttributes.MANUFACTURE: 1}
        )
        task.assign_robot(robot)
        updated = task.update()
        self.assertFalse(updated)
        self.assertEqual(task.completed_workload, 0.0)

    def test_dependency_incomplete(self):
        mock_dep = MagicMock()
        mock_dep.total_workload = 2.0
        mock_dep.completed_workload = 1.0  # 未完了
        task = Manufacture(
            name="M3",
            coordinate=(0, 0),
            total_workload=3.0,
            completed_workload=0.0,
            task_dependency=[mock_dep],
            required_performance={PerformanceAttributes.MANUFACTURE: 1}
        )
        robot = DummyRobot(
            coordinate=(0, 0),
            performance={PerformanceAttributes.MANUFACTURE: 1}
        )
        task.assign_robot(robot)
        updated = task.update()
        self.assertFalse(updated)

    def test_multiple_updates_to_completion(self):
        task = Manufacture(
            name="M4",
            coordinate=(2, 2),
            total_workload=3.0,
            completed_workload=0.0,
            task_dependency=[],
            required_performance={PerformanceAttributes.MANUFACTURE: 1}
        )
        robot = DummyRobot(
            coordinate=(2, 2),
            performance={PerformanceAttributes.MANUFACTURE: 1}
        )
        task.assign_robot(robot)
        for _ in range(3):
            updated = task.update()
            self.assertTrue(updated)
        self.assertEqual(task.completed_workload, 3.0)

if __name__ == '__main__':
    unittest.main()
