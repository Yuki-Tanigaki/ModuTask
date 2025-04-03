import numpy as np

_rng = np.random.default_rng()  # デフォルトGenerator

def get_rng() -> np.random.Generator:
    return _rng

def seed_rng(seed: int):
    global _rng
    _rng = np.random.default_rng(seed)
