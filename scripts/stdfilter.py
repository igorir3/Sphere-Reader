import numpy as np

def main(data: np.ndarray, params : dict) -> np.ndarray:
    window = params["window size"]
    data = np.asarray(data)

    if data.ndim not in (1, 2):
        raise ValueError("Ожидается 1D или 2D numpy-массив")

    def std_filter(array: np.ndarray) -> np.ndarray:
        pad = window // 2

        padded = np.pad(array, pad, mode="edge")
        windows = np.lib.stride_tricks.sliding_window_view(
            padded,
            window_shape=window
        )

        return np.std(windows, axis=-1)[:array.shape[0]]

    if data.ndim == 1:
        return std_filter(data)

    return np.array([
        std_filter(row)
        for row in data
    ])

def config():
    return {
        "name" : "STD Filter",
        "shape" : [1, 2],
        "multiply" : False,
        "inputParams" : {"window size" : int}
        }