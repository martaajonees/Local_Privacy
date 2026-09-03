import pandas as pd
import os
import sys
import json
import argparse
import optuna

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from clip_protocol.utils.utils import get_real_frequency, display_results
from clip_protocol.count_mean.private_cms_client import run_private_cms_client
from clip_protocol.hadamard_count_mean.private_hcms_client import run_private_hcms_client

n_runs = 10
error_value = 0.05
privacy_level = "high"
tolerance = 0.01

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

def run_experiment_3(datasets, params):
    base_path = os.path.join(os.path.dirname(__file__), "Parameters and results")
    os.makedirs(base_path, exist_ok=True)
    output_path = os.path.join(base_path, "table_experiment_3.csv")

    all_results = []

    for distribution, df in datasets.items():
        df.columns = ["user", "value"]
        df = filter_dataframe(df)
 
        for method in ["PCMeS", "PHCMS"]:
            print(f"🔍 Executing {method} with the distribution {distribution}...")
 
            method_params = params[distribution][method]
            k = method_params["k"]
            m = method_params["m"]
            e = method_params["e"]
 
            run_tables = []
            for run_idx in range(n_runs):
                print(f"   ↪ Repetition {run_idx + 1}/{n_runs}")
                table = optimize_e(k, m, df, e, privacy_level, error_value, tolerance, method)
 
                filtered_table = [[row[0], row[-1]] for row in table]
                cleaned_table = [
                    [col[0], float(col[1].replace('%', '')) if isinstance(col[1], str) else float(col[1])]
                    for col in filtered_table
                ]
 
                run_df = pd.DataFrame(cleaned_table, columns=['AOI', 'Error'])
                run_df['run'] = run_idx
                run_tables.append(run_df)
 
            all_runs_df = pd.concat(run_tables, ignore_index=True)
 
            error_by_aoi = (
                all_runs_df.groupby('AOI', sort=False)['Error']
                .agg(Error='mean', Error_std='std')
                .reset_index()
            )
 
            error_by_aoi.insert(0, 'distribution', distribution)
            error_by_aoi.insert(1, 'method', method)
 
            all_results.append(error_by_aoi)
 
    final_df = pd.concat(all_results, ignore_index=True)
 
    final_df = final_df[['distribution', 'method', 'AOI', 'Error', 'Error_std']]
 
    final_df.to_csv(output_path, index=False, header=True)
    print(f"✅ Results saved in: {output_path}")
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run scalability experiment")
    parser.add_argument("-f", type=str, required=True, help="Path to the input excel folder")
    args = parser.parse_args()
    data_path = args.f # folder
 
    params_path = os.path.join(os.path.dirname(__file__), "Parameters and results", "params_experiment_3.json")
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
 
    run_experiment_3(datasets, params)
 