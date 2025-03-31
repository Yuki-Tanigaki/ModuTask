# ModuTask
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


# How to Use
## Run Simulation
```
poetry run python modutask/simulator/launcher.py --property_file configs/sample000/property.yaml --scenario scenario_00 --max_step 50
```