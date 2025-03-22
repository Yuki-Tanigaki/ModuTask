import unittest
from unittest.mock import MagicMock
from modutask.robotic_system import *

class DummyRobot:
    def __init__(self, coordinate):
        self.name = MagicMock()
        self.state = RobotState.ACTIVE
        self.coordinate = coordinate
        self.charge_battery_power = MagicMock()

class TestChargeTask(unittest.TestCase):

    def test_charging_speed_set_correctly(self):
        charge_task = Charge(name="C1", coordinate=(0, 0), charging_speed=5.0)
        self.assertEqual(charge_task.charging_speed, 5.0)
        self.assertEqual(charge_task.total_workload, 0.0)
        self.assertEqual(charge_task.completed_workload, 0.0)
        self.assertEqual(charge_task.required_performance, {})

    def test_update_charges_all_robots(self):
        charge_task = Charge(name="C2", coordinate=(1, 1), charging_speed=2.0)
        robot1 = DummyRobot(coordinate=(1, 1))
        robot2 = DummyRobot(coordinate=(1, 1))
        charge_task.assign_robot(robot1)
        charge_task.assign_robot(robot2)

        updated = charge_task.update()

        self.assertTrue(updated)
        robot1.charge_battery_power.assert_called_once_with(2.0)
        robot2.charge_battery_power.assert_called_once_with(2.0)

    def test_update_no_robots(self):
        charge_task = Charge(name="C3", coordinate=(0, 0), charging_speed=1.0)
        # ロボットが割り当てられていなくても update は True を返す
        updated = charge_task.update()
        self.assertTrue(updated)  # 充電処理は空でもエラーではない

if __name__ == '__main__':
    unittest.main()
