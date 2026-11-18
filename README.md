[English](README.md) | [Español](README.es.md)

# Mercury in Prod

[![CI](https://img.shields.io/github/actions/workflow/status/AnaCataVC/mercury-in-prod/ci.yml?branch=main&style=flat&logo=githubactions&logoColor=white&label=CI)](https://github.com/AnaCataVC/mercury-in-prod/actions)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.36%2B-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.22%2B-3F4F75?style=flat&logo=plotly&logoColor=white)](https://plotly.com/python/)

Empirical Data Science laboratory testing whether **Mercury retrograde**, planetary shadow windows, or lunar phases correlate with software production incidents—and demonstrating how **calendar confounders** and **multiple-hypothesis testing (*p*-hacking)** create illusory patterns.

The ephemeris engine (`src/ephemeris.py`) is an exact Python port of `AstrologyEngine.kt` from `one-ui-extra-widgets`, powered by [`astronomy-engine`](https://pypi.org/project/astronomy-engine/) for 100% deterministic offline planetary and lunar calculations.

---

## Key Findings

- **Real Public Statuspage Audit (400 incidents across 8 platforms):** Cross-referencing recent public incidents from GitHub, Cloudflare, npm, Discord, Reddit, Bitbucket, Vercel, and DigitalOcean against each provider's exact date-window base rate shows zero excess risk (`Mercury Retrograde`: 31.0% observed vs 29.5% expected, `p = 0.51`; `Mercury Pre/Post Shadow`: 26.0% vs 26.1%, `p = 1.00`; `Full Moon`: 8.5% vs 11.0%, `p = 0.11`).
- **Confounder-Controlled Poisson GLM (2,130 days, 2021–2026):** With HC3 robust standard errors, operational calendar dynamics drive incident variance (`Weekend IRR = 0.31`, `p < 0.0001`; `Midweek Deploy Window Tue–Thu IRR = 1.23`, `p < 0.0001`; `Patch Tuesday IRR = 1.31`, `p = 0.0007`; `Q4 Code Freeze IRR = 0.63`, `p = 0.0011`), while `Mercury Retrograde` (`IRR = 0.98`, `p = 0.71`), `Mercury Shadow` (`IRR = 1.05`, `p = 0.30`), and `Full Moon` (`IRR = 0.91`, `p = 0.16`) sit at null.
- **P-Hacking & Seasonal Confounding (57 hypotheses):** Scanning 57 planetary, lunar, zodiacal, and subgroup slices yields 7 naive hits below `p < 0.05`. Benjamini-Hochberg FDR eliminates random noise hits (`Sun in Sagittarius`, `Moon in Taurus`, `Full Moon on Weekdays`), and exposes why the lone FDR survivor (`Sun in Capricorn`) is actually seasonal confounding from the December Q4 Code Freeze.

---

## Project Architecture

```text
mercury-in-prod/
├── .github/
│   └── workflows/
│       └── ci.yml            # Automated Ruff linter, pytest suite, and static build check
├── docs/
│   └── ux/
│       └── mercury-in-prod-lab.md  # 5-state UX specification and interaction contract
├── src/
│   ├── ephemeris.py          # Offline AstrologyEngine port (Sun, Moon, Mercury–Saturn)
│   ├── incidents.py          # Public Statuspage v2 ingestion + multi-year operational panel
│   ├── stats.py              # Naive tests, Poisson GLM (HC3), permutations, FDR/Bonferroni
│   └── build_site.py         # Builds standalone static Data Story + client-side explorer
├── data/
│   ├── raw_public_incidents.csv
│   ├── daily_incidents_ephemeris.csv
│   └── study_results.json
├── site/
│   └── index.html            # Version A: Static Data Story (GitHub Pages / Vercel ready)
├── app.py                    # Version B: Exploratory Streamlit lab (live permutations)
├── tests/
│   ├── test_ephemeris.py     # Parity tests matching AstrologyEngineTest.kt
│   ├── test_incidents.py     # Statuspage ingestion, deduplication, and cache fallback tests
│   ├── test_stats.py         # Statistical engine & multiple-testing invariants
│   └── test_build_site.py    # Static HTML generation & embedded JSON contract tests
├── pyproject.toml
└── requirements.txt
```

---

## Quick Start

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 1. Run Unit Tests

```bash
pytest -v
```

### 2. Rebuild Dataset, Statistical Study, and Static Web Story

```bash
python -m src.build_site
```

Open `site/index.html` in any browser or deploy the `site/` directory directly to **GitHub Pages** or **Vercel**.

### 3. Launch the Dynamic Exploratory App (Streamlit)

```bash
streamlit run app.py
```

Deploy `app.py` directly on **Streamlit Community Cloud** or **Hugging Face Spaces** pointing to the same repository.
