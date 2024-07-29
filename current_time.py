
import time
import numpy as np

def current_time_sec():
    return time.time()

def current_time_millis():
    return np.int64(time.time() * 1000)

