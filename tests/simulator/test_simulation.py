import pytest, os
import numpy as np
from modutask.robotic_system.core import Module, Robot, Task, ModuleState, RobotState
from modutask.robotic_system.manager import DataManager
from modutask.simulator.simulation import Simulator

@pytest.fixture
def simulator():
    """ シミュレーターのインスタンスを作成 """
    property_file = os.path.join("properties", "test_property.yaml")
    return Simulator(property_file)

def test_simulator_initialization(simulator):
    """ シミュレーションの初期化が正しく行われるか確認 """
    assert simulator.manager is not None
    assert isinstance(simulator.module_types, dict)
    assert isinstance(simulator.robot_types, dict)
    assert isinstance(simulator.modules, dict)
    assert isinstance(simulator.robots, dict)
    assert isinstance(simulator.tasks, dict)

def test_module_loading(simulator):
    """ モジュールのロードが正しく行われるか確認 """
    assert len(simulator.module_types) > 0, "モジュールタイプがロードされていません"
    for module in simulator.modules.values():
        assert isinstance(module, Module)
        assert module.state in [ModuleState.ACTIVE, ModuleState.ERROR]

def test_robot_loading(simulator):
    """ ロボットのロードが正しく行われるか確認 """
    assert len(simulator.robots) > 0, "ロボットがロードされていません"
    for robot in simulator.robots.values():
        assert isinstance(robot, Robot)
        assert robot.state in RobotState

def test_task_loading(simulator):
    """ タスクのロードが正しく行われるか確認 """
    assert len(simulator.tasks) > 0, "タスクがロードされていません"
    for task in simulator.tasks.values():
        assert isinstance(task, Task)
        assert isinstance(task.coordinate, tuple)

# def test_simulation_run(simulator):
#     """ シミュレーションが正常に動作するか確認 """
#     try:
#         simulator.run_simulation()
#     except Exception as e:
#         pytest.fail(f"シミュレーション実行中に例外が発生: {e}")

if __name__ == "__main__":
    pytest.main()
