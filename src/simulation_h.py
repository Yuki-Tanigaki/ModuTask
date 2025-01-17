from collections import defaultdict
import numpy as np
from robotic_system.core import Manufacture, Transport, RobotState, ModuleState
import copy

# エージェントの能力値合計がrequired_abilitiesを満たすかの判定
def check_abilities(agent_list, required_abilities):
    # 各能力の合計値を格納する辞書
    total_abilities = defaultdict(int)
    
    # 各エージェントの能力値を合計
    for agent in agent_list:
        for attribute, value in agent.robot.type.ability.items():
            total_abilities[attribute] += value

    # 必要な能力値を満たしているかチェック
    for attribute, required_value in required_abilities.items():
        if total_abilities[attribute] < required_value:
            return False  # 必要な能力値を満たしていない場合
    
    return True  # 全ての能力値がrequired_abilitiesを満たしている場合

def run_simulation(task_priority, agents, tasks, modules, seed, max_step, charge_station, break_prob):
    # シミュレーション内で使う乱数生成器
    simulation_rng = np.random.default_rng(seed)  # シード値を設定

    # シミュレーションを実行
    finished_tasks = []
    agent_history_ = []
    task_history_ = []

    break_limbs = []
    for t in range(max_step):
        break_limbs_ = []
        for r, agent in enumerate(agents):
            if simulation_rng.random() < break_prob:
                break_limbs_.append(True)
            else:
                break_limbs_.append(False)
        break_limbs.append(break_limbs_)

    agent_history_.append([copy.deepcopy(agent) for agent in agents])
    task_history_.append(copy.deepcopy(tasks))
    for t in range(int(max_step/2)):
        # タスクの完了をチェック
        for task_name, task in tasks.items():
            if task_name in finished_tasks:
                continue
            # タスクがすでに完了しているかチェック
            workload = task.workload # 仕事量[全体, 完了済み]
            if workload[0] <= workload[1]:
                finished_tasks.append(task_name)

        # finished_tasksに含まれないtasks
        filtered_tasks = {k: v for k, v in tasks.items() if k not in finished_tasks}
        # 前提タスクの終了を確認
        tasks_to_remove = []
        for task_name, task in filtered_tasks.items():
            for dependency_task in task.task_dependency:
                if dependency_task.name not in finished_tasks:
                    tasks_to_remove.append(task_name)
                    break
        for task_name in tasks_to_remove:
            filtered_tasks.pop(task_name)

        # 各エージェントのループ
        ready_task = {} # 1ターンの仕事リスト
        for r, agent in enumerate(agents):
            if break_limbs[t][r]:
                agent.break_limb()
            # 働けるかチェック
            # 各モジュールの位置をチェック
            agent.update_active()
            if agent.robot.state == RobotState.INACTIVE: # 稼働不可ならスキップ
                continue
            # 既に充電に割り当てられている場合
            if agent.to_be_charged is not None:
                if agent.check_travel(simulation_rng):
                    agent.travel()
                else:
                    agent.charge()
                continue
            # 充電が必要かチェック
            if not agent.check_battery(charge_station):
                if agent.check_travel(simulation_rng):
                    agent.travel()
                else:
                    agent.charge()
                continue
            # タスクの割り当て
            agent.update_task(task_priority[r], filtered_tasks)
            if agent.assigned_task is None:
                continue
            # タスク地点に到着していないなら移動
            if agent.check_travel(simulation_rng):
                agent.travel()
                continue
            if agent.assigned_task.name not in ready_task:
                ready_task[agent.assigned_task.name] = []
            ready_task[agent.assigned_task.name].append(agent)
            agent.set_work()

        # 仕事を実行
        for task_name, agent_list in ready_task.items():
            required_abilities = tasks[task_name].required_abilities
            if check_abilities(agent_list, required_abilities):
                # 仕事を実行
                if isinstance(tasks[task_name], Transport):
                    tasks[task_name].update()
                    # タスクに合わせて移動
                    for agent in agent_list:
                        agent.work(simulation_rng)
                        agent.travel()
                elif isinstance(tasks[task_name], Manufacture):
                    tasks[task_name].update()
                    for agent in agent_list:
                        agent.work(simulation_rng)
        agent_history = []
        for r, agent in enumerate(agents):
            agent_history.append(copy.deepcopy(agent))
        agent_history_.append(agent_history)
        task_history_.append(copy.deepcopy(tasks))






    # 故障モジュールの割り出しと予備の割り当て
    def find_next_module():
        for _, module in modules.items():
            if module.state == ModuleState.SPARE:
                return module
        return None

    for r, agent in enumerate(agents):
        replace = {}
        for r, module in enumerate(agent.robot.component):        
            if module.state == ModuleState.MALFUNCTION:
                nm = find_next_module()
                if nm is not None:
                    replace[r] = nm
        for r, mod in replace.items():
            agent.robot.component[r] = mod

    # 運搬が必要なモジュールの割り出し
    temp_tasks = copy.deepcopy(tasks)
    for agent in agents:
        for module in agent.robot.component:
            current = copy.deepcopy(module.coordinate)
            next = copy.deepcopy(agent.robot.coordinate)
            if all(abs(x - y) < 1e-9 for x, y in zip(current, next)):
                continue
            # 動的にインスタンス化したモジュール用運搬タスククラスを追加
            abilities = {}
            abilities['TRANSPORT'] = 1
            abilities['MANUFACTURE'] = 0
            task = Transport(
                name=module.name, # 名前
                coordinate=np.array(current),   # タスクの座標
                workload=(1, 0),  # 仕事量[全体, 完了済み]
                task_dependency=[],  # 依存するタスクのリスト
                required_abilities=abilities, # タスクを実行するために必要な合計パフォーマンス
                other_attrs=None, # 任意の追加情報
                origin_destination=(current, next, 1.0)
            )
            temp_tasks.append(new_task)


    # 再構成して実行
    for t in range(int(max_step/2)):
        # タスクの完了をチェック
        for task_name, task in temp_tasks.items():
            if task_name in finished_tasks:
                continue
            # タスクがすでに完了しているかチェック
            workload = task.workload # 仕事量[全体, 完了済み]
            if workload[0] <= workload[1]:
                finished_tasks.append(task_name)

        # finished_tasksに含まれないtasks
        filtered_tasks = {k: v for k, v in tasks.items() if k not in finished_tasks}
        # 前提タスクの終了を確認
        tasks_to_remove = []
        for task_name, task in filtered_tasks.items():
            for dependency_task in task.task_dependency:
                if dependency_task.name not in finished_tasks:
                    tasks_to_remove.append(task_name)
                    break
        for task_name in tasks_to_remove:
            filtered_tasks.pop(task_name)

        # 各エージェントのループ
        ready_task = {} # 1ターンの仕事リスト
        for r, agent in enumerate(agents):
            if break_limbs[int(max_step/2)+t][r]:
                agent.break_limb()
            # 働けるかチェック
            # 各モジュールの位置をチェック
            agent.update_active()
            if agent.robot.state == RobotState.INACTIVE: # 稼働不可ならスキップ
                continue
            # 既に充電に割り当てられている場合
            if agent.to_be_charged is not None:
                if agent.check_travel(simulation_rng):
                    agent.travel()
                else:
                    agent.charge()
                continue
            # 充電が必要かチェック
            if not agent.check_battery(charge_station):
                if agent.check_travel(simulation_rng):
                    agent.travel()
                else:
                    agent.charge()
                continue
            # タスクの割り当て
            agent.update_task(task_priority[r], filtered_tasks)
            if agent.assigned_task is None:
                continue
            # タスク地点に到着していないなら移動
            if agent.check_travel(simulation_rng):
                agent.travel()
                continue
            if agent.assigned_task.name not in ready_task:
                ready_task[agent.assigned_task.name] = []
            ready_task[agent.assigned_task.name].append(agent)
            agent.set_work()

        # 仕事を実行
        for task_name, agent_list in ready_task.items():
            required_abilities = tasks[task_name].required_abilities
            if check_abilities(agent_list, required_abilities):
                # 仕事を実行
                if isinstance(tasks[task_name], Transport):
                    tasks[task_name].update()
                    # タスクに合わせて移動
                    for agent in agent_list:
                        agent.work(simulation_rng)
                        agent.travel()
                elif isinstance(tasks[task_name], Manufacture):
                    tasks[task_name].update()
                    for agent in agent_list:
                        agent.work(simulation_rng)
        agent_history = []
        for r, agent in enumerate(agents):
            agent_history.append(copy.deepcopy(agent))
        agent_history_.append(agent_history)
        task_history_.append(copy.deepcopy(tasks))

    return agent_history_, task_history_