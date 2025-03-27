import yaml

# 各モジュール型に対応するデフォルトバッテリー値
DEFAULT_BATTERY = {
    "Body": 1,
    "Limb": 5,
    "EndE": 1,
    "Wheel": 15
}

def generate_modules_yaml(module_counts: dict, output_file: str = "module.yaml"):
    modules = {}
    for module_type, count in module_counts.items():
        for i in range(count):
            name = f"{module_type.lower()}_{i:02}"
            modules[name] = {
                "name": name,
                "module_type": module_type,
                "coordinate": [0.0, 0.0],
                "battery": DEFAULT_BATTERY.get(module_type, 1),
                "operating_time": 0.0
            }

    # YAMLファイルとして保存
    with open(output_file, "w") as f:
        yaml.dump(modules, f, allow_unicode=True, sort_keys=False)

    print(f"YAMLファイルを生成しました: {output_file}")

# 使用例
module_counts = {
    "Body": 5,
    "Limb": 30,
    "EndE": 10,
    "Wheel": 20
}

generate_modules_yaml(module_counts)
