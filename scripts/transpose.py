import numpy as np

def main(data: np.ndarray, params : dict) -> np.ndarray:
    return np.array(data).transpose()

def config():
    return {
        "name" : "Transpose",
        "shape" : None,
        "multiply" : False,
        "inputParams" : {}
        }