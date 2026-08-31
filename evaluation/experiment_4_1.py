
import pandas as pd
import os
import sys
import argparse
import optuna
import json

# Experimento 3. Ejecutar con ajuste y sin ajuste de epsilon

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from clip_protocol.utils.utils import display_results, get_real_frequency
from clip_protocol.count_mean.private_cms_client import run_private_cms_client
from clip_protocol.hadamard_count_mean.private_hcms_client import run_private_hcms_client

def filter_dataframe(df):
    df.columns = ["user", "value"]
    return df

def run_command(e, k, m, df, privacy_method):
    if privacy_method == "PCMeS":
        _, _, df_estimated = run_private_cms_client(k, m, e, df)
    elif privacy_method == "PHCMS":
        _, _, df_estimated = run_private_hcms_client(k, m, e, df)
    return display_results(get_real_frequency(df), df_estimated)

def get_max_error_from_table(table):
    # Última columna, quitando '%' y convirtiendo a float
    percentage_errors = [float(row[-1].strip('%')) for row in table]
    return max(percentage_errors)

def optimize_e(k, m, df, e_r, privacy_level, error_value, tolerance, privacy_method):
    matching_trial = {"trial": None}

    def objective(trial):
        e = round(trial.suggest_float('e', 0.1, e_r, step=0.1), 4)
        table = run_command(e, k, m, df, privacy_method)
        max_error = get_max_error_from_table(table)

        trial.set_user_attr('table', table)
        trial.set_user_attr('e', e)
        trial.set_user_attr('max_error', max_error)

        if privacy_level == "high":
            objective_high = (error_value + tolerance)*100
            objective_low = (error_value-tolerance)*100
        elif privacy_level == "low":
            objective_high = (error_value-tolerance)*100
            objective_low = 0

        print("Error: ", max_error)
        if objective_high >= max_error > objective_low:
            matching_trial["trial"] = trial
            trial.study.stop()
        
        return round(abs(objective_high - max_error), 4)
        
    study = optuna.create_study(direction='minimize') 
    study.optimize(objective, n_trials=20)

    final_trial = matching_trial["trial"] or study.best_trial
            
    return final_trial.user_attrs['max_error'], final_trial.user_attrs['e']


def run_experiment_3(datasets, params):
    error_value = 0.05
    tolerance = 0.01
    # privacy_level = "high"
    privacy_level = "low"

    for method in ["PCMeS", "PHCMS"]:
        row_apple = {"Método": "Método de Apple"}
        row_clip = {"Método": "CLiP"}
        k = params[method]["k"]
        m = params[method]["m"]
        e_r = params[method]["e_r"]

        for size, df in datasets.items():
            df.columns = ["user", "value"]
            df = filter_dataframe(df)
            
            # Ejecutar sin ajuste de epsilon
            table = run_command(e_r, k, m, df, method)
            max_error = get_max_error_from_table(table)
            row_apple[size] = f"{e_r:.2f} / {max_error:.2f}"

            # Ejecutar con ajuste de epsilon
            pe_error, epsilon  = optimize_e(k, m, df, e_r, privacy_level, error_value, tolerance, method)
            row_clip[size] = f"{epsilon:.2f} / {pe_error:.2f}"
        
        df_result = pd.DataFrame([row_apple, row_clip])
        df_result.to_csv(f"table_experiment_3_{method}.csv", index=False)
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run scalability experiment")
    parser.add_argument("-f", type=str, required=True, help="Path to the input excel file")
    args = parser.parse_args()
    data_path = args.f # folder

    params_path = os.path.join(os.path.dirname(__file__), "figures", "experiment_2_params.json")
    with open(params_path, 'r') as f:
        params = json.load(f)

    distribution = input("📌 Enter the distribution 1/2/3/4: ")
    sizes = [3000, 4000, 5000, 6000, 7000]

    datasets = {}
    for size in sizes:
        pattern = f"SynLog-{size}-d{distribution}"
        file_path = os.path.join(args.f, pattern + ".xlsx")
        header = 1 if "Unnamed" in pd.read_excel(file_path, nrows=1).columns[0] else 0
        df = pd.read_excel(file_path, header=header)
        datasets[size] = df
        
    
    run_experiment_3(datasets, params)
