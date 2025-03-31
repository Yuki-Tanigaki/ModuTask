import unittest
from unittest.mock import MagicMock
from modutask.core.task.charge import Charge

def make_mock_robot():
    robot = MagicMock()
    robot.charge_battery_power = MagicMock()
    return robot

class TestCharge(unittest.TestCase):
    def test_charge_single_robot(self):
        """ 単一ロボットが充電されるケース """
        robot = make_mock_robot()
        task = Charge("charge", (0.0, 0.0), charging_speed=5.0)
        task._assigned_robot = [robot]

        result = task.update()

        self.assertTrue(result)
        robot.charge_battery_power.assert_called_once_with(5.0)

    def test_charge_multiple_robots(self):
        """ 複数ロボットが全て充電されるケース """
        robots = [make_mock_robot(), make_mock_robot()]
        task = Charge("charge", (1.0, 1.0), charging_speed=3.5)
        task._assigned_robot = robots

        result = task.update()

        self.assertTrue(result)
        for r in robots:
            r.charge_battery_power.assert_called_once_with(3.5)

    def test_charge_no_assigned_robot(self):
        """ _assigned_robot が None のとき RuntimeError """
        task = Charge("charge", (0.0, 0.0), charging_speed=2.0)
        task._assigned_robot = None

        with self.assertRaises(RuntimeError):
            task.update()

if __name__ == '__main__':
    unittest.main()
