import numpy as np
import logging

def main(data: np.ndarray, params : dict) -> np.ndarray:
    return np.delete(np.array(data), params["index"], axis=0)

def config():
    return {
        "name" : "Del line",
        "shape" : [2],
        "multiply" : False,
        "inputParams" : {"index" : int}
        }