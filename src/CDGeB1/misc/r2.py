"""
sklearn's r2_score computes ***Coefficient of determination***,
while myR2 computes ***Pearson correlation coefficient***.

Prefer using CoD for evaluating linear model's performance (Y' vs Y),
and use Pearson for evaluating correlation between two variables (X vs Y).
"""

import numpy as np
from sklearn.metrics import r2_score

__all__ = ['r2_score', 'myR2']

def myR2(x, y):
    correlation_matrix = np.corrcoef(x, y)
    correlation_xy = correlation_matrix[0,1]
    r2 = correlation_xy ** 2
    return r2

"""
print(r2_score(Xs, Ys))         # -5.298
print(r2_score(Xs, Xs * slope)) # -5.298
print(r2_score(Ys, Xs * slope)) # 0.606 <- nice to have, linear model level

print(myR2(Xs, Ys))             # 0.644 <- nice to have, measurements level
print(myR2(Xs, Xs * slope))     # 1.0
print(myR2(Ys, Xs * slope))     # 0.644
"""
