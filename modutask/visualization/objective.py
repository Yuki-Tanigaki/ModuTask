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

    # 3目的以上: ペアごとの散布図
    else:
        plot_objective_matrix(objectives, file_path, labels)


def plot_objective_matrix(objectives: list[list[float]], file_path: str, labels: list[str] = None):
    """
    NxNの目的関数ペア散布図マトリクスを表示（対角線は空白）

    Parameters:
    - objectives: 各個体の目的関数値のリスト（形: [[f1, f2, ..., fn], ...]）
    - labels: 各目的の名前（例: ['Time', 'Cost', 'Energy']）デフォルトは 'f1', 'f2', ...
    """
    objectives = np.array(objectives)
    num_obj = objectives.shape[1]

    if labels is None:
        labels = [f"f{i+1}" for i in range(num_obj)]

    fig, axes = plt.subplots(num_obj, num_obj + 1, figsize=(4 * (num_obj + 1), 4 * num_obj))
    fig.subplots_adjust(wspace=0.3, hspace=0.3, top=0.92)

    for i in range(num_obj):
        for j in range(num_obj):
            ax = axes[i, j + 1]  # +1で1列目（j=0）はラベル用に空ける

            if i >= j:
                ax.axis('off')
                continue

            ax.scatter(objectives[:, j], objectives[:, i], alpha=0.6)

            if i == 0:
                ax.set_title(labels[j], fontsize=12)

            ax.set_xticks([])
            ax.set_yticks([])
            ax.grid(True)

    for j in range(0, num_obj):
        ax_label = axes[j, 0]  # j-1行目の左
        ax_label.axis('off')
        ax_label.text(0.5, 0.5, labels[j], fontsize=12, rotation=90,
                      va='center', ha='center', transform=ax_label.transAxes)

    for i in range(num_obj):
        axes[i, 0].axis('off')

    fig.suptitle("Objective Scatter Matrix", fontsize=18)
    plt.savefig(file_path)
    plt.close(fig)