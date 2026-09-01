import argparse
import os
 
import pandas as pd
from scipy import stats
 
ALPHA = 0.05
 
 
def compare_group(baseline_values, tuned_values):
    """Run a two-sided Mann-Whitney U test between two independent samples
    of PE_max values. Returns a dict with the test outcome."""
    if len(baseline_values) < 1 or len(tuned_values) < 1:
        return None
 
    statistic, p_value = stats.mannwhitneyu(
        baseline_values, tuned_values, alternative="two-sided"
    )
 
    return {
        "n_baseline": len(baseline_values),
        "n_tuned": len(tuned_values),
        "baseline_median_PE_max": round(float(pd.Series(baseline_values).median()), 4),
        "tuned_median_PE_max": round(float(pd.Series(tuned_values).median()), 4),
        "U_statistic": round(float(statistic), 4),
        "p_value": round(float(p_value), 6),
        "significant_at_0.05": bool(p_value < ALPHA),
    }
 
 
def run_analysis(df, baseline_label, tuned_label):
    """Compute Mann-Whitney U per distribution (pooling dataset sizes and
    repeats), plus one overall test pooling every distribution together."""
    rows = []
 
    for distribution, group in df.groupby("distribution"):
        baseline_vals = group.loc[group["method"] == baseline_label, "PE_max"]
        tuned_vals = group.loc[group["method"] == tuned_label, "PE_max"]
 
        result = compare_group(baseline_vals, tuned_vals)
        if result is not None:
            result["distribution"] = distribution
            rows.append(result)
 
    # Overall test pooling all distributions together.
    baseline_vals = df.loc[df["method"] == baseline_label, "PE_max"]
    tuned_vals = df.loc[df["method"] == tuned_label, "PE_max"]
    overall = compare_group(baseline_vals, tuned_vals)
    if overall is not None:
        overall["distribution"] = "Overall (d1-d4 pooled)"
        rows.append(overall)
 
    columns = [
        "distribution", "n_baseline", "n_tuned",
        "baseline_median_PE_max", "tuned_median_PE_max",
        "U_statistic", "p_value", "significant_at_0.05",
    ]
    return pd.DataFrame(rows)[columns]
 
 
def to_latex(results_df, baseline_label, tuned_label):
    """Build a booktabs-style LaTeX table ready to paste into the paper."""
    lines = []
    lines.append(r"\begin{table}[t]")
    lines.append(r"\centering")
    lines.append(
        r"\caption{Mann-Whitney $U$ test comparing the fixed-epsilon baseline "
        rf"(\textit{{{baseline_label}}}) against CLiP's personalized-epsilon "
        rf"tuning (\textit{{{tuned_label}}}) on $PE_{{max}}$ (\%), pooled across "
        r"repetitions. Distributions d1--d4 are tested individually and pooled."
    )
    lines.append(r"\label{tab:mannwhitney_experiment4}")
    lines.append(r"\begin{tabular}{lccccccc}")
    lines.append(r"\toprule")
    lines.append(
        r"Distribution & $n$ (baseline) & $n$ (tuned) & "
        r"$\widetilde{PE}_{max}$ baseline (\%) & $\widetilde{PE}_{max}$ tuned (\%) & "
        r"$U$ & $p$-value & Sig. ($\alpha=0.05$) \\"
    )
    lines.append(r"\midrule")
 
    for _, row in results_df.iterrows():
        sig = r"\checkmark" if row["significant_at_0.05"] else r"--"
        p_display = f"{row['p_value']:.4f}" if row["p_value"] >= 0.0001 else "$<0.0001$"
        label = row["distribution"]
        if label.startswith("Overall"):
            lines.append(r"\midrule")
            label = r"\textbf{" + label + "}"
 
        lines.append(
            f"{label} & {row['n_baseline']} & {row['n_tuned']} & "
            f"{row['baseline_median_PE_max']:.2f} & {row['tuned_median_PE_max']:.2f} & "
            f"{row['U_statistic']:.1f} & {p_display} & {sig} \\\\"
        )
 
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    return "\n".join(lines)
 
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mann-Whitney U test (baseline vs CLiP-tuned) for Experiment 4"
    )
    parser.add_argument("-i", required=True, help="Path to the *_raw_runs.csv from experiment_4.py")
    parser.add_argument("-o", default=".", help="Output directory")
    parser.add_argument("--baseline-label", default="CLiP",
                         help='Method label for the untuned baseline (e.g. "CLiP" or "Apple")')
    parser.add_argument("--tuned-label", default="CLiP (CLiP-tuned)",
                         help='Method label for the tuned run (e.g. "CLiP (CLiP-tuned)")')
    args = parser.parse_args()
 
    os.makedirs(args.o, exist_ok=True)
    df = pd.read_csv(args.i)
 
    results_df = run_analysis(df, args.baseline_label, args.tuned_label)
 
    csv_path = os.path.join(args.o, "mannwhitney_experiment_4.csv")
    tex_path = os.path.join(args.o, "mannwhitney_experiment_4.tex")
 
    results_df.to_csv(csv_path, index=False)
    with open(tex_path, "w") as f:
        f.write(to_latex(results_df, args.baseline_label, args.tuned_label))
 
    print(results_df.to_string(index=False))
    print(f"\nSaved: {csv_path}")
    print(f"Saved: {tex_path}")
 