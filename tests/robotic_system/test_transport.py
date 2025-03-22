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
        self.update_coordinate = MagicMock()
        self.draw_battery_power = MagicMock()

    @property
    def coordinate(self):
        return self._coordinate

class TestTransportTask(unittest.TestCase):

    def test_transport_initialization(self):
        """ total_workloadの初期化をテスト """
        task = Transport(
            name="T1",
            coordinate=(0, 0),
            task_dependency=[],
            required_performance={PerformanceAttributes.TRANSPORT: 1},
            origin_coordinate=(0, 0),
            destination_coordinate=(3, 4),  # 距離は5
            transportability=2.0,
            total_workload=None,
            completed_workload=None
        )
        self.assertEqual(task.total_workload, 10.0)
        self.assertEqual(task.completed_workload, 0.0)

    def test_update_progress(self):
        """ 十分なロボットが割り当てられているときupdateでcompleted_workloadが更新されるか """
        task = Transport(
            name="T1",
            coordinate=(0, 0),
            task_dependency=[],
            required_performance={PerformanceAttributes.TRANSPORT: 1},
            origin_coordinate=(0, 0),
            destination_coordinate=(0, 10),
            transportability=1.0,
            total_workload=None,
            completed_workload=None
        )
        robot = DummyRobot(
            coordinate=(0, 0),
            performance={
                PerformanceAttributes.TRANSPORT: 1,
                PerformanceAttributes.MOBILITY: 5
            }
        )
        task.assign_robot(robot)
        updated = task.update()
        self.assertTrue(updated)
        self.assertEqual(task.completed_workload, 5.0)
        self.assertEqual(task.coordinate, (0.0, 5.0))
        robot.update_coordinate.assert_called_once()
        robot.draw_battery_power.assert_called_once()

    def test_update_insufficient_mobility(self):
        """ 機動力がないロボットでupdateが失敗するか """
        task = Transport(
            name="T2",
            coordinate=(0, 0),
            task_dependency=[],
            required_performance={PerformanceAttributes.TRANSPORT: 1},
            origin_coordinate=(0, 0),
            destination_coordinate=(0, 5),
            transportability=1.0,
            total_workload=None,
            completed_workload=None
        )
        robot = DummyRobot(
            coordinate=(0, 0),
            performance={PerformanceAttributes.TRANSPORT: 1}
        )
        task.assign_robot(robot)
        updated = task.update()
        self.assertFalse(updated)

    def test_dependency_check(self):
        """ 依存タスクが未完了なら update できないことを確認 """
        mock_dep = MagicMock()
        mock_dep.total_workload = 5
        mock_dep.completed_workload = 4
        task = Transport(
            name="T3",
            coordinate=(0, 0),
            task_dependency=[mock_dep],
            required_performance={PerformanceAttributes.TRANSPORT: 1},
            origin_coordinate=(0, 0),
            destination_coordinate=(0, 1),
            transportability=1.0,
            total_workload=None,
            completed_workload=None
        )
        robot = DummyRobot(
            coordinate=(0, 0),
            performance={
                PerformanceAttributes.TRANSPORT: 1,
                PerformanceAttributes.MOBILITY: 1
            }
        )
        task.assign_robot(robot)
        self.assertFalse(task.update())

if __name__ == '__main__':
    unittest.main()
