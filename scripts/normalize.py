import numpy as np
import logging

def main(data: np.ndarray, params : dict) -> np.ndarray:
    if len(data.shape) == 2: 
        min_val = np.min(data, axis=1, keepdims=True)
        max_val = np.max(data, axis=1, keepdims=True)
    else:
        min_val = np.min(data)
        max_val = np.max(data)
    return (data - min_val) / np.maximum(max_val - min_val, 1e-12)

def config():
    return {
        "name" : "Normalize",
        "shape" : [1, 2],
        "multiply" : False,
        "inputParams" : {}
        }