# Publishing this repository

A checklist for the first push and for making it discoverable (SEO).

## 1. Placeholders

Already set to `PietroChierico` in `README.md`, `CITATION.cff`, `docs/index.md`, and
`.github/ISSUE_TEMPLATE/config.yml`. Nothing to do here unless you rename the GitHub account.

## 2. Check nothing private is included

- [ ] No CSVs, models, or `data/` / `results/` folders (`.gitignore` should already prevent this).
- [ ] Setup photos in `docs/assets/images/` have no faces, ID badges, screens with participant
      data, or handwritten notes.
- [ ] No names beyond the author and the two named supervisors.

## 3. Create the repo and push

```bash
git init
git add .
git commit -m "PulseCraft PPG 1.0.0 — open photoplethysmography teaching kit"
git branch -M main
git remote add origin https://github.com/your-handle/PulseCraft-PPG.git
git push -u origin main
git tag v1.0.0 && git push --tags
```

## 4. Make it discoverable (the SEO part)

**Repo → About (gear icon):**

- **Description:**
  `Open photoplethysmography (PPG) teaching kit: Arduino + ESP32 acquisition, MAX30102 case, Python feature extraction, small ML models, live demos, and a no-hardware simulator. 5 ready-to-teach projects.`
- **Website:** `https://your-handle.github.io/PulseCraft-PPG/`
- **Topics (add all):**
  `photoplethysmography` `ppg` `biomedical-signal-processing` `wearable-sensing` `digital-health`
  `heart-rate-variability` `pulse-oximetry` `arduino` `esp32` `max30102` `max30105`
  `machine-learning` `biomedical-engineering` `stem-education` `teaching-materials`
  `open-educational-resources` `signal-processing` `python`

**Repo settings:**

- Enable **Issues** and **Discussions**.
- **Pages:** Settings → Pages → Source = `Deploy from a branch`, branch `main`, folder `/docs`.
- Add a social preview image (Settings → Social preview) — a photo of the setup or a diagram.

**In the first GitHub Release (`v1.0.0`):** paste the `CHANGELOG.md` 1.0.0 section.

## 5. Get a citable DOI (optional, recommended)

1. Sign in to [Zenodo](https://zenodo.org) with GitHub.
2. Flip the switch for `PulseCraft-PPG` in Zenodo → GitHub settings.
3. Publish a new GitHub Release — Zenodo mints a DOI automatically.
4. Add the DOI badge to `README.md` and the `doi:` field to `CITATION.cff`.

## 6. Announce

- A short post with the Pages link and one screenshot.
- Consider: awesome-lists for biomedical engineering / physiological computing, your lab site,
  relevant subreddits and forums, and the Hackaday.io / Arduino Project Hub communities.
