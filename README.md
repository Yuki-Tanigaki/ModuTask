# ModuTask: A optimization framework for Task Allocation in Modular Robots 
モジュラーロボットに対するタスクスケジューリング

# Basic Concepts
## core
シミュレーションに用いるコンポーネント
- タスク
- モジュール
- ロボット
- マップ
- リスクシナリオ
## io
コンポーネントデータのセーブロード
### input
- task
- task-dependency
- module_type
- module
- robot_type
- robot
- map
- risk_scenario
- task-priority
### output
- task
- task-dependency
- module_type
- module
- robot_type
- robot
- task-priority

# How to Use
## Run Simulation
```
poetry run python modutask/simulator/launcher.py --property_file configs/quick_sample/property.yaml --scenario scenario_00 --max_step 50
```
