import numpy as np
import matplotlib.pyplot as plt

normal = np.load("experiments/scores_normal.npy")
abnormal = np.load("experiments/scores_abnormal.npy")

print("Normal:", normal.mean(), normal.std())
print("Abnormal:", abnormal.mean(), abnormal.std())

plt.hist(normal, bins=50, alpha=0.6, label="Normal")
plt.hist(abnormal, bins=50, alpha=0.6, label="Abnormal")
plt.legend()
plt.savefig("experiments/score_distribution.png", dpi=150)
plt.close()

