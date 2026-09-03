import pandas as pd
import os

base_path = os.path.join(os.path.dirname(__file__), "Parameters and results")

table_1 = pd.read_csv(os.path.join(base_path, "table_experiment_4_runs_A.csv"))
table_2 = pd.read_csv(os.path.join(base_path, "table_experiment_4_runs_B.csv"))

table_2["repeat"] = table_2["repeat"] + table_1["repeat"].max() + 1

# Unificar los dos CSV
result = pd.concat([table_1, table_2], ignore_index=True)

# Ordenar
result = result.sort_values(by=["distribution", "dataset_size", "method", "repeat"]).reset_index(drop=True)

output_path = os.path.join(base_path, "table_experiment_4_runs_AB.csv")

result.to_csv(output_path, index=False)
