import unittest
from modutask.core.robot.robot import Robot, RobotType, RobotState
from modutask.core.robot.performance import PerformanceAttributes
from modutask.core.module.module import Module, ModuleType, ModuleState
import numpy as np

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

        # モジュールインスタンス作成
        self.module = Module(
            module_type=self.module_type,
            name="Battery1",
            coordinate=(0, 0),
            battery=10.0,
            operating_time_limit=100.0
        )

        # ロボットインスタンス作成
        self.robot = Robot(
            robot_type=self.robot_type,
            name="Robo1",
            coordinate=(0, 0),
            component=[self.module]
        )

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
        # 初期状態確認
        self.assertEqual(self.robot.state, RobotState.ACTIVE)
        initial_battery = self.robot.total_battery()
        initial_operating_time = self.module.operating_time

        # act 実行
        self.robot.act()

        # バッテリー消費確認
        self.assertEqual(self.robot.total_battery(), initial_battery - self.robot.type.power_consumption)

        # モジュールの operating_time が増加していることを確認
        self.assertEqual(self.module.operating_time, initial_operating_time + 1.0)

    def test_act_when_not_active(self):
        # 強制的に状態を NO_ENERGY に設定
        self.robot._state = RobotState.NO_ENERGY

        with self.assertRaises(RuntimeError):
            self.robot.act()
    
    def test_travel(self):
        target = (1.0, 0.0)
        initial_battery = self.robot.total_battery()
        initial_operating_time = self.module.operating_time
        initial_coord = self.robot.coordinate

        self.robot.travel(target)

        # 座標が変化している（移動した）こと
        self.assertNotEqual(self.robot.coordinate, initial_coord)
        # 座標が目的地に向かっていること（完全一致は距離と移動力による）
        self.assertNotEqual(self.robot.coordinate, (0.0, 0.0))
        # バッテリー消費されたか
        self.assertLess(self.robot.total_battery(), initial_battery)
        # operating_time 増加しているか
        self.assertEqual(self.module.operating_time, initial_operating_time + 1.0)
        # モジュールの座標もロボットと同期しているか
        for module in self.robot.component_mounted:
            self.assertEqual(module.coordinate, self.robot.coordinate)

    def test_travel_with_insufficient_battery(self):
        # バッテリーをゼロにして状態を更新（強制的に NO_ENERGY に）
        self.module.battery = 0.0
        self.robot.update_state()
        self.assertEqual(self.robot.state, RobotState.NO_ENERGY)
        with self.assertRaises(RuntimeError):
            self.robot.travel((1.0, 1.0))

    def test_missing_components(self):
        self.assertEqual(self.robot.missing_components(), [])

    def test_mount_module_error(self):
        # 別座標にあるモジュール → エラーを期待
        wrong_module = Module(
            module_type=self.module_type,
            name="Battery2",
            coordinate=(1, 1),  # 異なる座標
            battery=5.0,
            operating_time_limit=100.0
        )
        with self.assertRaises(RuntimeError):
            self.robot.mount_module(wrong_module)

    def test_travel_and_battery_usage(self):
        self.robot.travel((1, 0))
        self.assertNotEqual(self.robot.coordinate, (0, 0))
        self.assertLess(self.robot.total_battery(), 10.0)
    
    def test_update_state_active(self):
        # 状態が正しくACTIVEに保たれるか
        self.robot.update_state()
        self.assertEqual(self.robot.state, RobotState.ACTIVE)

    def test_update_state_defective_due_to_missing_module(self):
        # モジュールを強制的に除去して足りない状態にする
        self.robot._component_mounted = []
        self.robot.update_state()
        self.assertEqual(self.robot.state, RobotState.DEFECTIVE)

    def test_update_state_no_energy(self):
        # バッテリーを空にしてエネルギー不足状態にする
        self.module.battery = 0.0
        self.robot.update_state()
        self.assertEqual(self.robot.state, RobotState.NO_ENERGY)

    def test_update_state_excludes_error_modules(self):
        # モジュールをERROR状態にし、update_state後に除外されていることを確認
        self.module.operating_time = 100.0
        self.robot.update_state()
        self.assertNotIn(self.module, self.robot.component_mounted)
        self.assertEqual(self.robot.state, RobotState.DEFECTIVE)  # モジュールが足りなくなるため

if __name__ == '__main__':
    unittest.main()
