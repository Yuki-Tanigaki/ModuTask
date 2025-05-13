import os
import time
from typing import Counter
import numpy as np
import pandas as pd
import argparse, yaml, logging
from modutask.io.input import load_module_types, load_modules, load_robot_types, load_tasks
from modutask.io.output import save_tasks, save_module
from modutask.utils import raise_with_log
from datetime import datetime
import shutil

from phase_process import Phase_process 

logger = logging.getLogger(__name__)

def save_result_folder(prop, log_folder_name):
    # コピー元のパス
    results_folder_path = os.path.dirname(os.path.dirname(prop['results']['task']))
    src_dir = results_folder_path

    # コピー先のパス
    dst_dir = os.path.join(os.path.dirname(os.path.dirname(results_folder_path)), "logs", log_folder_name)

    print("フォルダコピーします。")
    print("src_dir:", src_dir)
    print("dst_dir:", dst_dir)

    # コピー先フォルダを作成（存在しない場合）
    os.makedirs(dst_dir, exist_ok=True)

    # # src_dir 配下の全てのファイル・ディレクトリをコピー
    for item in os.listdir(src_dir):
        s = os.path.join(src_dir, item)
        d = os.path.join(dst_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)  # Python 3.8以降
        else:
            shutil.copy2(s, d)

def select_phase_index(n_phases):
    while True:
        #モード選択初期化
        mode_select = False

        # 実行モードの選択（無効な入力は再入力を促す）
        while True:
            print("\n=== 実行モードを選んでください ===")
            print("1: すべてのフェーズを実行")
            print("2: 単独のフェーズを実行")
            print("3: 指定範囲のフェーズを実行（from～to）")
            print("c: キャンセル・終了")
            mode = input("モード番号（1〜3）または 'c' を入力：").strip().lower()
            if mode in ['1', '2', '3']:
                break
            elif mode == 'c':
                print("キャンセルされました。プログラムを終了します。")
                exit(0)
            else:
                print("エラー：無効なモードが選択されました。1〜3 または 'c' を入力してください。")

        # 実行対象のインデックス決定
        if mode == '1':
            start_idx = 0
            end_idx = n_phases - 1
            mode_select = True
        elif mode == '2':
            while True:
                user_input = input(f"実行したいフェーズのインデックスを入力（0～{n_phases-1}、キャンセルは 'c'）：").strip().lower()
                if user_input == 'c':
                    print("キャンセルされました。モード選択に戻ります。")
                    break
                if user_input.isdigit():
                    idx = int(user_input)
                    if 0 <= idx < n_phases:
                        start_idx = idx
                        end_idx = idx
                        mode_select = True
                        break
                    else:
                        print("エラー：インデックスが範囲外です。")
                else:
                    print("エラー：数値または 'c' を入力してください。")
            else:
                continue  # mode選択に戻る

        elif mode == '3':
            while True:
                start_input = input(f"開始インデックスを入力（0～{n_phases-1}、キャンセルは 'c'）：").strip().lower()
                if start_input == 'c':
                    print("キャンセルされました。モード選択に戻ります。")
                    break
                end_input = input(f"終了インデックスを入力（{start_input}～{n_phases-1}、キャンセルは 'c'）：").strip().lower()
                if end_input == 'c':
                    print("キャンセルされました。モード選択に戻ります。")
                    break

                if start_input.isdigit() and end_input.isdigit():
                    start_idx = int(start_input)
                    end_idx = int(end_input)
                    if not (0 <= start_idx < n_phases) or not (0 <= end_idx < n_phases):
                        print("エラー：インデックスが範囲外です。")
                    elif start_idx > end_idx:
                        print("エラー：開始インデックスが終了インデックスより大きいです。")
                    else:
                        mode_select = True
                        break
                else:
                    print("エラー：数値または 'c' を入力してください。")
            else:
                continue  # mode選択に戻る

        else:
            print("予期しないエラー：モードが不正です。")

        if mode_select == True:
            break  # インデックス指定ができたため終了
    return start_idx, end_idx

def main():
    """propertyファイル読み込み"""
    print("propertyファイル読み込みしています...")
    parser = argparse.ArgumentParser(description="Run the robotic system simulator.")
    parser.add_argument("--property_file", type=str, help="Path to the property file")
    args = parser.parse_args()

    try:
        with open(args.property_file, 'r') as f:
            prop = yaml.safe_load(f)
            print("...propertyファイル読み込み完了しました。")
    except FileNotFoundError as e:
        raise_with_log(FileNotFoundError, f"File not found: {e}.")

    # フェーズの定義
    phase0 = Phase_process(0)
    phase1 = Phase_process(1)
    phase2 = Phase_process(2)
    phases = [phase0, phase1, phase2]

    # フェーズの選択
    sw_menu = True
    # sw_menu = False
    if sw_menu == True:
        start_idx, end_idx = select_phase_index(len(phases))
    else:
        start_idx = 0
        end_idx = len(phases)

    # 実行日時取得
    log_folder_name = "log_" + datetime.now().strftime("%Y%m%d%H%M%S")

    save_result_folder(prop, log_folder_name)
    exit(1)

    """phase0,1,2を実行"""
    print(f'phase選択: {start_idx}から{end_idx}を実行します。')
    next_modules = None
    next_tasks = None
    module_types = load_module_types(file_path=prop['load']['module_type'])
    robot_types = load_robot_types(file_path=prop['load']['robot_type'], module_types=module_types)

    for phase_index in range(start_idx, end_idx + 1):
        print(f'### phase{phase_index} ################################')
        phase = phases[phase_index]
    
        #propertyデータ展開
        if phase_index == 0:
            modules = load_modules(file_path=prop['load']['module'], module_types=module_types) # ./configs/20250414/module.yaml
            tasks = load_tasks(file_path=prop["load"]["task"])                                  # ./configs/20250414/task.yaml

        elif phase_index > 0 and phase_index < len(phases):
            #前回phaseの実行結果の引継ぎ
            phase_index_before = phase_index - 1
            if phase_index_before < 0:
                print("予期しないエラー：phase_indexが不正です。:", phase_index_before)
                exit(3)
            template = prop['results']['module']                                # 例)./results/20250414/phase_{phase_index}/module.yaml
            modules_path = template.format(phase_index=phase_index_before)             # 例)./results/20250414/phase_1/module.yaml
            modules = load_modules(file_path=modules_path, module_types=module_types)

            template = prop['results']['task']                                  # 例)./results/20250414/phase_{phase_index}/task.yaml
            tasks_path = template.format(phase_index=phase_index_before)               # 例)./results/20250414/phase_1/task.yaml
            tasks = load_tasks(file_path=tasks_path)

        else:
            print("予期しないエラー：phase_indexが不正です。:", phase_index)
            exit(2)
            
        """ロボット構成最適化の実行"""
        print('ロボット構成最適化を実行しています...')
        all_data = phase.proc_robot_configuration(prop, module_types, modules, robot_types)

        #実行結果の保存
        df = pd.DataFrame(all_data)
        template = prop['results']['configuration']
        file_path = template.format(phase_index=phase_index)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        df.to_csv(file_path, index=False)

        """タスクアロケーションの実行"""
        print('タスクアロケーションを実行しています...')
        task_data, next_modules, next_tasks = phase.proc_task_allocation(prop, module_types, modules, robot_types, tasks)

        #実行結果の保存
        print("実行結果を保存しています...")
        task_df = pd.DataFrame(task_data)
        template = prop['results']['scheduling']
        file_path = template.format(phase_index=phase_index)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        task_df.to_csv(file_path, index=False)
        
        # taskとモジュールの状態を保存
        template = prop['results']['module']
        file_path = template.format(phase_index=phase_index)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        save_module(modules=next_modules, file_path=file_path)

        template = prop['results']['task']
        file_path = template.format(phase_index=phase_index)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        save_tasks(tasks=next_tasks, file_path=file_path)

        print(f'...phase{phase_index} が完了しました。')

    # 結果をログ保存
    save_result_folder(prop, log_folder_name)

if __name__ == '__main__':
    main()
