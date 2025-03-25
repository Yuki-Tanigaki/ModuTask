import unittest
from unittest.mock import MagicMock
from modutask.core.task.assembly import Assembly

def make_mock_module(coord):
    module = MagicMock()
    module.coordinate = coord
    return module

def make_mock_robot(modules, robot_coord=(0.0, 0.0)):
    robot = MagicMock()
    robot.coordinate = robot_coord
    robot.missing_components.return_value = modules
    robot.mount_module = MagicMock()
    return robot

class TestAssembly(unittest.TestCase):
    def test_successful_assembly(self):
        """ 部品がロボットと異なる位置にあるケース """
        module = make_mock_module(coord=(1.0, 1.0))
        robot = make_mock_robot(modules=[module], robot_coord=(0.0, 0.0))
        task = Assembly("assembly", robot)

        result = task.update()

        self.assertFalse(result)
        robot.mount_module.assert_not_called()
        self.assertEqual(task.completed_workload, 0.0)

    def test_module_already_installed(self):
        """ モジュールの座標がロボットと一致しているケース """
        module = make_mock_module(coord=(0.0, 0.0))
        robot = make_mock_robot(modules=[module], robot_coord=(0.0, 0.0))
        task = Assembly("assembly", robot)

        result = task.update()

        self.assertTrue(result)
        robot.mount_module.assert_called_once_with(module)
        self.assertEqual(task.completed_workload, 1.0)

    def test_already_completed_task(self):
        """ 欠損部品がなく既にタスク完了している場合 """
        robot = make_mock_robot(modules=[], robot_coord=(0.0, 0.0))
        task = Assembly("assembly", robot)

        self.assertTrue(task.is_completed())
        result = task.update()

        self.assertFalse(result)
        robot.mount_module.assert_not_called()

if __name__ == '__main__':
    unittest.main()
