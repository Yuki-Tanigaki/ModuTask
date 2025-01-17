#!/usr/bin/env python
# coding: utf-8

# In[1]:


from IPython.display import clear_output

get_ipython().system('pip install -U pymoo')
get_ipython().system('pip install omegaconf')
get_ipython().system('pip install dill')
clear_output()


# In[1]:


from google.colab import drive
drive.mount('/content/drive')


# In[2]:


import sys
sys.path.append('/content/drive/MyDrive/Colab Notebooks/Moonshot/src')
get_ipython().run_line_magic('cd', '/content/drive/MyDrive/Colab Notebooks/Moonshot/20241228')


# In[15]:
#### 2. **Pythonスクリプト**
#    - **`Manager.py`**:
#      - **パス**: `robotic_system/data_manager/Manager.py`
#      - **役割**:
#        - データをプロパティファイルや他のリソースから読み取り、オブジェクトとして管理。
#        - メソッド例:
#          - `read_task()`: タスク情報を取得。
#          - `read_module_type()`: モジュールの種類情報を取得。

#    - **`SimulationAgent.py`**:
#      - **パス**: `simulator/agent/SimulationAgent.py`
#      - **役割**:
#        - シミュレーションにおけるエージェントの挙動を定義するクラス。
#        - 具体的な動作（例: ロボットの移動やタスクの実行）をシミュレートする機能を持つ。

#    - **`simulation.py`**:
#      - **パス**: `simulator/simulation.py`
#      - **役割**:
#        - 実際のシミュレーションを実行する関数やクラスを提供。
#        - 例: `run_simulation()` 関数を使ってシミュレーション全体を動かす。

### **プログラムの補足ポイント**
# 1. **カレントディレクトリの確認**:
#    - 実行時に正しいディレクトリから起動する必要があります（`properties` フォルダが存在する場所）。

# 2. **`Manager` クラスの実装次第でデータ処理の流れが変わる**:
#    - `Manager` がどのようにタスクやモジュールをロードしているかを確認することで、具体的なデータの構造がわかります。

# 3. **YAMLファイルの内容が重要**:
#    - `test.yaml` の内容によって、シミュレーションの動作が大きく変わります。

from robotic_system.data_manager import Manager
from simulator.agent import SimulationAgent
from simulator.simulation import run_simulation

from omegaconf import OmegaConf
import numpy as np
import os, copy

# propertyファイルを読み込み（\properties\test.yaml）
# 1. **設定ファイルの読み込み:**
#    - `\properties\test.yaml` というYAML形式のプロパティファイルを読み込んで、`OmegaConf` オブジェクトとして利用します。
#       このファイルはシミュレーションの各種設定（例えば、タスクやモジュールのパラメータなど）を格納していると推測されます。
#### **プロパティファイル**
#    - `test.yaml`:
#      - **パス**: `properties/test.yaml` (カレントディレクトリ基準)。
#      - **内容の役割**:
#        - シミュレーションの設定。
#        - 例: タスクの詳細、モジュールやロボットの構成情報、各種パラメータ。
property_file = os.path.join('properties', 'test.yaml')
properties = OmegaConf.load(property_file)

# 2. **Manager クラスのインスタンス化:**
#    - Manager.pyファイルが必要
#    - `Manager` クラスのインスタンスを作成し、その初期化に `properties` を使用します。
#   `Manager` クラスはデータの読み書きを担当するクラスで、タスク、モジュール、ロボットの情報を処理する機能を持っています。
manager = Manager(properties)

# 3. **データの読み込み:**
# SimulationAgent.pyファイルが必要
#    - `Manager` クラスの各種メソッドを使って、以下のデータを読み取ります。
#      - `tasks`: 実行すべきタスクのリスト。
#      - `module_types`: モジュールの種類情報。
#      - `robot_types`: ロボットの種類情報。
#      - `modules`: モジュールの具体的なインスタンス情報。
#      - `robots`: ロボットの具体的なインスタンス情報。
tasks = manager.read_task()
module_types = manager.read_module_type()
robot_types = manager.read_robot_type(module_types)
modules = manager.read_module(module_types)
robots = manager.read_robot(robot_types, modules)


for t_name, task in tasks.items():
    print(task)

print(module_types)

# # シミュレーション設定
# seed = properties.simulation.seed
# max_step = properties.simulation.maxSimulationStep
# max_step = 100
# battery_limit = properties.simulation.batteryLimit
# charge_station = properties.simulation.chargeStation

# # シミュレーションエージェントの生成
# agents = [SimulationAgent(robot, battery_limit) for _, robot in robots.items()]

# task_priority = []
# np.random.seed(1111)
# for _ in agents:
#     keys = tasks.keys()
#     # 辞書のキーをリストに変換してシャッフルする
#     task_priority_ = np.array(list(keys))  # keysをリストに変換
#     np.random.shuffle(task_priority_)  # その場で並び替え
#     task_priority.append(copy.deepcopy(task_priority_))


# agent_history, task_history = run_simulation(task_priority, agents, tasks, seed, max_step, charge_station, 0.001)
# print(task_history)
# print(agent_history)


# In[9]:アニメーション動画作成モジュール
# （ロボットを動かした後、どのように動いたのか、動画として可視化するためのもの）
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec
from matplotlib import rc
from matplotlib.collections import PolyCollection
import matplotlib.patches as patches
from matplotlib.patches import Circle, Rectangle, Ellipse, Polygon
from math import cos, sin, pi

from robotic_system.core import RobotState

# 描画する正三角形のパラメータ
triangle_size = 0.5  # 辺の長さ
rectangle_size = 0.5  # 辺の長さ
pentagon_size = 0.4 # 辺の長さ
ellipse_size = (0.5, 0.2) # 半径
circle_size = 0.4 # 半径


# 正三角形の頂点を計算
def calculate_equilateral_triangle_vertices(center):
    x, y = center
    # 頂点を計算
    vertices = [
        (x + triangle_size * cos(pi / 6 + i * 2 * pi / 3), y + triangle_size * sin(pi / 6 + i * 2 * pi / 3))
        for i in range(3)
    ]
    return vertices

# 逆正三角形の頂点を計算する関数
def calculate_inverted_triangle_vertices(center):
    x, y = center
    # 頂点を計算
    vertices = [
        (x + triangle_size * cos(-pi / 6 + i * 2 * pi / 3), y + triangle_size * sin(-pi / 6 + i * 2 * pi / 3))
        for i in range(3)
    ]
    return vertices

# 正方形の左下の座標を計算する関数
def calculate_rectangle_vertices(center):
    return (center[0] - rectangle_size / 2, center[1] - rectangle_size / 2)

# 五角形の頂点を計算する関数
def calculate_pentagon_vertices(center):
    x, y = center
    # 5つの頂点を計算
    vertices = [
        (x + pentagon_size * cos(2 * pi * i / 5), y + pentagon_size * sin(2 * pi * i / 5))
        for i in range(5)
    ]
    return vertices

#   アニメーション動画作成関数（ロボットを動かした後、どのように動いたのか、動画として可視化するためのもの）
#   ※動いた結果は、agent_historyとtask_history
#       ・２×２のグラフ作成
#       ・agent_historyの数だけループ
#           ・凡例を描画（初回だけ）
#           ・agent(ロボット)の数だけループ
#               ・ロボットのタイプに応じて描画（例.〇/△/□）
#           ・棒グラフ描画
#           ・スケジュール表描画
#       ・動画記録（ffmpegを使用）

def save_animation(agent_history, task_history, numsave_dir, name, max_step, agent_name_list, task_name_list, file_name):
    # 描画するグラフの設定
    # ax[0]: ロボット移動軌跡
    # ax[2]: タスク残量
    # ax[3]: スケジュール表

    fig = plt.figure(figsize=(7.5, 5))
    gs = gridspec.GridSpec(2, 2, height_ratios=(3, 1))
    ax = [plt.subplot(gs[0, 0]), plt.subplot(gs[0, 1]), plt.subplot(gs[1, 0]), plt.subplot(gs[1, 1])]
    legend_flag = True  # 凡例描画のフラグ
    plt.close()

    # カラーマップを用意する
    color_map = {
        'Transport': 'blue',
        'Manufacture': 'green'
    }

    # アニメーション用のグラフ保管場所
    ims = []

    # スケジュール
    scheduleBar = {}
    for member in RobotState:
        scheduleBar[member] = [[] for x in range(len(agent_name_list))]

    assert len(task_history) == len(agent_history), "Mismatch: task_history and agent_history must be of the same length."

    for t, agents in enumerate(agent_history):
        # 描画設定
        if legend_flag:  # 一回のみ凡例を描画
            ax[0].legend(loc='lower center', bbox_to_anchor=(1.1, 1.1), ncol=4)
            ax[0].set_xlim([-6.0, 6.0])
            ax[0].set_ylim([-6.0, 6.0])
            ax[0].tick_params(labelbottom=False, labelleft=False, labelright=False, labeltop=False, length=0)
            ax[0].tick_params(length=0)
            ax[0].set_title("2D simulation")
            ax[1].axis("off")
            ax[1].set_xlim([-6.0, 6.0])
            ax[1].set_ylim([-6.0, 6.0])
            ax[1].tick_params(labelbottom=False, labelleft=False, labelright=False, labeltop=False, length=0)
            ax[1].tick_params(length=0)
            ax[2].set_xlim(0, len(task_name_list))
            ax[2].set_ylim(0, 20)
            ax[2].set_xticks([n for n in range(len(task_name_list))])
            ax[2].set_title("Leftover Jobs")
            handles = [plt.Rectangle((0,0),1,1, color=color_map[cat]) for cat in color_map]
            labels = list(color_map.keys())
            ax[2].set_xticklabels(task_name_list, rotation=45, ha='right') # 横軸ラベル回転
            ax[2].legend(handles, labels) # 凡例を追加

            ax[3].set_xlim(0, max_step)
            ax[3].set_ylim(0, len(agent_name_list))
            ax[3].set_title('Timeline')
            ax[3].set_xlabel("period")
            ax[3].set_ylabel("robots")
            ax[3].tick_params(labelbottom=True, labelleft=True, labelright=False, labeltop=False, length=0)
            legend_flag = False
        # subplot0：2D
        im = []
        for r, agent in enumerate(agents):
            robot_coodinate = agent.robot.coordinate
            robot_state = agent.robot.state
            robot_type = agent.robot.type.name
            if robot_type == 'TWSH':
                vertices = calculate_equilateral_triangle_vertices(robot_coodinate)
                triangle = Polygon(vertices, closed=True, color=robot_state.color, alpha=0.8)
                ax[0].add_patch(triangle)
                im.append(triangle)
            if robot_type == 'TWDH':
                vertices = calculate_inverted_triangle_vertices(robot_coodinate)
                triangle = Polygon(vertices, closed=True, color=robot_state.color, alpha=0.8)
                ax[0].add_patch(triangle)
                im.append(triangle)
            if robot_type == 'QWSH':
                vertices = calculate_rectangle_vertices(robot_coodinate)
                rect = Rectangle(vertices, rectangle_size, rectangle_size, color=robot_state.color, alpha=0.8)
                ax[0].add_patch(rect)
                im.append(rect)
            if robot_type == 'QWDH':
                vertices = calculate_pentagon_vertices(robot_coodinate)
                pentagon = Polygon(vertices, closed=True, color=robot_state.color, alpha=0.8)
                ax[0].add_patch(pentagon)
                im.append(pentagon)
            if robot_type == 'Dragon':
                ellipse = Ellipse(robot_coodinate, ellipse_size[0], ellipse_size[1], color=robot_state.color, alpha=0.8)
                ax[0].add_patch(ellipse)
                im.append(ellipse)
            if robot_type == 'Minimal':
                circle = Circle(robot_coodinate, circle_size, color=robot_state.color, alpha=0.8)
                ax[0].add_patch(circle)
                im.append(circle)
            # subplot2：スケジュール表のデータ保存
            scheduleBar[robot_state][r].append((t, 1.0))

        # subplot1：棒グラフ
        tasks = task_history[t]
        keys = [task.name for task in tasks.values()]
        colors = [color_map[type(task).__name__] for task in tasks.values()]
        height = [task.workload[0] - task.workload[1] for task in tasks.values()]
        bars = ax[2].bar(keys, height, color=colors)
        for bar in bars:
            im.append(bar)

        # subplot2：スケジュール表
        for r in range(len(robots)):
            for state, schedule in scheduleBar.items():
                im.append(ax[3].broken_barh(schedule[r], (r, 1), facecolors=state.value[1]))
        im.append(ax[3].axvline(x=t, color='white', linestyle='--'))  # 縦棒の追加

        # 各ターンの図を保管
        ims.append(im)
    # タスクが早めに終わった場合のデータ補完
    if t != max_step -1:
        for _ in range(10):
            ims.append(im)

    ani = animation.ArtistAnimation(fig, ims, blit=True, interval=2000)
    ani.save(file_name, writer="ffmpeg", fps=15, dpi=500)

    return ani


# In[10]:
#   変数
#       agent_history[] : クラスのインスタンス  ※出所不明
#       task_history[]  : クラスのインスタンス  ※出所不明
#   関数
#       save_animation(): アニメーション作成関数（mp4形式の動画ファイル作成）   # In[9]:

from IPython.display import HTML

agents = agent_history[-1]
tasks = task_history[-1]
agent_name_list = [agent.robot.name for agent in agents]
task_name_list = [task_name for task_name, data in tasks.items()]
ani = save_animation(agent_history, task_history, _ ,_, max_step, agent_name_list, task_name_list, 'without_break.mp4')
# HTML(ani.to_jshtml())

