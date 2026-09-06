# Data sources and availability

Public housing, permit, socioeconomic, hazard, and regulatory-text sources.

Acquisition and prototype code with selected summaries are included. Grant applications and internal funding strategy are excluded.

## External inputs for the entry point

Paths are relative to the repository root. They describe files or directories to supply; they are not bundled download links. Upstream acquisition and optional analyses may require additional inputs.

| Path | Availability |
|---|---|
| `data/processed/county_prototype_panel_2020_2025.csv` | external; not bundled |
| `data/processed/zoning_text_term_counts.csv` | external; not bundled |
| `data/interim/mhs_workbook_inventory.csv` | external; not bundled |

## File definitions and provenance

- [Table inventory](TABLES.csv): distributed CSV columns and row counts.
- [Input inventory](INPUTS.json): paths checked by the input preflight.
- [Source fingerprints](../SOURCE_FILES.csv): hashes of retained source files and their public versions.
