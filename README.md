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
poetry run python optimize_configuration.py --property_file configs/optimize_configuration_sample/property.yaml
```

## Run Task-allocation
```python
poetry run python modutask/task_allocation.py --property_file configs/task_allocation_sample/property.yaml
```


## Run Simulation
```python
poetry run python simulation_launcher.py --property_file configs/simulation_sample/property.yaml
```

