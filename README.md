<p align="center">
  <picture>
    <source srcset="https://github.com/user-attachments/assets/09204ae5-6326-4db0-bc97-c447cd49a42c" width="600" media="(prefers-color-scheme: dark)" >
    <img src="https://github.com/user-attachments/assets/f5f65605-55bd-4f4e-aaa3-29e9a3222057" alt="Logo" width="500">
  </picture>
</p>

<p align="center">
<img src="https://badgen.net/badge/license/MIT/orange?icon=github" alt="build badge">
<img src="https://badgen.net/badge/language/Python/yellow" alt="language badge">
<img src="https://badgen.net/badge/build/passing/green?icon=githubactions" alt="build badge">
<img src="https://badgen.net/pypi/v/clip-protocol" alt="PyPI version">
<img src="https://img.shields.io/pypi/pyversions/clip-protocol?color=red" alt="Python version supported">
<a href="https://clip-protocol.readthedocs.io/en/latest/">
  <img src="https://img.shields.io/badge/docs-online-blueviolet" alt="documentation">
</a>
</p>

## Index
* [Project Description](#project-description)
* [Repository Structure](#repository-structure)
* [Online Execution](#online-execution)
* [Usage](#usage)
* [Pseudocode](#pseudocode)
* [Documentation](#documentation)

## Project Description
Learning analytics involves collecting and analyzing data about learners to improve educational outcomes. However, this process raises concerns about the privacy of individual data. To address these concerns, this project implements differential privacy algorithms, which add controlled noise to data, ensuring individual privacy while maintaining the overall utility of the dataset. This approach aligns with recent advancements in safeguarding data privacy in learning analytics. 

In this project, we explore a privacy protocol for sketching with privacy considerations. The steps it follow

* **Setup**
* **Mask**
* **Agregation**
* **Estimation**

## Repository Structure
The repository is organized as follows:
```sh
Local_Privacy
┣ 📂 src
┣ ┣ 📂 clip_protocol
┃ ┃ ┣ 📂 count mean
┃ ┃ ┣ 📂 hadamard mean
┃ ┃ ┣ 📂 main
┃ ┃ ┃ ┣ setup.py
┃ ┃ ┃ ┣ mask.py
┃ ┃ ┃ ┣ agregate.py
┃ ┃ ┃ ┗ estimation.py
┃ ┗ ┗ 📂 utils
┗ 📂 tests
```
## Online Execution
You can execute the code online using Google Colab. Google Colab sessions are intended for individual users and have limitations such as session timeouts after periods of inactivity and maximum session durations. 

For **single-user dataset** scenarios, click this link to execute the method: [Execute in Google Colab](https://colab.research.google.com/drive/1dY1OSfRECHFBFYaX_5ToZy-KynjT_0z0?usp=sharing)

## Usage 
These methods are included in PyPI as you can view [here](https://pypi.org/project/clip-protocol/), and can be installed on your device with:
```sh
pip install clip-protocol
```
Once installed, you can execute the following commands to run the privacy adjustment methods.
### Setup
Use the following command:
```sh
setup -d <dataset>
```
- `dataset`: path to the input dataset (`.xlsx`) you want to setup for tests

Example:
```sh
setup -d /path/to/dataset.xlsx
```
### Mask
Use the following command:
```sh
mask -d <dataset> -o <output>
```
- `dataset`: Path to the input dataset you want to privatize.
- `output`: Path to where the privatized dataset will be saved.

> The output variable is optional, if it is not needed to save the privatized data you can skip it
### Agregation
Use the following command:
```sh
agregate
```
### Estimation 
Estimates the true frequencies from the aggregated privatized data. This command answers frequency queries based on the collected sketches.
```sh
estimate
```
### Clear 
Use this command when it is needed to delete all data saved from the previous steps.
```sh
clip_clear
```
### Important Notes
- Ensure that the paths provided are correct, and that the necessary permissions are granted for writing to the output location.
- In the mask step, the output will be a new file `.csv` containing the privatized data.

## Pseudocode of the Dynamic Privacy Budget (ε) Optimization for a single student in CLiP (via Optuna)
 
**Require:**
- Sequential event dataset $D$
- Reference budget $\epsilon_{ref}$
- Sketch dimensions $k, m$
- Acceptable error range ($l$ as the error value and $t$ as the tolerance) $[l-t,\ l+t]$
- Number of trials $N_{trials}$
- Level of privacy (*low* or *high*)

**Ensure:**
- Optimized privacy budget $\epsilon$
- Privatized dataset $D'$
```
1:  ε_priv ← ε_ref
2:  D_priv ← ∅
3:  F_real ← CalculateFrequencies(D)
4:  for i = 1 to N_trials do
5:      Propose candidate ε_priv ∈ [0.1, ε_ref]
6:      D_priv ← LDPMechanism(D, k, m, ε_priv)      // Applies PCMeS or PHCMeS
7:      F_est ← CalculateFrequencies(D_priv)
8:      PE_max ← MaxPercentageError(F_real, F_est)
9:      if (l - t)·100 ≤ PE_max ≤ (l + t)·100 then
10:         D' ← D_priv
11:         ε ← ε_priv
12:         break                                    // LA utility condition satisfied
13:     end if
14: end for
15: return ε, D'
```
 
  
## Documentation
The complete documentation for this project is available online. You can access it at the following link:
- [Project Documentation - Local Privacy in Learning Analytics](https://clip-protocol.readthedocs.io/en/latest/)

This documentation includes detailed explanations of the algorithms, methods, and the overall structure of the project.

## Authors
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/martaajonees"><img src="https://avatars.githubusercontent.com/u/100365874?v=4?s=100" width="100px;" alt="Marta Jones"/><br /><sub><b>Marta Jones</b></sub></a><br /><a href="https://github.com/martaajonees/Local_Privacy/commits?author=martaajonees" title="Code">💻</a></td>
       <td align="center" valign="top" width="14.28%"><a href="https://github.com/ichi91"><img src="https://avatars.githubusercontent.com/u/41892183?v=4?s=100" width="100px;" alt="Anailys Hernandez" style="border-radius: 50%"/><br /><sub><b>Anailys Hernandez</b></sub></a><br /><a href="https://github.com/ichi91/Local_Privacy/commits?author=ichi91" title="Method Designer">💡</a></td>
    </tr>
     
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

