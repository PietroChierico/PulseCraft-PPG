# Contributing

Contributions are welcome when they keep the kit **educational, reproducible, and safe**.

## Good contributions

- Clearer setup or wiring instructions, wiring diagrams, setup photos.
- Better signal-quality checks and troubleshooting entries.
- New simulator scenarios or a more realistic waveform model.
- Additional interpretable features or visualisations.
- Translations of the docs and worksheets.
- Bug fixes in parsers, protocols, or GUIs.
- New projects that follow the collect → analyze → run-live pattern.

## Please do not submit

- Real participant recordings, private photos, or anything with identifiers.
- Clinical or diagnostic claims.
- Large binary dependencies or heavyweight ML frameworks.

## Dev setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python tools/check_setup.py
# smoke test without hardware:
python tools/ppg_simulator.py --scenario plain --port 3333   # terminal 1
python tools/check_setup.py --stream 127.0.0.1:3333          # terminal 2
```

## Before opening a PR

- Keep Python 3.11-compatible; no new required dependencies without discussion.
- `python -m py_compile` must pass for every changed `.py` (CI checks this).
- If you touch a protocol or feature set, update the matching `docs/` page and worksheet.
- One focused change per PR. Describe what you tested (hardware or simulator).

## Reporting problems

Use the issue templates in `.github/ISSUE_TEMPLATE/`. Include OS, Python version, wired/wireless,
the exact command, and the full error.

By contributing you agree your work is licensed under MIT (code) / CC BY 4.0 (media), and that you
will follow the [Code of Conduct](CODE_OF_CONDUCT.md).
