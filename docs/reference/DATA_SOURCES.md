# Public data sources

The sources below support housing, permitting, and regulatory-text measurement. Provider terms apply separately to each source.

## Structured Data

### Census Building Permits Survey

Source page: https://www.census.gov/construction/bps/

Prototype files:

- county annual year-to-date text files, 2020-2025;
- South region place annual year-to-date text files, 2020-2025.

Study use: local housing supply, unit mix, and permitting output. BPS measures authorized new construction, not completed construction or a direct measure of regulatory delay.

### Census Manufactured Housing Survey

Source page: https://www.census.gov/programs-surveys/mhs/technical-documentation/datasets.html

Prototype files:

- annual shipments to states workbook;
- monthly shipments to states workbook;
- annual average price workbook;
- annual average square footage workbook;
- 2024 public use file workbook.

Study use: manufactured housing supply pipeline, unit characteristics, and
state-level shipment trends. This links the regulatory-barrier question to the
actual manufactured/modular market.

### ACS 2024 5-Year County Data

Source page: https://www.census.gov/data/developers/data-sets/acs-5year.html

Prototype variables:

- total housing units;
- mobile home units;
- median household income;
- median gross rent;
- median home value;
- renter households;
- owner households.

Study use: baseline housing stock, affordability, and manufactured/mobile
home prevalence by county.

### FEMA National Risk Index

Source page: https://hazards.fema.gov/nri/data-resources

The prototype uses the NRI input vintage acquired by its download script. A later provider download may differ and should be recorded as a new input version.

Prototype variables:

- overall risk score and rating;
- expected annual loss score and rating;
- social vulnerability score and rating;
- community resilience score and rating;
- selected coastal flood, hurricane, wind, tornado, wildfire, and heat scores.

Study use: resilience constraints. CECREH can distinguish barriers that
increase supply from barriers that shift low-cost housing into risky geographies
or weak recovery contexts.

### Texas Manufactured Housing Administrative Data

Source pages:

- https://www.tdhca.texas.gov/mhd
- https://mhweb.tdhca.state.tx.us/mhweb/main.jsp

Planned acquisition targets:

- ownership records;
- monthly titling reports;
- installation records;
- license records;
- county ownership counts.

Study use: Texas-specific manufactured-home placement and administrative
context. These sources can improve local manufactured-home measures beyond
state-level Census MHS context, but they should be tracked separately from local
ordinance text.

### Texas Industrialized / Modular Housing Administrative Data

Source page: https://www.tdlr.texas.gov/ihb/

Planned acquisition targets:

- industrialized housing and buildings rules;
- registrant lists;
- inspection/procedure sources;
- state guidance on modular/industrialized housing.

Study use: state regulatory context and modular/industrialized housing
distinctions. These data distinguish modular,
industrialized, HUD-code manufactured, and mobile housing categories.

### Optional Zoning Benchmarks

Potential source: National Zoning Atlas and licensed zoning datasets where
available.

Study use: current zoning benchmarks or context only. These sources should
not be treated as the historical treatment source unless they include dated rule
changes and usable ordinance-history evidence.

## Unstructured Data

The first NLP corpus is deliberately small. It is meant to test whether automated
text extraction and barrier coding are feasible before scaling to a large
municipal-code corpus.

Initial accessible pages:

- Texas Department of Licensing and Regulation industrialized/modular housing
  consumer guidance: https://www.tdlr.texas.gov/ihb/beforebuying.htm
- City of Dalhart code department manufactured home permitting page:
  https://www.dalharttx.gov/199/Code-Department
- City of Burnet conditional use permit ordinance page:
  https://www.burnetedc.com/ordinances/conditional-use-permit-manufactured-home-sales
- Texas Real Estate Research Center modular housing article:
  https://trerc.tamu.edu/article/modular-housing/

Candidate municipal code pages that appear relevant but may require browser/API
collection:

- eCode360 and Municode pages for Texas cities with manufactured/modular housing
  provisions.

Study use: NLP can convert code text into barrier indicators: where
manufactured/modular housing is allowed by right, allowed only in a special
district, requires conditional/specific use approval, faces age limits, must
match taxable value/design compatibility, or requires additional inspection and
site-plan layers.

## Source capture and coding

The public [download script](../../scripts/download_data.py) describes the supplied acquisition implementation. The broader Texas acquisition queue and hand-coding materials are not distributed. Record each captured page's source, date, jurisdiction, and coding status before interpreting regulatory-text counts. A page that has not been captured or coded is not evidence that a jurisdiction has or lacks a restriction.
