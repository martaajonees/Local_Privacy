
import os
import pandas as pd
from scipy.stats import wilcoxon

base_path = os.path.join(os.path.dirname(__file__), "Parameters and results")

df = pd.read_csv(os.path.join(base_path, "table_experiment_4_runs.csv"))

METRIC = "PE_max"
#METRIC = "epsilon"
ALPHA = 0.05

results = []

for dist, group in df.groupby("distribution"):
    methods = group["method"].unique()

    m1, m2 = methods

    pivot = group.pivot_table(
        index=["dataset_size", "repeat"], columns="method", values=METRIC
    )
    pivot = pivot.dropna(subset=[m1, m2])  # nos quedamos solo con pares completos
 
    x = pivot[m1]
    y = pivot[m2]
 
    stat, p_value = wilcoxon(x, y, alternative="two-sided", method="approx", zero_method="wilcox")
    z_stat = wilcoxon(x, y, alternative="two-sided", method="approx", zero_method="wilcox").zstatistic
 
    n_pares = len(pivot)
    r_effect_size = abs(z_stat) / (n_pares ** 0.5)

    results.append({
        "distribution": dist,
        "method_1": m1,
        "method_2": m2,
        "W_statistic": stat,
        "Z_statistic": z_stat,
        "p_value": p_value,
        "r_effect_size": r_effect_size,
        "reject_H0 (p<0.05)": p_value < ALPHA,
    })

results_df = pd.DataFrame(results).sort_values("distribution").reset_index(drop=True)

output_path = os.path.join(base_path, "table_mannwhitney.csv")
results_df.to_csv(output_path, index=False)
