# UX Specification: Mercury in Prod Exploratory Lab & Data Story

> **Status:** Approved
> **Target Interface:** Web (Static Data Story `site/index.html` & Interactive Streamlit Lab `app.py`)

## 1. User Intent & Mental Model

- **Primary User Goal:** Empirically audit whether planetary transits (Mercury retrograde, pre/post shadow windows, lunar phases, and zodiac signs) correlate with software production incidents, and observe how engineering calendar confounders and multiple-hypothesis testing (*p*-hacking) generate illusory patterns.
- **Mental Model (Jakob's Law):** Data journalists, engineers, and technical readers expect a clear executive verdict upfront, followed by verifiable interactive evidence and a filterable statistical sandbox that behaves like standard BI/analytics dashboards with consistent controls and responsive charts.
- **Progressive Disclosure Strategy:**
  - **Layer 1 (Executive Overview):** High-level KPI summary cards and the statistical verdict callout appear immediately above the fold without requiring user interaction.
  - **Layer 2 (Controlled Evidence):** Scrollable narrative sections present the 2021–2026 orbital timeline, confounder-controlled Poisson GLM forest plot, 57-hypothesis multiple-testing volcano plot with top-10 FDR table, and real Statuspage platform audit.
  - **Layer 3 (Interactive Hypothesis Exploration & Raw Inspection):** The bottom-up Interactive Hypothesis Explorer (`site/index.html`) and the multi-tab Streamlit Laboratory (`app.py`) let users filter astronomical conditions, calendar slices, and Monte Carlo permutations, while raw Statuspage incident tables remain collapsed inside an expandable disclosure (`st.expander`).

## 2. The 5 Essential UX States

| State | Screen Behavior (`site/index.html` & `app.py`) | Actionable Elements & Microcopy |
| :--- | :--- | :--- |
| **1. Ideal (Populated)** | Static Data Story renders 4 KPI cards, verdict callout, 5 Plotly visualizations using design tokens from `:root`, top-10 FDR table, and synchronized explorer controls. Streamlit Lab renders 3 populated tabs with `THEME_COLORS` charts and human-readable `st.column_config` tables. | Bilingual toggle (`EN` / `ES`), hypothesis & calendar slice selectors, `"Reset Explorer Filters"` / `"Restablecer Filtros"` secondary button, and live Monte Carlo permutation controls. |
| **2. Empty State** | When a chart dataset or Statuspage audit table has zero records, or when a Streamlit calendar filter yields fewer than 2 exposed days (`n_exposed < 2`), the UI displays a structured empty/insufficient-sample notice instead of a blank container or misleading statistics. | Informational notice explaining why inference is unavailable and guiding the user to broaden the calendar slice or reset filters (`"Reset Explorer Filters"` / `"Restablecer Filtros"`). |
| **3. Loading & Transition** | Static HTML initializes DOM cards and controls immediately before chart hydration; chart containers reserve `min-height` to prevent Cumulative Layout Shift (CLS). Streamlit displays descriptive spinners on `@st.cache_data` loading and keeps filter columns fixed without vertical layout jumps when switching astronomical dimensions. | `"Loading ephemeris & incidents data..."` spinner in Streamlit; immediate numeric KPI rendering in static HTML prior to Plotly mounting. |
| **4. Error & Recovery** | Enforces the **Zero Information Leakage Invariant**: chart rendering exceptions in JS (`try/catch` around `Plotly.newPlot`) and dataset loading exceptions in `app.py` catch internal failures without exposing stack traces, SQL, or local paths. | Empathetic error banner paired with an explicit recovery action: `"Retry Chart Render"` / `"Reintentar Renderizado"` in static HTML and `"Retry Loading Data"` / `"Reintentar Carga de Datos"` (`st.rerun()`) in Streamlit. |
| **5. Partial / Degraded** | If the external Plotly CDN is unreachable offline (`typeof Plotly === "undefined"`), KPIs, top-hits table, and Explorer summary statistics remain 100% functional while `.chart-box` renders a degraded notice. Language and explorer selections persist safely via `localStorage`. In `app.py`, cached Statuspage snapshots remain active if live API refresh is unavailable. | Degraded inline notice: `"Interactive chart unavailable offline — statistical summary active above."` / `"Gráfico interactivo no disponible sin conexión — resumen estadístico activo arriba."` paired with `"Retry Chart Render"` / `"Reintentar Renderizado"`. |

## 3. Microcopy & Button Directory

| UI Element | Label (EN) | Label (ES) | Purpose & Feedback |
| :--- | :--- | :--- | :--- |
| Language Switch Buttons (`#btn-en`, `#btn-es`) | `EN` / `ES` | `EN` / `ES` | Toggles active UI locale, updates `<html lang>` and `aria-pressed`, and persists selection in `localStorage`. |
| Reset Explorer Action (Secondary) | `"Reset Explorer Filters"` | `"Restablecer Filtros"` | Restores default hypothesis (`Mercury Retrograde`) and calendar slice (`All Days`) across Explorer controls. |
| Retry Chart Action (Secondary) | `"Retry Chart Render"` | `"Reintentar Renderizado"` | Re-invokes `renderAll()` when Plotly CDN recovers or after a transient render failure. |
| Retry Data Load Action (`app.py`) | `"Retry Loading Data"` | `"Reintentar Carga de Datos"` | Triggers `st.rerun()` after an unexpected dataset read/build error. |
| Degraded Offline Chart Notice | `"Interactive chart unavailable offline — statistical summary active above."` | `"Gráfico interactivo no disponible sin conexión — resumen estadístico activo arriba."` | Informs user that numeric inference remains valid when CDN scripts cannot load. |
| Empty Chart / Audit Notice | `"No records available for this view."` | `"No hay registros disponibles para esta vista."` | Replaces blank chart frames or empty Statuspage audit sections. |
| Low Sample Warning (`app.py`) | `"Sample size too small (< 2 exposed days) for reliable inference. Select a broader calendar slice."` | `"Muestra insuficiente (< 2 días expuestos) para inferencia fiable. Selecciona un filtro de calendario más amplio."` | Prevents misreading degenerate `rate_ratio = 1.0` / `p = 1.0` placeholders on sparse slices. |

## 4. Interaction Ergonomics & Safety Guardrails

- **Single Token Source of Truth:** All colors, plot grids, backgrounds, and border radii live in CSS `:root` custom properties inside `src/build_site.py` (with `color-scheme: dark` and matching dark scrollbar styling) and are read dynamically in JavaScript via `getComputedStyle(document.documentElement)`. `app.py` centralizes plot color assignments in `THEME_COLORS`.
- **Concentric Border-Radius Invariant:** Outer surfaces (`.card`, `.callout`, standalone `.chart-box`) use `--radius-lg` (`14px`), while nested containers inside `.card` (`.mini-stat`, `.card .chart-box`, `select`, `.btn-secondary`) use `--radius-md` (`8px`) and `--radius-sm` (`6px`) to eliminate corner pinching ($R_{\text{inner}} \le R_{\text{outer}} - \text{padding}$).
- **Interactive States & Accessibility:** Every interactive button and `<select>` implements `:hover`, `:focus-visible`, `:active`, and `:disabled` styles. Language toggle buttons specify `type="button"` and synchronize `aria-pressed`. State notices expose `role="status"` and `aria-live="polite"`.
- **Layout Stability (Zero CLS):** In `app.py` Tab 2, primary controls stay fixed in a 4-column grid while the conditional `Motion State` selector occupies a dedicated slot in the secondary control row alongside the permutation slider and reset button, preventing column shifts when changing `Astronomical Dimension`.
- **Language & Asset Hygiene:** Uses ISO language codes (`EN` / `ES`) and deterministic astronomical Unicode symbols (`♈`–`♓`, `☿`–`♄`) with zero country flag emojis.
