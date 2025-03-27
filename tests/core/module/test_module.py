import unittest
from unittest.mock import MagicMock
from modutask.core.module.module import Module, ModuleType, ModuleState


class TestModule(unittest.TestCase):
    def setUp(self):
        self.module_type = ModuleType(name="TestType", max_battery=100.0)
        self.module = Module(
            module_type=self.module_type,
            name="TestModule",
            coordinate=(0.0, 0.0),
            battery=50.0,
            operating_time=5.0
        )
        # MagicMock で scenario を生成
        self.mock_scenario = MagicMock()
        self.mock_scenario.malfunction_module.return_value = False
        self.module.update_state([self.mock_scenario])

    def test_initial_state(self):
        self.assertEqual(self.module.name, "TestModule")
        self.assertEqual(self.module.coordinate, (0.0, 0.0))
        self.assertEqual(self.module.battery, 50.0)
        self.assertEqual(self.module.state, ModuleState.ACTIVE)

    def test_set_battery_valid(self):
        self.module.battery = 80.0
        self.assertEqual(self.module.battery, 80.0)

    def test_set_battery_invalid(self):
        with self.assertRaises(ValueError):
            self.module.battery = 120.0  # exceeds max
        with self.assertRaises(ValueError):
            self.module.battery = -5.0   # negative

    def test_set_operating_time_valid(self):
        self.module.operating_time = 7.0
        self.assertEqual(self.module.operating_time, 7.0)

    def test_set_operating_time_invalid(self):
        with self.assertRaises(ValueError):
            self.module.operating_time = -1.0
        with self.assertRaises(ValueError):
            self.module.operating_time = 4.0  # smaller than current

    def test_update_state_sets_error(self):
        self.mock_scenario.malfunction_module.return_value = True
        self.module.update_state([self.mock_scenario])
        self.assertEqual(self.module.state, ModuleState.ERROR)

    def test_str_repr(self):
        self.assertIn("Module(TestModule", str(self.module))
        self.assertIn("Module(name=TestModule", repr(self.module))


if __name__ == '__main__':
    unittest.main()
