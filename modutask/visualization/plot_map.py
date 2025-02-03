import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
import matplotlib.ticker as ticker

# Plotting the 2D map
def plot_map(map_config, save_dir=None):
    fig, ax = plt.subplots()
    ax.set_xlim(map_config.xlim)
    ax.set_ylim(map_config.ylim)

    # Loop through each workplace and plot
    handles = []
    for name in map_config.workplace.keys():
        wp = map_config.workplace[name]
        coord = wp.coordinate
        color = wp.color
        c = patches.Circle(xy=(coord[0], coord[1]), radius=wp.size, fc=color, ec=color, label=name)
        handles.append(patches.Circle(xy=(0, 0), radius=0.1, fc=color, ec=color, label=name))
        ax.add_patch(c)
        ax.text(coord[0] + 0.1, coord[1] + 0.1, name, fontsize=12)

    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    ax.set_title('2D Map')

    # Add a legend
    ax.legend(handles=handles)
    # Set aspect ratio to 'equal' to make the plot square
    ax.set_aspect('equal')
    # plt.grid(True)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    if save_dir:
        image_file = os.path.join(save_dir, 'map.png')
        plt.savefig(image_file)
    plt.close()

# Plotting the task bar
def plot_task(tasks, save_dir=None):
    # カラーマップを用意する
    color_map = {
        'Transport': 'blue',
        'Manufacture': 'green'
    }
    # 横軸はタスクのキー、縦軸は required_workload
    task_keys = list(tasks.keys())
    workloads = np.array([task.required_workload for task in tasks.values()])
    current_progress = np.array([task.current_progress for task in tasks.values()])
    left_workloads = workloads - current_progress
    # 各要素が0より小さくならないようにする
    left_workloads = np.maximum(left_workloads, 0)
    # タスクごとの色を決定
    colors = [color_map[task.__class__.__name__] for task in tasks.values()]

    # 棒グラフを作成
    plt.figure(figsize=(8, 6))
    plt.bar(task_keys, left_workloads, color=colors)

    # グラフにラベルを付ける
    plt.xlabel('Tasks')
    plt.ylabel('Required Workload')
    plt.title('Required Workload for Each Task')
    # 凡例を追加
    handles = [plt.Rectangle((0,0),1,1, color=color_map[cat]) for cat in color_map]
    labels = list(color_map.keys())
    plt.legend(handles, labels)
    # グラフを表示
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    if save_dir:
        image_file = os.path.join(save_dir, 'task.png')
        plt.savefig(image_file)
    plt.close()

# Plotting the task bar
def plot_module(map_config, modules, save_dir=None):
    xlim = map_config.xlim
    ylim = map_config.ylim
    bins = (25, 25)
    # モジュールの座標データを抽出
    coordinates = [module.coordinate for module in modules.values()]

    # ヒートマップのための2Dヒストグラムを作成
    x_coords = [coord[0] for coord in coordinates]
    y_coords = [coord[1] for coord in coordinates]

    # ヒートマップの範囲を定義
    heatmap, xedges, yedges = np.histogram2d(x_coords, y_coords, bins=bins, range=[xlim, ylim])

    # ヒートマップをプロット
    plt.figure(figsize=(8, 6))
    plt.imshow(heatmap.T, origin='lower', cmap='copper', interpolation='nearest', extent=[xlim[0], xlim[1], ylim[0], ylim[1]])

    # ラベルを設定
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.title('Heatmap of Module Locations')

    # カラーバーを追加
    plt.colorbar(label='Number of Modules')

    # ヒートマップを表示
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    if save_dir:
        image_file = os.path.join(save_dir, 'module.png')
        plt.savefig(image_file)
    plt.close()

def plot_objective_space(objectives, nond_o, objective_name, save_dir=None):
    objectives = pd.DataFrame(objectives, columns=objective_name)
    nond_o = pd.DataFrame(nond_o, columns=objective_name)

    concat = pd.concat([objectives, nond_o])
    solution_type1 = [0 for i in range(objectives.shape[0])]
    solution_type2 = [1 for i in range(nond_o.shape[0])]

    def minmax_norm(df_input):
        return (df_input - df_input.min()) / (df_input.max() - df_input.min())
    df_minmax_norm = minmax_norm(concat)
    df_minmax_norm = df_minmax_norm.fillna(0) # 正規化でNaNが出たとき0に置き換え

    # Define colors for each solution type
    colors = ['blue', 'orange']
    color_labels = solution_type1 + solution_type2
    color_map = [colors[c] for c in color_labels]

    #散布図行列の描画
    plt.figure() #グラフを描く領域の作成
    scatter = pd.plotting.scatter_matrix(
        df_minmax_norm, #説明変数
        diagonal=None, #ヒストグラム無し
        c=color_map, #色分け
        figsize = (10, 10), #図の大きさ
        marker = 'o', #マーカーの種類
        edgecolors='black'
    )

    # Add legend
    legend_labels = ['Objectives', 'Non-Dominated']
    for color, label in zip(colors, legend_labels):
        plt.scatter([], [], c=color, label=label, marker='o', edgecolors='black')
    plt.legend(loc="upper right")

    # Set number format for axis tick labels in each subplot
    for ax in scatter.ravel():
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:.2f}'))
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f'{y:.2f}'))

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    if save_dir:
        image_file = os.path.join(save_dir, 'objective_space.png')
        plt.savefig(image_file)
    plt.close()