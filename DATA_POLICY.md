# Data policy

This repository ships **no** participant recordings, datasets, trained models, or generated
analysis outputs. Everything under those categories is produced locally by the user and stays
local.

PPG is physiological data. Handle it accordingly:

- Collect only what the exercise needs.
- Use participant codes, never names, in filenames or CSVs.
- Get consent appropriate to what you will do with the data. A live in-class demo with nothing
  retained needs only clear verbal consent; keeping or publishing data needs your institution's
  ethics/IRB process.
- Do not commit raw participant data, models, or result folders to git.
- Store anything you keep outside the repository, unless it is synthetic or explicitly approved
  for release.

`.gitignore` excludes `*.csv`, `*.tsv`, model files (`*.joblib`, `*.pkl`, `*.npy`, …), and the
`data/`, `datasets/`, `outputs/`, `results/`, `models/` folders by default. Do not override this
to commit data.

Synthetic data from `tools/ppg_simulator.py` is safe to share.
