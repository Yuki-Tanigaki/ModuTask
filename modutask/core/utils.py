from typing import Union
import numpy as np
import copy, logging
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)

def make_coodinate_to_tuple(
    coordinate: Union[tuple[float, float], np.ndarray, list],
) -> tuple[float, float]:
    """さまざまな2D座標フォーマットをTuple[float, float]に変換"""

    # NumPyの配列
    if isinstance(coordinate, np.ndarray):
        if coordinate.shape == (2,):
            return copy.deepcopy(tuple(map(float, coordinate)))
        else:
            raise_with_log(TypeError, f"Invalid coordinate shape: {coordinate.shape}. Expected shape (2,).")

    # リスト
    elif isinstance(coordinate, list):
        if len(coordinate) == 2:
            return copy.deepcopy(tuple(map(float, coordinate)))
        else:
            raise_with_log(TypeError, f"Invalid coordinate length: {len(coordinate)}. Expected length 2.")

    # NumPyのfloat64が含まれているタプル
    elif isinstance(coordinate, tuple):
        if len(coordinate) == 2 and all(
            isinstance(x, (float, int, np.float64)) for x in coordinate
        ):
            return copy.deepcopy(tuple(map(float, coordinate)))
        else:
            raise_with_log(TypeError, f"Invalid coordinate format: {coordinate}. Expected Tuple[float, float].")

    else:
        raise_with_log(TypeError, f"Invalid coordinate type: {type(coordinate)}. Expected Tuple[float, float] or np.ndarray.")
        