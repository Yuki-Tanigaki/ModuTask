from collections import defaultdict
import numpy as np
from robotic_system.core import Manufacture, Transport, RobotState
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

# **`run_simulation`** 関数の目的および機能。
# `run_simulation` 関数は、エージェントとタスクのシミュレーションを行い、
#   動的な環境でのタスク割り当て、遂行、エージェントの状態変化をモデル化しています。
#   この関数は、複雑なスケジューリング問題やエージェント行動の最適化を解析するための基盤を提供します。
#
# ### **目的**
# `run_simulation` 関数は、エージェントとタスク間の動的な相互作用をシミュレーションするために設計されています。主な目的は、以下の条件を含む状況下で、複数のエージェントがどのようにタスクを遂行するかをモデル化し、結果を記録することです。
# 1. **タスク依存関係**: タスクが他のタスクの完了を前提としている場合、その条件が満たされるまで作業を開始しない。
# 2. **エージェントの行動**: エージェントがタスクの割り当てを受け、作業を遂行し、充電が必要な場合は充電ステーションに移動する。
# 3. **ランダム性の考慮**: エージェントが壊れる確率や移動成功確率など、確率的な要素を取り入れている。
# シミュレーション結果として、**エージェントの状態履歴**や**タスクの進捗状況**を記録し、返却します。
#
# ### **機能**
# 以下に、関数内の主要な機能を整理して説明します。
# #### **1. 初期設定**
# - **乱数生成器 (`simulation_rng`)**
#   シミュレーションの再現性を保つために、指定されたシード値に基づいて乱数生成器を初期化します。
# - **状態記録用リスト (`agent_history_`, `task_history_`)**
#   各タイムステップでのエージェントおよびタスクの状態を記録します。
# - **エージェントの故障フラグ (`break_limbs`)**
#   各タイムステップでエージェントが壊れるかどうかをランダムに決定し記録します。
#
# #### **2. タイムステップのループ処理**
# 1. **タスクの進行管理**
#    - タスクが完了したかどうかをチェックし、完了したタスクを `finished_tasks` に記録します。
#    - 未完了タスクの中で、前提条件を満たさないタスクを除外します。
#
# 2. **エージェントの行動**
#    - エージェントが壊れた場合は、作業不能状態になります。
#    - バッテリーが不足している場合、充電ステーションに移動または充電を行います。
#    - 完了条件を満たしているタスクを選択し、移動や作業を開始します。
#
# 3. **タスクの遂行**
#    - エージェントがタスクに必要な能力を満たしているかをチェックします。
#    - 対応するエージェントがタスクを遂行し、タスクの進行状況を更新します。
#
# 4. **状態の記録**
#    - 各タイムステップ終了後、エージェントとタスクの現在の状態を `agent_history_` と `task_history_` に記録します。
#
# #### **3. 結果の返却**
# 最終的に以下を返します:
# - **`agent_history_`**: 各エージェントのタイムステップごとの状態履歴。
# - **`task_history_`**: 各タスクのタイムステップごとの状態履歴。

def run_simulation(task_priority, agents, tasks, seed, max_step, charge_station, break_prob):
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
    for t in range(max_step):
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

    return agent_history_, task_history_