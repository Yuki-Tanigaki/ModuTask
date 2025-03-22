import unittest
from modutask.robotic_system import *

class TestModuleState(unittest.TestCase):

    def test_from_value_valid(self):
        self.assertEqual(ModuleState.from_value(0), ModuleState.ACTIVE)
        self.assertEqual(ModuleState.from_value(1), ModuleState.ERROR)

    def test_from_value_invalid(self):
        with self.assertRaises(ValueError):
            ModuleState.from_value(2)

    def test_color_property(self):
        self.assertEqual(ModuleState.ACTIVE.color, 'green')
        self.assertEqual(ModuleState.ERROR.color, 'gray')

    def test_enum_members(self):
        self.assertTrue(hasattr(ModuleState, 'ACTIVE'))
        self.assertTrue(hasattr(ModuleState, 'ERROR'))
        self.assertIsInstance(ModuleState.ACTIVE, ModuleState)
        self.assertIsInstance(ModuleState.ERROR, ModuleState)

class TestModuleType(unittest.TestCase):

    def test_equality(self):
        mod1 = ModuleType(name="TypeA", max_battery=100.0)
        mod2 = ModuleType(name="TypeA", max_battery=150.0)
        mod3 = ModuleType(name="TypeB", max_battery=100.0)
        self.assertEqual(mod1, mod2)
        self.assertNotEqual(mod1, mod3)

    def test_hash(self):
        mod1 = ModuleType(name="TypeA", max_battery=100.0)
        mod2 = ModuleType(name="TypeA", max_battery=200.0)
        mod3 = ModuleType(name="TypeC", max_battery=100.0)
        self.assertEqual(hash(mod1), hash(mod2))
        self.assertNotEqual(hash(mod1), hash(mod3))

    def test_attributes(self):
        mod = ModuleType(name="PowerCore", max_battery=80.0)
        self.assertEqual(mod.name, "PowerCore")
        self.assertEqual(mod.max_battery, 80.0)

class TestModule(unittest.TestCase):

    def setUp(self):
        self.module_type = ModuleType(name="Core", max_battery=100.0)
        self.module = Module(module_type=self.module_type, name="M1", coordinate=(0, 0), battery=50.0)

    def test_initialization(self):
        self.assertEqual(self.module.name, "M1")
        self.assertEqual(self.module.coordinate, (0.0, 0.0))
        self.assertEqual(self.module.battery, 50.0)
        self.assertEqual(self.module.state, ModuleState.ACTIVE)
        self.assertEqual(self.module.type, self.module_type)

    def test_str_and_repr(self):
        self.assertIn("M1", str(self.module))
        self.assertIn("Battery", str(self.module))
        self.assertIn("M1", repr(self.module))
        self.assertIn("Core", repr(self.module))

    def test_update_coordinate(self):
        self.module.update_coordinate((1, 2))
        self.assertEqual(self.module.coordinate, (1.0, 2.0))

    def test_update_battery_normal(self):
        self.module.update_battery(10)
        self.assertEqual(self.module.battery, 60.0)

    def test_update_battery_overflow(self):
        self.module.update_battery(100)
        self.assertEqual(self.module.battery, 100.0)

    def test_update_battery_underflow(self):
        self.module.update_battery(-100)
        self.assertEqual(self.module.battery, 0.0)

    def test_update_battery_in_error_state(self):
        self.module.update_state(ModuleState.ERROR)
        with self.assertRaises(RuntimeError):
            self.module.update_battery(10)

    def test_update_state(self):
        self.module.update_state(ModuleState.ERROR)
        self.assertEqual(self.module.state, ModuleState.ERROR)

    def test_invalid_battery_on_init(self):
        with self.assertRaises(ValueError):
            Module(self.module_type, "TooMuch", (0, 0), 200.0)

if __name__ == '__main__':
    unittest.main()
