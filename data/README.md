# Data sources and availability

Public housing, permit, socioeconomic, hazard, and regulatory-text sources.

Acquisition and prototype code with selected summaries are included. Grant applications and internal funding strategy are excluded.

The prototype reads three processed/interim tables listed in data/INPUTS.json. download_data.py describes acquisition. Reference outputs are descriptive snapshots; their correlations do not identify the effect of a regulatory barrier.

## File-level records

- [Required inputs](INPUTS.json) describes separately acquired files.
- [Released table inventory](TABLES.csv) lists distributed table columns and row counts.
- [Source fingerprints](../SOURCE_FILES.csv) links retained source content to its hashes without publishing private workspace paths.

Raw records, access credentials, personal notes, correspondence, and publisher full-text collections are not distributed.
