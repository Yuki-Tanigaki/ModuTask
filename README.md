# ModuTask: A optimization framework for Task Allocation in Modular Robots 

# Basic Concepts
TBA

# How to Use
## Run Tests
```
poetry run pytest -s
```

## Run mypy
```
poetry run mypy modutask/core/
```

## Run Robot-Configuration
```python
poetry run python modutask/robot_configuration.py --property_file configs/robot_configuration_sample/property.yaml
```
-> output
```
NonD solutions:
Robots: Counter({'QWDH': 8})
Objectives: [-32.0, -24.0, -24.0, 0.0, 0.0]
Robots: Counter({'QWDH': 8})
Objectives: [-32.0, -24.0, -24.0, 0.0, 0.0]
Robots: Counter({'Dragon': 8})
Objectives: [-8.0, -32.0, -16.0, 0.0, 0.0]
Robots: Counter({'Dragon': 8})
Objectives: [-8.0, -32.0, -16.0, 0.0, 0.0]
Robots: Counter({'QWDH': 4, 'Dragon': 4})
Objectives: [-20.0, -28.0, -20.0, 0.0, 0.0]
Robots: Counter({'QWDH': 7, 'Dragon': 1})
Objectives: [-29.0, -25.0, -23.0, 0.0, 0.0]
Robots: Counter({'Dragon': 7, 'QWDH': 1})
Objectives: [-11.0, -31.0, -17.0, 0.0, 0.0]
Robots: Counter({'Dragon': 6, 'TWDH': 1, 'QWDH': 1})
Objectives: [-13.0, -30.0, -18.0, 0.0, 0.0]
Robots: Counter({'QWDH': 5, 'Dragon': 2, 'TWDH': 1})
Objectives: [-25.0, -26.0, -22.0, 0.0, 0.0]
Robots: Counter({'QWDH': 5, 'Dragon': 2, 'TWDH': 1})
Objectives: [-25.0, -26.0, -22.0, 0.0, 0.0]
```
and result files:
robot_"n_step".yaml

## Run Simulation
```python
poetry run python modutask/simulation_launcher.py --property_file configs/simulation_sample/property.yaml
```
-> output
```
Training scenarios average:
[42.25, 30.94960485235799, 17.559813204133135]
Varidate scenario evaluation:
[32.0, 30.46875, 49.46260387811635]
```
and result files:
task_"n_step".pkl

## Run Task-allocation
```python
poetry run python modutask/task_allocation.py --property_file configs/task_allocation_sample/property.yaml
```
-> output
```
NonD solutions:
Training: [61.5, 5.162223290086425, 17.559813204133135]
Varidation: [50.0, 16.0, 49.46260387811635]
Training: [61.5, 5.162223290086425, 17.559813204133135]
Varidation: [50.0, 16.0, 49.46260387811635]
Training: [20.25, 20.388260565386545, 17.559813204133135]
Varidation: [23.0, 23.53497164461248, 49.46260387811635]
Training: [17.0, 17.47965839100346, 19.350733254659993]
Varidation: [8.0, 0.0, 56.25]
Training: [17.0, 17.47965839100346, 19.350733254659993]
Varidation: [8.0, 0.0, 56.25]
Training: [58.75, 5.229645306924513, 19.350733254659993]
Varidation: [47.0, 12.675418741511995, 56.25]
Training: [23.5, 13.433492159225173, 19.350733254659993]
Varidation: [15.0, 30.0, 56.25]
Training: [26.25, 7.5637368799706, 17.559813204133135]
Varidation: [23.0, 11.058601134215502, 49.46260387811635]
Training: [49.75, 6.634131425080693, 17.559813204133135]
Varidation: [40.0, 18.75, 49.46260387811635]
Training: [37.25, 6.990091446268318, 19.350733254659993]
Varidation: [27.0, 19.204389574759944, 56.25]
```
