from typing import Tuple, Union
from omegaconf import ListConfig
import numpy as np
import copy

def make_coodinate_to_tuple(coordinate: Union[Tuple[float, float], np.ndarray, list, ListConfig]) -> Tuple[float, float]:
    # `ListConfig` を `list` に変換
    if isinstance(coordinate, ListConfig):
        coordinate = list(coordinate)

    # NumPyの配列ならタプルに変換
    if isinstance(coordinate, np.ndarray):
        if coordinate.shape == (2,):  # 2要素の1次元配列か確認
            return copy.deepcopy(tuple(map(float, coordinate)))
        else:
            raise TypeError(f"Invalid coordinate shape: {coordinate.shape}. Expected shape (2,).")

    # リストの場合もタプルに変換
    elif isinstance(coordinate, list):
        if len(coordinate) == 2:
            return copy.deepcopy(tuple(map(float, coordinate)))
        else:
            raise TypeError(f"Invalid coordinate length: {len(coordinate)}. Expected length 2.")

    # NumPyのfloat64が含まれているタプルを処理
    elif isinstance(coordinate, tuple):
        if len(coordinate) == 2 and all(isinstance(x, (float, int, np.float64)) for x in coordinate):
            return copy.deepcopy(tuple(map(float, coordinate)))  # floatに変換
        else:
            raise TypeError(f"Invalid coordinate format: {coordinate}. Expected Tuple[float, float].")

    else:
        raise TypeError(f"Invalid coordinate type: {type(coordinate)}. Expected Tuple[float, float] or np.ndarray.")
