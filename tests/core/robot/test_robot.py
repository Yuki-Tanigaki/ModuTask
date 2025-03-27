import unittest
from unittest.mock import MagicMock
from modutask.core.robot.robot import Robot, RobotType, RobotState
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.module.module import Module, ModuleType

class TestRobot(unittest.TestCase):

    def setUp(self):
        # モジュールタイプとロボットタイプの定義
        self.module_type = ModuleType(name="BatteryModule", max_battery=10.0)
        self.performance = {
            PerformanceAttributes.MOBILITY: 1,
            PerformanceAttributes.MANUFACTURE: 2,
            PerformanceAttributes.TRANSPORT: 1
        }
        self.robot_type = RobotType(
            name="BasicBot",
            required_modules={self.module_type: 1},
            performance=self.performance,
            power_consumption=5.0,
            recharge_trigger=2.0
        )

        # MagicMock を使ったシナリオ
        self.mock_scenario = MagicMock()
        self.mock_scenario.malfunction_module.return_value = False

        # モジュール作成＆シナリオ初期化
        self.module = Module(
            module_type=self.module_type,
            name="Battery1",
            coordinate=(0, 0),
            battery=10.0,
            operating_time=0.0
        )

        # ロボット作成
        self.robot = Robot(
            robot_type=self.robot_type,
            name="Robo1",
            coordinate=(0, 0),
            component=[self.module]
        )
        self.robot.update_state([self.mock_scenario])
        

    def test_initial_state(self):
        self.assertEqual(self.robot.name, "Robo1")
        self.assertEqual(self.robot.state, RobotState.ACTIVE)
        self.assertEqual(self.robot.coordinate, (0, 0))

    def test_total_battery(self):
        self.assertEqual(self.robot.total_battery(), 10.0)
        self.assertEqual(self.robot.total_max_battery(), 10.0)

    def test_is_battery_full(self):
        self.assertTrue(self.robot.is_battery_full())

    def test_draw_battery_power(self):
        self.robot.draw_battery_power()
        self.assertEqual(self.robot.total_battery(), 5.0)

    def test_charge_battery_power(self):
        self.robot.draw_battery_power()
        self.robot.charge_battery_power(3.0)
        self.assertEqual(self.robot.total_battery(), 8.0)

    def test_act(self):
        initial_battery = self.robot.total_battery()
        initial_operating_time = self.module.operating_time
        self.robot.act()
        self.assertEqual(self.robot.total_battery(), initial_battery - self.robot.type.power_consumption)
        self.assertEqual(self.module.operating_time, initial_operating_time + 1.0)

    def test_act_when_not_active(self):
        self.robot._state = RobotState.NO_ENERGY
        with self.assertRaises(RuntimeError):
            self.robot.act()

    def test_travel(self):
        target = (1.0, 0.0)
        initial_battery = self.robot.total_battery()
        initial_operating_time = self.module.operating_time
        initial_coord = self.robot.coordinate
        self.robot.travel(target)
        self.assertNotEqual(self.robot.coordinate, initial_coord)
        self.assertLess(self.robot.total_battery(), initial_battery)
        self.assertEqual(self.module.operating_time, initial_operating_time + 1.0)
        for module in self.robot.component_mounted:
            self.assertEqual(module.coordinate, self.robot.coordinate)

    def test_travel_with_insufficient_battery(self):
        self.module.battery = 0.0
        self.robot.update_state([self.mock_scenario])
        self.assertEqual(self.robot.state, RobotState.NO_ENERGY)
        with self.assertRaises(RuntimeError):
            self.robot.travel((1.0, 1.0))

    def test_missing_components(self):
        self.assertEqual(self.robot.missing_components(), [])

    def test_mount_module_error(self):
        wrong_module = Module(
            module_type=self.module_type,
            name="Battery2",
            coordinate=(1, 1),
            battery=5.0,
            operating_time=0.0
        )
        wrong_module.update_state([self.mock_scenario])
        with self.assertRaises(RuntimeError):
            self.robot.mount_module(wrong_module)

    def test_travel_and_battery_usage(self):
        self.robot.travel((1, 0))
        self.assertNotEqual(self.robot.coordinate, (0, 0))
        self.assertLess(self.robot.total_battery(), 10.0)

    def test_update_state_active(self):
        self.robot.update_state([self.mock_scenario])
        self.assertEqual(self.robot.state, RobotState.ACTIVE)

    def test_update_state_defective_due_to_missing_module(self):
        self.robot._component_mounted = []
        self.robot.update_state([self.mock_scenario])
        self.assertEqual(self.robot.state, RobotState.DEFECTIVE)

    def test_update_state_no_energy(self):
        self.module.battery = 0.0
        self.robot.update_state([self.mock_scenario])
        self.assertEqual(self.robot.state, RobotState.NO_ENERGY)

    def test_update_state_excludes_error_modules(self):
        # 故障を返すようにシナリオを変更
        self.mock_scenario.malfunction_module.return_value = True
        self.module.update_state([self.mock_scenario])
        self.robot.update_state([self.mock_scenario])
        self.assertNotIn(self.module, self.robot.component_mounted)
        self.assertEqual(self.robot.state, RobotState.DEFECTIVE)

if __name__ == '__main__':
    unittest.main()
