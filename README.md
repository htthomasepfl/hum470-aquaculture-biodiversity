# Aquaculture and Marine Biodiversity Pressures in Norway's Salmon Industry

**EPFL HUM-470 — Economic Growth and Sustainability II**  
**Spring 2025–2026 · Group 02**

## Authors

- Victor Legrand  
- Thomas Hetier  
- Elhadji Ousmane Ndiaye  
- Dominic Bazina-Grolinger

**Supervisors:** Dr. Sascha Nick · Prof. Philippe Thalmann

## Overview

This repository contains the data, code, and analysis for our final report on environmental decoupling in Norwegian salmon aquaculture. We apply two IPAT decompositions to assess whether absolute decoupling has occurred between salmon production growth and two measurable biodiversity pressures:

1. **IPAT 1 — Wild fish extraction** (*W*, tonnes/year): total wild forage fish extracted to supply Norwegian salmon feed, 2000–2013.  
2. **IPAT 2 — Persistent antiparasitic chemical discharge** (*A_out*, kg/year): total persistent antiparasitic substances discharged into Norwegian fjords from sea lice treatments, 2012–2019.

## Key Results

| Pressure | Period | Production change | Pressure change | Dominant driver |
|----------|--------|-------------------|-----------------|-----------------|
| Wild fish extraction (*W*) | 2000–2013 | +166% | **−64%** | *W/M* (by-product substitution): −0.94 ln-pts |
| Chemical discharge (*A_out*) | 2012–2019 | +10.7% | **−95.3%** | *δ* (bath → oral shift): −2.04 ln-pts |

Both pressures show **absolute decoupling**: environmental impact fell in absolute terms while the industry continued to grow.

## Repository Structure

```
├── README.md
├── report/
│   └── main.tex                          # LaTeX source of the final report
├── code/
│   ├── ipat1_analysis.Rmd                # R Markdown — IPAT 1 analysis and figures
│   ├── ipat2_analysis.Rmd                # R Markdown — IPAT 2 analysis and figures
│   └── fetch_barentswatch_lice.py        # Python — BarentsWatch API data retrieval
├── data/
│   ├── sta-laks-mat-06-salg.xlsx         # Fiskeridir Atlantic salmon sales (Norwegian)
│   ├── ipat_decomposition_2000_2013.csv  # IPAT 1 annual decomposition (2000–2013)
│   ├── ipat2_antiparasitic_discharge.csv # IPAT 2 annual decomposition (2012–2019)
│   ├── lice_annual_avg.csv              # Annual avg adult female lice per fish
│   ├── treatments.csv                    # Raw BarentsWatch treatment event data
│   ├── Fish Health Report 2024.pdf       # NVI Fish Health Report 2024
│   ├── rapport_2014.pdf                  # Nofima Report 36/2014 (feed benchmarks)
│   ├── rapport_2015.pdf                  # Ytrestøyl et al. 2015 (Aquaculture 448)
│   ├── 2016_22_Use of Antibiotics in Norwegian Aquaculture.pdf
│   └── file.pdf                          # Additional reference document
└── figures/
    ├── Atlantic_Salmon_production.png    # Fig 5.1 — Production P (2000–2013)
    ├── Ipat1_Interpolation_factors.png   # Fig 5.2 — F/P, M/F, W/M interpolation
    ├── Absolut_decoupling.png            # Fig 5.3 — W vs P decoupling
    ├── Waterfall_chart_factors_IPAT_1.png# Fig 5.4 — IPAT 1 waterfall
    ├── Contribution_multipliers_IPAT_1.png
    ├── Index_IPAT_1.png
    ├── YoY_decomposition_IPAT_1.png
    ├── Absolut_Decoupling_IPAT_2.png     # Fig 6.1 — A_out vs P decoupling
    ├── A_out_absolut_term.png            # Fig 6.2 — A_out absolute (kg/yr)
    ├── IPAT_2_Factors.png                # Fig 6.3 — Five-factor time series
    ├── IPAT_2_Waterfall.png              # Fig 6.4 — IPAT 2 waterfall
    └── Treatment_Mix_shift_IPAT_2.png    # Fig 6.5 — Treatment mix stacked bar
```

## IPAT Identities

**IPAT 1 — Wild fish extraction:**

$$W = P \times \frac{F}{P} \times \frac{M}{F} \times \frac{W}{M}$$

where *P* = salmon production (t), *F/P* = feed conversion ratio (eFCR), *M/F* = marine ingredient share, *W/M* = wild fish dependency ratio (FFDR_FM).

**IPAT 2 — Persistent chemical discharge:**

$$A_{out} = N_{salmon} \times \lambda \times \tau \times \phi \times \delta$$

where *λ* = lice per fish, *τ* = treatments per lice, *φ* = chemical share of treatments, *δ* = kg discharged per chemical event. H₂O₂ is excluded from *A_out* (half-life < 1 h, non-persistent). Oral treatments are assigned a 3% discharge factor.

## Data Sources

| Dataset | Variables | Period | Source |
|---------|-----------|--------|--------|
| Fiskeridir sales statistics | *P* (tonnes) | 2000–2019 | [Norwegian Directorate of Fisheries](https://www.fiskeridir.no/english/aquaculture/statistics-for-aquaculture/atlantic-salmon-and-rainbow-trout) |
| Nofima benchmark reports | *F/P*, *M/F*, *W/M* | 2000, 2010, 2012, 2013 | Ytrestøyl et al. (2015), *Aquaculture* 448:365–374 |
| BarentsWatch Fish Health API | Lice counts, treatment events | 2012–2019 | [BarentsWatch](https://www.barentswatch.no/data) |
| Myhre Jensen et al. (2020) | Substance quantities by type | 2012–2019 | *Aquaculture* 519:734385 |

## Reproducing the Analysis

### Requirements

- **R** (≥ 4.1) with packages: `tidyverse`, `readxl`, `scales`, `patchwork`, `knitr`  
- **Python 3** (≥ 3.8) with `requests`, `pandas` (only for `fetch_barentswatch_lice.py`)

### Running the code

1. Open `code/ipat1_analysis.Rmd` in RStudio. Set the working directory to `data/`. Knit to PDF.  
2. Open `code/ipat2_analysis.Rmd` in RStudio. Set the working directory to `data/`. Knit to PDF.

Both scripts produce all figures used in the report and verify the IPAT identities (residual = 0% for all years).

### BarentsWatch data retrieval

The `fetch_barentswatch_lice.py` script retrieves weekly lice counts from the BarentsWatch Fish Health API and computes annual national averages. It requires OAuth2 credentials:

```bash
export BW_CLIENT_ID="your_client_id"
export BW_CLIENT_SECRET="your_client_secret"
python code/fetch_barentswatch_lice.py
```

Register at [barentswatch.no/minside](https://www.barentswatch.no/minside/) to obtain API credentials.

## License

This repository is provided for academic purposes as part of the EPFL HUM-470 course. Data from Norwegian public sources (Fiskeridir, BarentsWatch) are publicly available. Nofima benchmark values are reported from published academic literature.