# CLiP Protocol — Evaluation

This folder contains the experimental evaluation of **CLiP (Context-aware Local information Protection)**, a privacy-preserving protocol for estimating frequencies over sequential data in Learning Analytics, based on Local Differential Privacy (LDP) and probabilistic sketches (**PCMeS** and **PHCMeS**).

The code in this directory reproduces the experiments reported in the paper *"CLiP: Privacy Preserving Protocol for Estimating Frequency over Sequential Data in Learning Analytics"*.

## Folder structure

```
evaluation/
├── AOI datasets/          # Real-world eye-tracking dataset (AOIdataset)
├── Parameters and results/# Setup-stage outputs (k, m, epsilon_ref) and experiment results
├── Synthetic datasets/    # Synthetic event-sequence datasets (SynLog-*)
├── __init__.py
├── experiment_1.py        # Experiment 1: Influence of the privacy budget on estimation accuracy
├── experiment_2.py        # Experiment 2: Scalability of the CLiP protocol
├── experiment_3.py        # Experiment 3: CLiP under different data distributions
├── experiment_4.py        # Experiment 4: Comparative analysis of CLiP vs. Apple's fixed-budget method
├── experiment_5.py        # Experiment 5: Application of CLiP on real data (AOIdataset)
├── experiment_7.py        # Additional experiment (see article/appendix for details)
└── generate_dataset.py    # Synthetic dataset generator (uniform, Poisson, categorical distributions)
```

## Datasets

### Real-world data — `AOI datasets/`
`AOIdataset`: eye-tracking data collected from 20 undergraduate students using **MetaTutorES**, an intelligent tutoring system. Fixations are aggregated into three Areas of Interest (AOI):

- **AOI1** — Learning session timer
- **AOI2** — Intelligent tutoring system agent/avatar
- **AOI3** — Instructional images/graphics

### Synthetic data — `Synthetic datasets/`
Generated with `generate_dataset.py` to simulate four discrete events (`e0`, `e1`, `e2`, `e3`) under different distributions, labeled as `SynLog-<size>-<distribution>` (e.g., `SynLog-5000-d1`):

| Label | Distribution   | Description                                   |
|-------|----------------|------------------------------------------------|
| d1    | Uniform        | All events equally likely (balanced baseline) |
| d2    | Poisson        | Events at a known average rate                |
| d3    | Categorical    | Moderate class imbalance                      |
| d4    | Categorical    | Extreme class imbalance                       |

Dataset sizes range from 3,000 to 7,000 records.

## Experiments

### `experiment_1.py` — Influence of the privacy budget (ε) on estimation accuracy
Evaluates the accuracy of frequency estimation for different values of the privacy budget ε on `SynLog-5000-d1`, comparing **PCMeS** and **PHCMeS** across four error metrics: MAE, RMSE, L_p Norm, and MSE. Each configuration is run twice to assess stability.

### `experiment_2.py` — Scalability of the CLiP protocol
Analyzes the execution time and number of iterations of the masking stage as dataset size increases (`SynLog-3000-d1` to `SynLog-7000-d1`), comparing PCMeS and PHCMeS in terms of computational efficiency.

### `experiment_3.py` — CLiP under different data distributions
Evaluates the robustness of CLiP across the four synthetic distributions (`d1`–`d4`), measuring the percentage estimation error (PE) per event to assess sensitivity to event imbalance.

### `experiment_4.py` — Comparative analysis: CLiP vs. Apple's fixed-budget method
Compares CLiP's dynamic, personalized privacy-budget optimization against Apple's (2017) fixed-budget PCMeS configuration, across multiple dataset sizes.

### `experiment_5.py` — Application of CLiP on real data
Applies the full CLiP protocol to the real-world `AOIdataset` (20 students), using student S11 as the reference subject for the setup stage. Reports the optimized privacy budget ε and maximum estimation error (PE_max) under both **low** and **high** privacy levels for every student.

### `experiment_7.py`
Additional experiment extending the evaluation suite (refer to the corresponding section/appendix of the article for details not covered in Experiments 1–5).

## Outputs

Results from the setup stage (sketch dimensions `k`, `m`, and reference privacy budget `ε_ref`) and experiment outputs (error metrics, execution times, per-student privacy budgets) are stored in `Parameters and results/`.

## Reference

If you use this code, please cite:

> *CLiP: Privacy Preserving Protocol for Estimating Frequency over Sequential Data in Learning Analytics*. Journal of Learning Analytics.

## License / Notes

This implementation follows the ACM artifact review guidelines for functional, reusable, and publicly available artifacts. Hyperparameter optimization is performed with [Optuna](https://optuna.org/) (TPE algorithm).
