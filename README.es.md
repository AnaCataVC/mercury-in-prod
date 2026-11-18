[English](README.md) | [Español](README.es.md)

# Mercury in Prod

[![CI](https://img.shields.io/github/actions/workflow/status/AnaCataVC/mercury-in-prod/ci.yml?branch=main&style=flat&logo=githubactions&logoColor=white&label=CI)](https://github.com/AnaCataVC/mercury-in-prod/actions)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.36%2B-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.22%2B-3F4F75?style=flat&logo=plotly&logoColor=white)](https://plotly.com/python/)

Laboratorio empírico de Data Science que evalúa si **Mercurio retrógrado**, las sombras planetarias o las fases lunares tienen relación con incidentes en producción de software, y demuestra cómo los **confusores de calendario** y el **testeo de múltiples hipótesis (*p-hacking*)** generan patrones ilusorios.

- **Data Story en Vivo (Estática):** https://mercury.ana-catalina.com
- **Laboratorio Exploratorio en Vivo (Streamlit):** https://mercury-lab.ana-catalina.com ([URL directa en Streamlit](https://mercury-anacatavc.streamlit.app/))

El motor de efemérides (`src/ephemeris.py`) es una réplica exacta en Python de `AstrologyEngine.kt` de `one-ui-extra-widgets`, impulsado por [`astronomy-engine`](https://pypi.org/project/astronomy-engine/) para cálculos astronómicos 100% deterministas y sin conexión.

---

## Hallazgos Principales

- **Auditoría sobre Incidentes Públicos Reales (400 incidentes en 8 plataformas):** Al cruzar incidentes públicos recientes de GitHub, Cloudflare, npm, Discord, Reddit, Bitbucket, Vercel y DigitalOcean contra la tasa base exacta de la ventana temporal de cada proveedor, no existe exceso de riesgo (`Mercurio Retrógrado`: 31.0% observado vs 29.5% esperado, `p = 0.51`; `Sombra de Mercurio`: 26.0% vs 26.1%, `p = 1.00`; `Luna Llena`: 8.5% vs 11.0%, `p = 0.11`).
- **GLM de Poisson Controlado por Confusores (2,130 días, 2021–2026):** Con errores estándar robustos HC3, el calendario humano explica la varianza (`Fin de semana IRR = 0.31`, `p < 0.0001`; `Ventana de despliegues Mar–Jue IRR = 1.23`, `p < 0.0001`; `Patch Tuesday IRR = 1.31`, `p = 0.0007`; `Code Freeze Q4 IRR = 0.63`, `p = 0.0011`), mientras `Mercurio Retrógrado` (`IRR = 0.98`, `p = 0.71`), `Sombra de Mercurio` (`IRR = 1.05`, `p = 0.30`) y `Luna Llena` (`IRR = 0.91`, `p = 0.16`) permanecen nulos.
- **P-Hacking y Confusión Estacional (57 hipótesis):** Evaluar 57 cortes planetarios, lunares y zodiacales arroja 7 falsos hallazgos ingenuos con `p < 0.05`. La corrección FDR de Benjamini-Hochberg elimina el ruido aleatorio (`Sol en Sagitario`, `Luna en Tauro`, `Luna Llena en Días Laborales`) y revela que el único sobreviviente (`Sol en Capricornio`) corresponde en realidad al *Code Freeze* de diciembre.

---

## Arquitectura del Proyecto

```text
mercury-in-prod/
├── .github/
│   └── workflows/
│       └── ci.yml            # Pipeline CI con Ruff, pytest y verificación del sitio estático
├── docs/
│   └── ux/
│       └── mercury-in-prod-lab.md  # Especificación UX de 5 estados y contrato de interacción
├── src/
│   ├── ephemeris.py          # Réplica exacta de AstrologyEngine (Sol, Luna, Mercurio–Saturno)
│   ├── incidents.py          # Ingesta pública Statuspage v2 + panel operativo multi-año
│   ├── stats.py              # Pruebas ingenuas, GLM Poisson (HC3), permutaciones, FDR/Bonferroni
│   └── build_site.py         # Genera la Data Story estática + explorador en el navegador
├── data/
│   ├── raw_public_incidents.csv
│   ├── daily_incidents_ephemeris.csv
│   └── study_results.json
├── site/
│   └── index.html            # Versión A: Data Story estática (lista para GitHub Pages / Vercel)
├── app.py                    # Versión B: Laboratorio exploratorio dinámico (Streamlit)
├── tests/
│   ├── test_ephemeris.py     # Tests de paridad con AstrologyEngineTest.kt
│   ├── test_incidents.py     # Tests de ingesta Statuspage, deduplicación y fallback en caché
│   ├── test_stats.py         # Invariantes del motor estadístico y corrección múltiple
│   └── test_build_site.py    # Tests de generación HTML estática y contrato JSON embebido
├── pyproject.toml
└── requirements.txt
```

---

## Inicio Rápido

Crea el entorno virtual e instala las dependencias:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 1. Ejecutar Pruebas Unitarias

```bash
pytest -v
```

### 2. Regenerar Dataset, Estudio Estadístico y Web Estática

```bash
python -m src.build_site
```

Abre `site/index.html` en cualquier navegador o publica la carpeta `site/` directamente en **GitHub Pages** o **Vercel**.

### 3. Iniciar la App Exploratoria (Streamlit)

```bash
streamlit run app.py
```

Se puede desplegar `app.py` directamente en **Streamlit Community Cloud** o **Hugging Face Spaces** apuntando al mismo repositorio.
