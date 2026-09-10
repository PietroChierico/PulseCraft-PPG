# Data policy

This repository ships no participant recordings, datasets, trained models, or generated analysis
outputs. Anything in those categories is produced locally by the user and stays local.

PPG is physiological data, so handle it with care.

- Collect only what the exercise needs.
- Use participant codes in filenames and CSVs, never names.
- Get consent that matches what you will do with the data. A live in-class demo with nothing kept
  needs only clear verbal consent. Keeping or publishing data needs your institution's ethics or
  IRB process.
- Do not commit raw participant data, models, or result folders to git.
- Store anything you keep outside the repository, unless it is synthetic or has been explicitly
  approved for release.

`.gitignore` already excludes `*.csv`, `*.tsv`, model files such as `*.joblib`, `*.pkl` and
`*.npy`, and the `data/`, `datasets/`, `outputs/`, `results/` and `models/` folders. Do not
override that to commit data.

Synthetic data from `tools/ppg_simulator.py` is safe to share.
