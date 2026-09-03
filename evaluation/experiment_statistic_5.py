import os
from scipy.stats import wilcoxon
import pandas as pd
import numpy as np

base_path = os.path.join(
    os.path.dirname(__file__),
    "Parameters and results"
)

low_path = os.path.join(base_path, "experiment_5_low.csv")
high_path = os.path.join(base_path, "experiment_5_high.csv")

tabla_bajo = pd.read_csv(low_path)
tabla_alto = pd.read_csv(high_path)

pe_bajo = tabla_bajo["PE_max"].values
pe_alto = tabla_alto["PE_max"].values

statistic, p_value = wilcoxon(pe_bajo, pe_alto, method="approx")

n = len(pe_bajo)
mean_W = n * (n + 1) / 4
std_W = np.sqrt(n * (n + 1) * (2 * n + 1) / 24)

z = (statistic - mean_W) / std_W
r = abs(z) / np.sqrt(n)

print(f"\nWilcoxon statistic: {statistic}")
print(f"p-value: {p_value}")
print(f"Z: {z}")
print(f"Effect size r: {r}")
 