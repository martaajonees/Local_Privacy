import pandas as pd
import os
import sys
import json
import argparse
import optuna

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from clip_protocol.utils.utils import get_real_frequency, display_results
from clip_protocol.utils.errors import compute_error_table
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

def optimize_e(k, m, df, e_r, privacy_level, error_value, tolerance, privacy_method):
    matching_trial = {"trial": None}
    trial_counter = {"count": 0}

    def objective(trial):
        trial_counter["count"] += 1
        e = round(trial.suggest_float('e', 0.1, e_r, step=0.1), 4)
        table = run_command(e, k, m, df, privacy_method)

        percentage_errors = [float(row[-1].strip('%')) for row in table]
        max_error = max(percentage_errors)

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
            
    table = final_trial.user_attrs['table']
            
    return table

def run_experiment_4(datasets, params):
    error_value = 0.05
    privacy_level = "high"
    tolerance = 0.01

    for distribution, df in datasets.items():
        df.columns = ["user", "value"]
        df = filter_dataframe(df)

        for method in ["PCMeS", "PHCMS"]:
            print(f"🔍 Ejecutando {method} en distribución {distribution}...")

            method_params = params[distribution][method]
            k = method_params["k"]
            m = method_params["m"]
            e = method_params["e"]
            table = optimize_e(k, m, df, e, privacy_level, error_value, tolerance, method)

            filtered_table = [[row[0], row[-1]] for row in table]
            cleaned_table = [[col[0], col[1].replace('%', '') if isinstance(col[1], str) else col[1]] for col in filtered_table]

            error_by_aoi = pd.DataFrame(cleaned_table, columns=['AOI', 'Error'])
            path_individual = f"experimet_4_d{distribution}_{method}.csv"
            error_by_aoi.to_csv(path_individual, index=False)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run scalability experiment")
    parser.add_argument("-f", type=str, required=True, help="Path to the input excel file")
    args = parser.parse_args()
    data_path = args.f # folder

    params_path = os.path.join(os.path.dirname(__file__), "figures", "experiment_4_params.json")
    with open(params_path, 'r') as f:
        params = json.load(f)
    
    distributions = ["1", "2", "3", "4"]

    datasets = {}
    for distribution in distributions:
        pattern = f"SynLog-5000-d{distribution}"
        file_path = os.path.join(args.f, pattern + ".xlsx")
        header = 1 if "Unnamed" in pd.read_excel(file_path, nrows=1).columns[0] else 0
        df = pd.read_excel(file_path, header=header)
        datasets[distribution] = df  
    
    run_experiment_4(datasets, params)