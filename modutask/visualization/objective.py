import os
import matplotlib.pyplot as plt
import itertools
import numpy as np

def plot_objective_scatter(objectives: list[list[float]], file_path: str, labels: list[str] = None):
    """
    N目的の目的関数に対する散布図を描く（3次元以上はペアごとの散布図を並べる）

    Parameters:
    - objectives: 各個体の目的関数値のリスト（形: [[f1, f2, ..., fn], ...]）
    - labels: 各目的の名前（例: ['Time', 'Cost', 'Energy']）デフォルトは 'f1', 'f2', ...
    """
    objectives = np.array(objectives)
    num_obj = objectives.shape[1]
    
    if labels is None:
        labels = [f"f{i+1}" for i in range(num_obj)]
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # 2目的: 単一の散布図
    if num_obj == 2:
        plt.figure(figsize=(5, 5))
        plt.scatter(objectives[:, 0], objectives[:, 1], alpha=0.7)
        plt.xlabel(labels[0])
        plt.ylabel(labels[1])
        plt.title("Objective Scatter Plot")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(file_path)
        plt.close()

    # 3目的以上: ペアごとの散布図を並べる
    else:
        plot_objective_matrix(objectives, file_path, labels)


def plot_objective_matrix(objectives: list[list[float]], file_path: str, labels: list[str] = None):
    """
    NxNの目的関数ペア散布図マトリクスを表示（対角線は空白）

    Parameters:
    - objectives: 各個体の目的関数値のリスト（形: [[f1, f2, ..., fn], ...]）
    - labels: 各目的の名前（例: ['Time', 'Cost', 'Energy']）デフォルトは 'f1', 'f2', ...
    """
    # objectives = np.array(objectives)
    # num_obj = objectives.shape[1]
    
    # if labels is None:
    #     labels = [f"f{i+1}" for i in range(num_obj)]

    # fig, axes = plt.subplots(num_obj, num_obj, figsize=(4 * num_obj, 4 * num_obj))

    # for i in range(num_obj):
    #     for j in range(num_obj):
    #         ax = axes[i, j]

    #         if i >= j:
    #             # 対角線・左下は非表示
    #             ax.axis('off')
    #         else:
    #             ax.scatter(objectives[:, j], objectives[:, i], alpha=0.6)
    #             # 上にラベル（X軸）
    #             if i == 0:
    #                 ax.set_title(labels[j], fontsize=12)

    #             # 右にラベル（Y軸）
    #             if j == num_obj - 1:
    #                 ax.yaxis.set_label_position("left")
    #                 ax.set_ylabel(labels[j], fontsize=12, rotation=0, labelpad=30, va='center')
    #                 # shown_column_labels.add(j)
                    

    #             # 軸目盛りは消す（美化）
    #             ax.set_xticks([])
    #             ax.set_yticks([])

    #             ax.grid(True)

    # fig.suptitle("Upper Triangle Objective Scatter Matrix", fontsize=18)
    # plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    objectives = np.array(objectives)
    num_obj = objectives.shape[1]

    if labels is None:
        labels = [f"f{i+1}" for i in range(num_obj)]

    fig, axes = plt.subplots(num_obj, num_obj, figsize=(4 * num_obj, 4 * num_obj))
    fig.subplots_adjust(left=0.1, right=0.95, top=0.92, wspace=0.4, hspace=0.4)

    col_positions = {}  # j: (x_center, y_top, y_bottom)

    for i in range(num_obj):
        for j in range(num_obj):
            ax = axes[i, j]

            if i >= j:
                ax.axis('off')
                continue

            ax.scatter(objectives[:, j], objectives[:, i], alpha=0.6)

            if i == 0:
                ax.set_title(labels[j], fontsize=12)

            if j not in col_positions:
                bbox = ax.get_position()
                col_positions[j] = {
                    "x": (bbox.x0 + bbox.x1) / 2,
                    "y_top": bbox.y1,
                    "y_bot": bbox.y1,
                }
            else:
                bbox = ax.get_position()
                col_positions[j]["y_bot"] = bbox.y0  # 更新していく

            ax.set_xticks([])
            ax.set_yticks([])
            ax.grid(True)

    # 正しい位置にラベルを fig.text で描画
    for j in range(1, num_obj):  # f1列は除く
        center = col_positions[j]
        y_middle = (center["y_top"] + center["y_bot"]) / 2
        x_left = center["x"] - 0.06  # 近づける（調整可）

        fig.text(x_left, y_middle, labels[j], rotation=90,
                 va='center', ha='center', fontsize=12)

    fig.suptitle("Objective Scatter Matrix", fontsize=18)
    plt.savefig(file_path)
    plt.close(fig)