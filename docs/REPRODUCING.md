# Reproduction guide

Public-data prototype and descriptive reference tables; full acquisition remains to verify.

## Verify the distribution

From the package root:

```bash
python scripts/check_package.py
python scripts/check_inputs.py
```

The first command verifies the shipped files and hashes. The second checks whether separately acquired inputs are present and exits with code 2 when they are missing. Neither command estimates a statistical model.

## Run the selected workflow

The prototype reads three processed/interim tables listed in data/INPUTS.json. download_data.py describes acquisition. Reference outputs are descriptive snapshots; their correlations do not identify the effect of a regulatory barrier.

Use a disposable working copy when running the original analysis: several original scripts overwrite their project-relative output locations. Keep the distributed reference snapshot for comparison.

Environment: `See docs/SOFTWARE.md and the dependencies imported by the chosen source modules.`

```bash
python scripts/prototype_viability.py
```

## Input contract

Required paths are listed in [data/INPUTS.json](../data/INPUTS.json). Acquisition and prototype code with selected summaries are included. Grant applications and internal funding strategy are excluded.

[Source guide](CODE_MAP.md) identifies additional acquisition, sensitivity, and rendering modules. Original modeling and uncertainty procedures are retained. Use the documented input definitions; undocumented data substitutions can change the analysis.

## Evidence

[VALIDATION.json](../VALIDATION.json) records the checks performed on this snapshot. A partial model run or a fictional demo is identified by its limited scope. Full reproduction is claimed only where that record explicitly supports it.
