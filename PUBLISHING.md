# Publishing and discoverability

Notes for publishing this repository, or a fork of it, and for making it easy to find.

## Before the first push

Check that nothing private is included.

- No CSVs, models, or `data/` and `results/` folders. `.gitignore` should already prevent this.
- Setup photos under `docs/assets/images/` have no faces, ID badges, screens showing participant
  data, or handwritten notes.
- No names beyond the author and the two named supervisors.

## Create the repo and push

```bash
git init
git add .
git commit -m "PulseCraft PPG 1.0.0"
git branch -M main
git remote add origin https://github.com/your-handle/PulseCraft-PPG.git
git push -u origin main
git tag v1.0.0 && git push --tags
```

## Repo settings that make it findable

Open the repo's About panel (the gear icon on the main page) and set the following.

Description.

```
Open photoplethysmography (PPG) projects. Arduino and ESP32 acquisition, a MAX30102 sensor case, Python feature extraction, small ML models, live demos, and a no-hardware simulator. Five small projects.
```

Website, `https://your-handle.github.io/PulseCraft-PPG/`.

Topics, added one at a time.

```
photoplethysmography  ppg  biomedical-signal-processing  wearable-sensing  digital-health
heart-rate-variability  pulse-oximetry  arduino  esp32  max30102  max30105  machine-learning
biomedical-engineering  stem-education  teaching-materials  open-educational-resources
signal-processing  python
```

In the repo settings, enable Issues and Discussions. Under Pages, set the source to a branch,
pick `main` and the `/docs` folder. Add a social preview image under Social preview, a photo of
the setup or a diagram works well.

For the first GitHub Release, tag `v1.0.0` and paste the 1.0.0 section of `CHANGELOG.md`.

## Optional, a citable DOI

Sign in to Zenodo with GitHub, turn on the switch for this repository in the Zenodo GitHub
settings, then publish a GitHub Release. Zenodo mints a DOI for it. Add the DOI badge to
`README.md` and a `doi:` field to `CITATION.cff`.
