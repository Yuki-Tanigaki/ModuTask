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
## simulator
## optimizer

# How to Use
## Run Tests
```
poetry run pytest -s
```

## Run mypy
```
poetry run mypy modutask/core/
```

## Run Simulation
```python
poetry run python modutask/simulator/launcher.py --property_file configs/quick_sample_000/property.yaml
```
-> output
```
Training scenarios average:
[42.25, 30.94960485235799, 17.559813204133135]
Varidate scenario evaluation:
[32.0, 30.46875, 49.46260387811635]
```

## Run Task-allocation
```python
poetry run python modutask/optimizer/task_allocation/task_sample_nsgaii.py --property_file configs/quick_sample_001/property.yaml
```

