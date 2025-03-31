from typing import Union
from numpy.typing import NDArray
import numpy as np
import logging
from modutask.utils import raise_with_log

logger = logging.getLogger(__name__)

def make_coodinate_to_tuple(
    coordinate: Union[tuple[float, float], NDArray[np.float64], list[float]],
) -> tuple[float, float]:
    """さまざまな2D座標フォーマットをTuple[float, float]に変換"""

    # NumPyの配列
    if isinstance(coordinate, np.ndarray):
        if coordinate.shape == (2,):
            x, y = coordinate
            return (float(x), float(y))
        else:
            raise_with_log(TypeError, f"Invalid coordinate shape: {coordinate.shape}. Expected shape (2,).")

    # リスト
    elif isinstance(coordinate, list):
        if len(coordinate) == 2:
            x, y = coordinate
            return (float(x), float(y))
        else:
            raise_with_log(TypeError, f"Invalid coordinate length: {len(coordinate)}. Expected length 2.")

    # NumPyのfloat64が含まれているタプル
    elif isinstance(coordinate, tuple):
        if len(coordinate) == 2 and all(
            isinstance(x, (float, int, np.float64)) for x in coordinate
        ):
            x, y = coordinate
            return (float(x), float(y))
        else:
            raise_with_log(TypeError, f"Invalid coordinate format: {coordinate}. Expected Tuple[float, float].")

    else:
        raise_with_log(TypeError, f"Invalid coordinate type: {type(coordinate)}. Expected Tuple[float, float] or np.ndarray.")
        