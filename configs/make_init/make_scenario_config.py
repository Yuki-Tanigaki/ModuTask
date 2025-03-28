import yaml
import random

def load_module_names(modules_yaml_path: str) -> list:
    """ modules.yaml からモジュール名一覧を読み込む """
    with open(modules_yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    return list(data.keys())

def generate_random_thresholds(module_names: list, min_threshold: int = 10, max_threshold: int = 100) -> dict:
    """ モジュール名ごとにランダムな閾値（整数）を割り当てる """
    return {name: float(random.randint(min_threshold, max_threshold)) for name in module_names}

def generate_scenario_yaml(thresholds: dict, output_file: str = "scenario.yaml"):
    scenario_data = {
        "scenario": {
            "class": "TimeBasedScenario",
            "thresholds": thresholds
        }
    }
    with open(output_file, "w") as f:
        yaml.dump(scenario_data, f, allow_unicode=True, sort_keys=False)
    print(f"YAMLファイルを生成しました: {output_file}")

# 使用例
module_names = load_module_names("configs/sample000/module.yaml")
thresholds = generate_random_thresholds(module_names, min_threshold=10, max_threshold=60)
generate_scenario_yaml(thresholds)
