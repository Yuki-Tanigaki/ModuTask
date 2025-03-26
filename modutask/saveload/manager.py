from omegaconf import OmegaConf
from typing import Dict, List, Type
from collections import Counter
import numpy as np
import inspect
from modutask.core import *
 
def find_subclasses_by_name(base_class: Type) -> Dict[str, Type]:
    """
    指定された基底クラスのすべてのサブクラスを探索し、クラス名をキーとする辞書を返す。

    :param base_class: 基底クラス
    :return: クラス名をキー、クラスオブジェクトを値とする辞書
    """
    subclasses = {}
    for cls in base_class.__subclasses__():
        subclasses[cls.__name__] = cls  # クラス名 (__name__) をキーとして登録
    return subclasses

def get_class_init_args(cls):
    """クラスの __init__ メソッドの引数を取得"""
    signature = inspect.signature(cls.__init__)
    return [param for param in signature.parameters]

class DataManager:
    """ タスク、モジュール、ロボットのデータを管理するクラス """
    def __init__(self, config_files: Dict[str, str]):
        """
        設定ファイルを読み込み、データを管理する。

        :param config_files: 設定ファイルのパスを格納した辞書
        """
        self._task_config = OmegaConf.load(config_files["task"])
        self._module_type_config = OmegaConf.load(config_files["module_type"])
        self._robot_type_config = OmegaConf.load(config_files["robot_type"])
        self._module_config = OmegaConf.load(config_files["module"])
        self._robot_config = OmegaConf.load(config_files["robot"])
    
    def load(self):
        

