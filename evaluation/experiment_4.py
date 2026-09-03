import argparse
import json
import os
import sys

import numpy as np
import optuna
import pandas as pd
from scipy import stats
from tqdm import tqdm

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from clip_protocol.utils.utils import display_results, get_real_frequency
from clip_protocol.count_mean.private_cms_client import run_private_cms_client

DISTRIBUTIONS = ["1", "2", "3", "4"]
DATASET_SIZES = [3000, 4000, 6000, 7000]

N_OPTUNA_TRIALS = 20
ERROR_VALUE = 0.05
TOLERANCE = 0.01
PRIVACY_LEVEL = "high"

# Number of repeated runs per (distribution, dataset_size, method)
N_REPEATS = 5
BASE_SEED = 42
CONFIDENCE_LEVEL = 0.95


def filter_dataframe(df):
    df.columns = ["user", "value"]
    return df


def run_client(epsilon, k, m, df, seed=None):
    if seed is not None:
        np.random.seed(seed)

    _, _, df_estimated = run_private_cms_client(k, m, epsilon, df)

    return display_results(get_real_frequency(df), df_estimated)


def get_max_error_from_table(table):
    percentage_errors = [float(row[-1].strip("%")) for row in table]
    return max(percentage_errors)


def optimize_epsilon(k, m, df, e_max, privacy_level, error_value, tolerance, seed=None):
    if privacy_level == "high":
        objective_high = (error_value + tolerance) * 100
        objective_low = (error_value - tolerance) * 100
    elif privacy_level == "low":
        objective_high = (error_value - tolerance) * 100
        objective_low = 0
    else:
        raise ValueError(f"Unknown privacy level: {privacy_level}")

    matching_trial = {"trial": None}
    all_trial_pes = []

    def objective(trial):
        epsilon = round(trial.suggest_float("e", 0.1, e_max, step=0.1), 4)
        table = run_client(epsilon, k, m, df, seed=seed)
        max_error = get_max_error_from_table(table)

        for pe_index, row in enumerate(table):
            all_trial_pes.append({
                "trial": trial.number,
                "epsilon": epsilon,
                "pe_index": pe_index,
                "PE": float(row[-1].strip("%"))
            })

        trial.set_user_attr("epsilon", epsilon)
        trial.set_user_attr("max_error", max_error)

        if objective_high >= max_error > objective_low:
            matching_trial["trial"] = trial
            trial.study.stop()

        return round(abs(objective_high - max_error), 4)

    sampler = optuna.samplers.TPESampler(seed=seed) if seed is not None else None
    study = optuna.create_study(direction="minimize", sampler=sampler)
    study.optimize(objective, n_trials=N_OPTUNA_TRIALS)

    final_trial = matching_trial["trial"] or study.best_trial
    return final_trial.user_attrs["epsilon"], final_trial.user_attrs["max_error"], all_trial_pes


def confidence_interval(values, confidence=CONFIDENCE_LEVEL):
    values = np.asarray(values, dtype=float)
    n = len(values)
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1)) if n > 1 else 0.0

    if n > 1:
        margin = stats.t.ppf((1 + confidence) / 2, df=n - 1) * std / np.sqrt(n)
    else:
        margin = 0.0

    return mean, std, mean - margin, mean + margin


def run_repeated(method_label, k, m, e_max, df, distribution, size, tuned):
    """
    `tuned=False` runs the Apple baseline at the fixed epsilon `e_max`.
    `tuned=True` runs CLiP's personalized-epsilon search via
    optimize_epsilon.
    """
    runs = []
    all_trial_pes = []

    for rep in range(N_REPEATS):
        seed = BASE_SEED + rep

        if tuned:
            epsilon, pe_max, all_trial_pes_i = optimize_epsilon(
                k, m, df, e_max, PRIVACY_LEVEL, ERROR_VALUE, TOLERANCE, seed=seed
            )
            for pe in all_trial_pes_i:
                pe.update({
                    "distribution": f"d{distribution}",
                    "dataset_size": size,
                    "method": method_label,
                    "repeat": rep,
                    "seed": seed
                })

            all_trial_pes.extend(all_trial_pes_i)
        else:
            table = run_client(e_max, k, m, df, seed=seed)
            epsilon, pe_max = e_max, get_max_error_from_table(table)


        runs.append({
            "distribution": f"d{distribution}",
            "dataset_size": size,
            "method": method_label,
            "repeat": rep,
            "epsilon": epsilon,
            "PE_max": pe_max,
            "seed": seed
        })

    return runs, all_trial_pes


def aggregate_runs(runs_df):
    """Collapse per-run records into mean/std/95% CI per
    (distribution, dataset_size, method) combination."""
    rows = []
    group_cols = ["distribution", "dataset_size", "method"]

    for keys, group in runs_df.groupby(group_cols):
        distribution, size, method = keys

        eps_mean, eps_std, eps_lo, eps_hi = confidence_interval(group["epsilon"])
        pe_mean, pe_std, pe_lo, pe_hi = confidence_interval(group["PE_max"])

        rows.append({
            "distribution": distribution,
            "dataset_size": size,
            "method": method,
            "n_repeats": len(group),
            "epsilon_mean": round(eps_mean, 4),
            "epsilon_std": round(eps_std, 4),
            "epsilon_ci95_low": round(eps_lo, 4),
            "epsilon_ci95_high": round(eps_hi, 4),
            "PE_max_mean": round(pe_mean, 4),
            "PE_max_std": round(pe_std, 4),
            "PE_max_ci95_low": round(pe_lo, 4),
            "PE_max_ci95_high": round(pe_hi, 4),
        })

    return pd.DataFrame(rows).sort_values(group_cols).reset_index(drop=True)


def run_for_distribution(distribution, datasets, params, output_dir):
    """Run Apple (fixed epsilon) vs CLiP (tuned epsilon) for every dataset
    size, for a single distribution, each repeated N_REPEATS times.

    Returns (raw_runs_df, summary_df), both long-format with a
    'distribution' column.
    """
    all_runs = []
    all_trial_pes = []

    method_params = params[distribution]
    k = method_params["k"]
    m = method_params["m"]
    e_max = method_params["e"]

    total_runs = len(datasets) * 2 * N_REPEATS

    with tqdm(
        total=total_runs,
        desc=f"Distribución d{distribution}",
        unit="run"
    ) as pbar:

        for size, raw_df in datasets.items():
            df = filter_dataframe(raw_df.copy())

            # Apple: fixed epsilon
            pbar.set_postfix(
                dataset=size,
                method="Apple"
            )

            runs, trial_pes = run_repeated(
                "Apple", k, m, e_max, df,
                distribution, size, tuned=False,
            )

            all_runs.extend(runs)
            all_trial_pes.extend(trial_pes)

            pbar.update(N_REPEATS)

            #CLiP: tuned epsilon
            pbar.set_postfix(
                dataset=size,
                method="CLiP"
            )

            runs, trial_pes = run_repeated(
                "CLiP-tuned", k, m, e_max, df,
                distribution, size, tuned=True,
            )

            all_runs.extend(runs)
            all_trial_pes.extend(trial_pes)

            pbar.update(N_REPEATS)

    runs_df = pd.DataFrame.from_records(all_runs)
    summary_df = aggregate_runs(runs_df)

    raw_path = os.path.join(output_dir, f"table_experiment_4_d{distribution}_raw_runs.csv")
    summary_path = os.path.join(output_dir, f"table_experiment_4_d{distribution}.csv")

    runs_df.to_csv(raw_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    

    print(f"Saved: {raw_path}")
    print(f"Saved: {summary_path}")
    

    return runs_df, summary_df


def run_experiment_4(all_datasets, params, output_dir="."):
    """Run the full experiment across DISTRIBUTIONS and save consolidated
    raw-runs and summary CSVs covering d1-d4."""
    os.makedirs(output_dir, exist_ok=True)

    all_runs, all_summaries = [], []
    for distribution in DISTRIBUTIONS:
        print(f"Running experiment for distribution d{distribution} "
              f"({N_REPEATS} repeats per combination)...")
        runs_df, summary_df = run_for_distribution(distribution, all_datasets[distribution], params, output_dir)
        all_runs.append(runs_df)
        all_summaries.append(summary_df)

    consolidated_runs = pd.concat(all_runs, ignore_index=True)
    consolidated_summary = pd.concat(all_summaries, ignore_index=True)

    runs_path = os.path.join(output_dir, "table_experiment_4_consolidated_raw_runs.csv")
    summary_path = os.path.join(output_dir, "table_experiment_4_consolidated.csv")
    consolidated_runs.to_csv(runs_path, index=False)
    consolidated_summary.to_csv(summary_path, index=False)
    print(f"Saved consolidated raw runs (d1-d4): {runs_path}")
    print(f"Saved consolidated summary (d1-d4, mean/std/95% CI): {summary_path}")

    return consolidated_runs, consolidated_summary


def load_datasets(data_folder, distribution):
    """Load the SynLog Excel file for every dataset size, for one distribution."""
    datasets = {}
    for size in DATASET_SIZES:
        file_name = f"SynLog-{size}-d{distribution}.xlsx"
        file_path = os.path.join(data_folder, file_name)

        header = 1 if "Unnamed" in pd.read_excel(file_path, nrows=1).columns[0] else 0
        datasets[size] = pd.read_excel(file_path, header=header)

    return datasets


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run Experiment 4: CLiP vs Apple across dataset sizes, for d1-d4"
    )
    parser.add_argument("-f", type=str, required=True, help="Path to the folder with the input Excel files")
    parser.add_argument("-o", type=str, default=".", help="Output directory for result CSVs")
    args = parser.parse_args()

    params_path = os.path.join(os.path.dirname(__file__), "Parameters and results", "params_experiment_4.json")
    with open(params_path, "r") as f:
        params = json.load(f)

    all_datasets = {
        distribution: load_datasets(args.f, distribution)
        for distribution in DISTRIBUTIONS
    }

    run_experiment_4(all_datasets, params, output_dir=args.o)