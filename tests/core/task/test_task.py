import unittest
from unittest.mock import MagicMock
from modutask.core.task import BaseTask
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.robot.robot import RobotState

class DummyTask(BaseTask):
    """ テスト用の具象クラス """
    def update(self) -> bool:
        return True


class TestBaseTask(unittest.TestCase):
    def setUp(self):
        self.coord = (1.0, 2.0)
        self.required_perf = {attr: 1.0 for attr in PerformanceAttributes}
        self.task = DummyTask(
            name="MockTask",
            coordinate=self.coord,
            total_workload=10.0,
            completed_workload=5.0,
            required_performance=self.required_perf
        )

    def test_name_and_coordinate(self):
        self.assertEqual(self.task.name, "MockTask")
        self.assertEqual(self.task.coordinate, self.coord)

    def test_is_completed(self):
        self.assertFalse(self.task.is_completed())
        self.task._completed_workload = 10.0
        self.assertTrue(self.task.is_completed())

    def test_dependency_check(self):
        dep1 = MagicMock()
        dep2 = MagicMock()
        dep1.is_completed.return_value = True
        dep2.is_completed.return_value = False
        self.task.initialize_task_dependency([dep1, dep2])
        self.assertFalse(self.task.are_dependencies_completed())
        dep2.is_completed.return_value = True
        self.assertTrue(self.task.are_dependencies_completed())

    def test_assign_and_release_robot(self):
        robot = MagicMock()
        robot.coordinate = self.coord
        robot.state = RobotState.ACTIVE
        robot.type.performance = {attr: 2.0 for attr in PerformanceAttributes}

        self.task.assign_robot(robot)
        self.assertIn(robot, self.task.assigned_robot)

        self.task.release_robot()
        self.assertEqual(self.task.assigned_robot, None)

    def test_assign_robot_defective(self):
        robot = MagicMock()
        robot.coordinate = self.coord
        robot.state = RobotState.DEFECTIVE
        robot.__str__.return_value = "MockRobot"

        with self.assertRaises(RuntimeError):
            self.task.assign_robot(robot)

    def test_assign_robot_no_energy(self):
        robot = MagicMock()
        robot.coordinate = self.coord
        robot.state = RobotState.NO_ENERGY
        robot.__str__.return_value = "MockRobot"        

        with self.assertRaises(RuntimeError):
            self.task.assign_robot(robot)

    def test_assign_robot_wrong_coordinate(self):
        robot = MagicMock()
        robot.coordinate = (9.9, 9.9)
        robot.state = RobotState.ACTIVE

        with self.assertRaises(RuntimeError):
            self.task.assign_robot(robot)

    def test_is_performance_satisfied(self):
        robot = MagicMock()
        robot.type.performance = {attr: 2.0 for attr in PerformanceAttributes}
        self.task._assigned_robot = [robot]
        self.assertTrue(self.task.is_performance_satisfied())


if __name__ == "__main__":
    unittest.main()
