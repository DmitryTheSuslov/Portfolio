import numpy as np
import math


def apk(actual, predicted, k = 10):
    k = min(k, len(predicted))
    s = 0
    for i in range(k):
        s += (sum(np.in1d(predicted[:i + 1], actual)) / (i + 1)) * int(predicted[i] in actual)
    
    return s / k

def mapk(actual, predicted, k = 10):
    s = 0
    n = len(actual)

    for i in range(n):
        s += apk(actual[i], predicted[i], k)

    return s / n

def DCG(predicted):
    return sum([rel / math.log(i + 1, 2) for i, rel in enumerate(predicted)])
