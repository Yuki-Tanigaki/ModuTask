import numpy as np
from collections import Counter
from modutask.core.module.module import Module, ModuleState
from modutask.core.robot.robot import Robot, RobotType, has_duplicate_module
from modutask.core.utils.coodinate_utils import is_within_range
from modutask.optimizer.my_moo.core.encoding import BaseVariable
from modutask.optimizer.my_moo.rng_manager import get_rng

class ConfigurationVariable(BaseVariable):
    def __init__(self, modules: dict[str, Module], robot_types: dict[str, RobotType], ):
        self.modules = modules
        self.robot_types = robot_types

    def sample(self) -> list[Robot]:
        """ランダムなロボット群を生成"""
        robots = []
        
        while True:
            new_robot = self.sample_robot(robots)
            if new_robot is None:
                break
            robots.append(new_robot)
        return robots

    def sample_robot(self, robots:list[Robot]) -> Robot:
        rng = get_rng()
        used_modules = []
        for robot in robots:
            used_modules.extend(robot.component_required)
        """ランダムなロボットを生成"""
        robot_type: RobotType = rng.choice(list(self.robot_types.values()))
        component = []
        for module_type, required_num in robot_type.required_modules.items():
            active_modules = []
            for module in self.modules.values():
                if module.type == module_type and module.state == ModuleState.ACTIVE and module not in used_modules:
                    active_modules.append(module)
            if len(active_modules) < required_num:
                return None
            module: list[Module] = rng.choice(active_modules, required_num, replace=False)
            component.extend(module)
            used_modules.extend(module)
        coordinates = [module.coordinate for module in component]
        most_common_coordinate, _ = Counter(coordinates).most_common(1)[0]
        return Robot(robot_type=robot_type, name="dummy", coordinate=most_common_coordinate, 
                        component=component)
    
    def clone_robots(self, value: list[Robot]) -> list[Robot]:
        clone = []
        for robot in value:
            robot_type = robot.type
            name = robot.name
            coordinate = robot.coordinate
            component = []
            for module in robot.component_required:
                module_name = module.name
                component.append(self.modules[module_name])
            clone.append(Robot(
                robot_type=robot_type,
                name=name,
                coordinate=coordinate,
                component=component
            ))
        return clone

    def mutate(self, value: list[Robot]) -> list[Robot]:
        """突然変異"""
        rng = get_rng()
        mutated = self.clone_robots(value)
        if not mutated:
            return mutated  # 空なら何もしない

        # ランダムなインデックスを1つ選んで削除
        idx = rng.integers(0, len(mutated))
        del mutated[idx]

        # 新しいロボットを生成して追加
        new_robot = self.sample_robot(mutated)
        if new_robot is not None:
            mutated.append(new_robot)
        return self.mutate_cross(mutated) # モジュール交叉を行う

    def mutate_cross(self, value: list[Robot]) -> list[Robot]:
        """任意のロボットを選択し、モジュールを交換する"""
        rng = get_rng()
        mutated = self.clone_robots(value)
        if len(mutated) == 1:
            return mutated # ロボットがひとつの場合交換不可能
        robots: list[Robot] = rng.choice(mutated, 2)
        r1, r2 = robots[0], robots[1]
        # それぞれのモジュールから同じtypeのものを探す
        type_pairs = [
            (m1, m2)
            for m1 in r1.component_required
            for m2 in r2.component_required
            if m1.type == m2.type and m1 != m2
        ]
        
        if not type_pairs:
            return mutated  # 同じタイプのモジュールがない場合は交換しない

        # 1組選んで交換
        m1, m2 = rng.choice(type_pairs)
        r1.component_required.remove(m1)
        r2.component_required.remove(m2)
        if m1 in r1.component_mounted:
            r1.component_mounted.remove(m1)
        if m2 in r2.component_mounted:
            r2.component_mounted.remove(m2)
        r1.component_required.append(m2)
        r2.component_required.append(m1)
        if is_within_range(m2.coordinate, r1.coordinate):
            r1.mount_module(m2)
        if is_within_range(m1.coordinate, r2.coordinate):
            r2.mount_module(m1)
        return mutated

    def crossover(self, value1: list[Robot], value2: list[Robot]) -> list[Robot]:
        # """交叉"""
        rng = get_rng()
        offspring = self.clone_robots(value1)
        opponent = self.clone_robots(value2)
        if not value1:
            return opponent
        elif not value2:
            return offspring

        # ランダムにロボット A を選ぶ
        robot_a: Robot = rng.choice(offspring)

        # 同じタイプのロボットを value2 から抽出
        same_type_candidates = [r for r in opponent if r.type == robot_a.type]

        if not same_type_candidates:
            return offspring  # 同タイプなし

        # ロボット B をランダムに選ぶ
        robot_b: Robot = rng.choice(same_type_candidates)

        # robot_a のインデックスを探して B に置き換え
        idx = offspring.index(robot_a)
        offspring[idx] = robot_b

        # AとBの component_required を比較して変化したモジュールを記録
        swap_map = {}
        candidate = robot_a.component_required[:]
        for mod_b in robot_b.component_required:
            if mod_b in candidate:
                candidate.remove(mod_b)
                continue
            temp = [mod_candidate for mod_candidate in candidate 
                    if mod_candidate.type == mod_b.type]
            mod_a = rng.choice(temp)
            swap_map[mod_b] = mod_a
            candidate.remove(mod_a)

        # 残りのロボットの component_required も置き換え候補があれば交換
        for i, robot in enumerate(offspring):
            if i == idx:
                continue  # 置き換え済みなのでスキップ
            for old_module, new_module in swap_map.items():
                if old_module in robot.component_required:
                    robot.component_required.remove(old_module)
                    robot.component_required.append(new_module)

                    if old_module in robot.component_mounted:
                        robot.component_mounted.remove(old_module)

                    if is_within_range(new_module.coordinate, robot.coordinate):
                        robot.mount_module(new_module)

        return offspring
    
    def validate(self, value: list[Robot]) -> bool:
        """全ロボットのモジュール名の重複なし"""
        all_module_names = []
        for robot in value:
            module_names = [module.name for module in robot.component_required]
            all_module_names.extend(module_names)

        duplicates = set(name for name in all_module_names if all_module_names.count(name) > 1)
        if duplicates:
            return False
        return True

    def __repr__(self):
        return f"ConfigurationVariable={self.modules}, {self.robot_types}"

    def equals(self, value1: list[Robot], value2: list[Robot]) -> bool:
        if len(value1) != len(value2):
            return False
        for r1, r2 in zip(value1, value2):
            if not self._robot_equal(r1, r2):
                return False
        return True
    
    def _robot_equal(self, r1: Robot, r2: Robot) -> bool:
        return (
            r1.type == r2.type and
            self._module_names_equal(r1.component_required, r2.component_required)
        )
    
    def _module_names_equal(self, mods1: list[Module], mods2: list[Module]) -> bool:
        names1 = [m.name for m in mods1]
        names2 = [m.name for m in mods2]
        return names1 == names2
    
    def hash(self, value: list[Robot]) -> int:
        hash_value = 0
        for robot in value:
            hash_value ^= hash(robot.type)
            for module in robot.component_required:
                hash_value ^= hash(module.name)
        return hash_value
