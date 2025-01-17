- component
	- robotic_system.py: 
		タスク，モジュール，ロボットの状態を保存するクラスの記述
	- malfunction.py
	- data_manager.py
		タスク，モジュール，ロボットの状態の読み込み書き出し

============================
推定:
    ルートフォルダのmain.pyは動作していない（機能していない）。

    ×）simulation.pyまたはsimulation_h.pyを起動プログラム(main.py相当)として実行するもの。
        また、それぞれの中にある"run_simulation()"をコールする。

    〇）simulation.py（またはsimulation_h.py）は、以下の引数が必要。
        task_priority, agents, tasks, seed, max_step, charge_station, break_prob
        これらを別の処理によって作る必要がある。
        つまり、simulation.py（またはsimulation_h.py）を実行する上位の処理が存在する。

    simulator/simulation.pyまたはsimulation_h.pyは、選択的に実行される。
    それそれの"run_simulation()"関数が、robotic_system/core.pyをコールする。
    "run_simulation()"関数は、agent_history_, task_history_を返す。

    何らかの仕掛けによって、simulation.pyまたはsimulation_h.pyの実行と並行して、以下のものを動作させる。
    - simulator/agent.py
    - robotic_system/data_manager.py

    robotic_system/core.pyは、以下からコールされる重要な共通モジュール。
    - robotic_system/data_manager.py
    - simulator/agent.py
    - simulator/simulation.py または simulation_h.py

    jupyterノートブックは、agent_history_, task_history_を入力値として、mp4ファイル形式の動画を作成する。
    動画の作成に当たり、ffmpegを使用する。

理解の進め方：
    1. simulation.pyをmain.py相当のものとして理解して（simulation_h.pyの方が規模大、作成途上の様子が伺えるため）
        "run_simulation()"関数の内容を理解する。
            ※simulation_h.pyの理解は、後日。
    2. "run_simulation()"関数がコールする、robotic_system/core.pyのクラスを理解する。
    3. 続いて、agent.pyとdata_manager.pyの動きを理解する。
        ※但し、これらが誰によってコールされるのか、その仕掛けを理解しないといけない。
    4. jupyterノートブックの描画処理について理解する。進化系アルゴリズム等の研究的要素なく、優先度低い。

========================================================
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



========================================================
- component #0
    # robotic_system/data_manager.py
    #   -> robotic_system/core.py

    - robotic_system/data_manager.py
        - robotic_system/core.py
            - class Task
            - class Module
            - class Robot
            - class ModuleType
            - class RobotType
            - class RobotPerformanceAttributes
            - class ModuleState

- component #1
    # main.py
    #    -> agent.py/SimulationAgent
    #        -> robotic_system/core.py

    - simulator/agent.py:       # ★
        - class SimulationAgent
        - robotic_system/core.py
            - class RobotState
            - class ModuleState
            - class RobotPerformanceAttributes

- component #2-1
    # simulator/simulation.py
    #     -> robotic_system/core.py

    - simulator/simulation.py:      # agent_history_, task_history_を返す
        - def run_simulation()      # ★
            - def check_abilities()
            - robotic_system/core.py
                - class RobotState
                - class Manufacture
                - class Transport

- component #2-2
    # simulator/simulation_h.py
    #    -> robotic_system/core.py

    - simulator/simulation_h.py:      # agent_history_, task_history_を返す
        - def run_simulation()      # ★
            - def check_abilities()
            - robotic_system/core.py
                - class RobotState
                - class ModuleState
                - class Manufacture
                - class Transport
