"""Build the standalone interactive Data Story website (``site/index.html``)."""

from __future__ import annotations

import json
from pathlib import Path

from src.incidents import build_and_save_dataset
from src.stats import run_full_study

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Mercury in Prod — Ephemeris vs. Software Incidents</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {
      --bg: #0b1120;
      --bg-hero: #172554;
      --surface: #111827;
      --surface-alt: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --accent-contrast: #082f49;
      --accent-2: #f97316;
      --ok: #10b981;
      --danger: #ef4444;
      --null-color: #64748b;
      --badge-null-text: #cbd5e1;
      --badge-hit-text: #fdba74;
      --badge-fdr-text: #6ee7b7;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: radial-gradient(circle at top right, var(--bg-hero) 0%, var(--bg) 48%);
      color: var(--text);
      line-height: 1.6;
    }
    .container {
      max-width: 1180px;
      margin: 0 auto;
      padding: 2rem 1.25rem 4rem;
    }
    header {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: flex-start;
      gap: 1rem;
      padding-bottom: 1.75rem;
      border-bottom: 1px solid var(--border);
    }
    .eyebrow {
      font-size: 0.78rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--accent);
      font-weight: 700;
      margin-bottom: 0.4rem;
    }
    h1 {
      margin: 0 0 0.5rem;
      font-size: clamp(1.9rem, 3.6vw, 2.8rem);
      line-height: 1.15;
    }
    .subtitle {
      max-width: 760px;
      color: var(--muted);
      margin: 0;
      font-size: 1.02rem;
    }
    .lang-switch {
      display: inline-flex;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 0.25rem;
      gap: 0.25rem;
    }
    .lang-btn {
      border: none;
      background: transparent;
      color: var(--muted);
      padding: 0.4rem 0.9rem;
      border-radius: 999px;
      cursor: pointer;
      font-weight: 600;
      font-size: 0.85rem;
    }
    .lang-btn:hover:not(.active) {
      color: var(--text);
      background: rgba(148, 163, 184, 0.12);
    }
    .lang-btn.active {
      background: var(--accent);
      color: var(--accent-contrast);
    }
    .lang-btn:focus-visible,
    select:focus-visible {
      outline: 2px solid var(--accent);
      outline-offset: 2px;
    }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem;
      margin: 1.75rem 0;
    }
    .card {
      background: rgba(17, 24, 39, 0.88);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.2rem 1.25rem;
    }
    .kpi-label {
      font-size: 0.82rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .kpi-value {
      font-size: 1.85rem;
      font-weight: 700;
      margin: 0.3rem 0 0.2rem;
    }
    .kpi-sub {
      font-size: 0.85rem;
      color: var(--muted);
    }
    .callout {
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.12), rgba(249, 115, 22, 0.08));
      border: 1px solid rgba(56, 189, 248, 0.35);
      border-radius: 14px;
      padding: 1.25rem 1.4rem;
      margin: 1.5rem 0 2rem;
    }
    .callout strong { color: var(--accent); }
    section {
      margin-top: 2.5rem;
    }
    h2 {
      font-size: 1.45rem;
      margin: 0 0 0.4rem;
    }
    .section-desc {
      color: var(--muted);
      margin: 0 0 1rem;
      max-width: 860px;
    }
    .chart-box {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 0.75rem;
      min-height: 410px;
    }
    .controls {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      align-items: flex-end;
      margin-bottom: 1rem;
    }
    .control-group {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      min-width: 240px;
    }
    label {
      font-size: 0.82rem;
      color: var(--muted);
      font-weight: 600;
    }
    select {
      background: var(--surface-alt);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.55rem 0.75rem;
      font-size: 0.95rem;
    }
    select:hover {
      border-color: var(--muted);
    }
    .explorer-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 0.75rem;
      margin-bottom: 1rem;
    }
    .mini-stat {
      background: var(--surface-alt);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 0.75rem 0.9rem;
    }
    .mini-stat .label { font-size: 0.76rem; color: var(--muted); }
    .mini-stat .val { font-size: 1.2rem; font-weight: 700; margin-top: 0.2rem; }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
      margin-top: 1rem;
    }
    th, td {
      text-align: left;
      padding: 0.65rem 0.75rem;
      border-bottom: 1px solid var(--border);
    }
    th {
      color: var(--muted);
      font-weight: 600;
      font-size: 0.8rem;
      text-transform: uppercase;
    }
    .badge {
      display: inline-block;
      padding: 0.15rem 0.55rem;
      border-radius: 999px;
      font-size: 0.76rem;
      font-weight: 600;
    }
    .badge-null { background: rgba(148, 163, 184, 0.2); color: var(--badge-null-text); }
    .badge-hit { background: rgba(249, 115, 22, 0.2); color: var(--badge-hit-text); }
    .badge-fdr { background: rgba(16, 185, 129, 0.2); color: var(--badge-fdr-text); }
    footer {
      margin-top: 3.5rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--border);
      color: var(--muted);
      font-size: 0.86rem;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <div class="eyebrow" data-i18n="eyebrow"></div>
        <h1 data-i18n="title"></h1>
        <p class="subtitle" data-i18n="subtitle"></p>
      </div>
      <div class="lang-switch" role="group" aria-label="Language switch">
        <button class="lang-btn active" id="btn-en" onclick="setLang('en')">EN</button>
        <button class="lang-btn" id="btn-es" onclick="setLang('es')">ES</button>
      </div>
    </header>

    <div class="kpi-grid" id="kpi-grid"></div>

    <div class="callout" id="verdict-callout"></div>

    <section>
      <h2 data-i18n="sec1_title"></h2>
      <p class="section-desc" data-i18n="sec1_desc"></p>
      <div class="chart-box" id="chart-timeline"></div>
    </section>

    <section>
      <h2 data-i18n="sec2_title"></h2>
      <p class="section-desc" data-i18n="sec2_desc"></p>
      <div class="chart-box" id="chart-forest"></div>
    </section>

    <section>
      <h2 data-i18n="sec3_title"></h2>
      <p class="section-desc" data-i18n="sec3_desc"></p>
      <div class="chart-box" id="chart-volcano"></div>
      <div class="card" style="margin-top: 1rem; overflow-x: auto;">
        <h3 style="margin-top:0; font-size: 1.05rem;" data-i18n="top_hits_title"></h3>
        <table id="top-hits-table"></table>
      </div>
    </section>

    <section>
      <h2 data-i18n="sec4_title"></h2>
      <p class="section-desc" data-i18n="sec4_desc"></p>
      <div class="chart-box" id="chart-real-audit"></div>
    </section>

    <section>
      <h2 data-i18n="sec5_title"></h2>
      <p class="section-desc" data-i18n="sec5_desc"></p>
      <div class="card">
        <div class="controls">
          <div class="control-group">
            <label for="select-hypothesis" data-i18n="lbl_hypothesis"></label>
            <select id="select-hypothesis" onchange="renderExplorer()"></select>
          </div>
          <div class="control-group">
            <label for="select-slice" data-i18n="lbl_slice"></label>
            <select id="select-slice" onchange="renderExplorer()"></select>
          </div>
        </div>
        <div class="explorer-stats" id="explorer-stats"></div>
        <div class="chart-box" id="chart-explorer" style="min-height: 360px;"></div>
      </div>
    </section>

    <footer>
      <span data-i18n="footer_note"></span>
    </footer>
  </div>

  <script>
    const STUDY_DATA = __STUDY_JSON__;
    let currentLang = "en";

    const I18N = {
      en: {
        eyebrow: "Empirical Ephemeris & Spurious Correlation Lab",
        title: "Mercury in Prod: Do Planets Break Deployments?",
        subtitle: "A 2,130-day statistical audit pairing an exact Python port of One UI Extra Widgets' AstrologyEngine with production incident dynamics and 400 real public Statuspage outages.",
        sec1_title: "1. Apparent Orbital Speed vs. Daily Incident Volume",
        sec1_desc: "Mercury's daily geocentric angular speed (orange) dips below zero three times a year during retrograde loops. The 14-day rolling average of software incidents (cyan) follows release freezes and workweeks rather than orbital loops.",
        sec2_title: "2. Confounder-Controlled Poisson GLM (Incident Rate Ratios)",
        sec2_desc: "Once engineering calendar confounders (weekends, Tue–Thu deploy windows, Patch Tuesday, and Q4 code freeze) are controlled in a robust Poisson GLM, every astrological predictor sits squarely at IRR = 1.0.",
        sec3_title: "3. P-Hacking Scan: 57 Hypotheses & Multiple-Testing Correction",
        sec3_desc: "Testing 57 planetary, lunar, and zodiacal slices without correction produces naive hits below p = 0.05. Benjamini-Hochberg FDR eliminates random noise hits—and exposes how the lone FDR survivor (Sun in Capricorn) is actually seasonal confounding from the December Q4 code freeze.",
        top_hits_title: "Lowest Raw p-Values Before & After Multiple-Testing Correction",
        sec4_title: "4. Real Public Statuspage Audit (8 Cloud & Dev Platforms)",
        sec4_desc: "Cross-referencing 400 real incidents fetched from GitHub, Cloudflare, npm, Discord, Reddit, Bitbucket, Vercel, and DigitalOcean against each provider's exact date-window base rate shows zero excess outage risk.",
        sec5_title: "5. Interactive Hypothesis Explorer",
        sec5_desc: "Inspect any planetary motion state or lunar phase directly in the browser, and toggle weekday filtering to see how calendar selection bias distorts naive rates.",
        lbl_hypothesis: "Astrological Condition",
        lbl_slice: "Calendar Slice",
        footer_note: "Built with astronomy-engine, statsmodels, and Plotly. Ephemeris logic matches AstrologyEngine.kt from one-ui-extra-widgets.",
      },
      es: {
        eyebrow: "Laboratorio Empírico de Efemérides y Correlaciones Espurias",
        title: "Mercury in Prod: ¿Los planetas rompen producción?",
        subtitle: "Auditoría estadística de 2,130 días que cruza una réplica exacta en Python de AstrologyEngine (One UI Extra Widgets) con dinámicas operativas de software y 400 incidentes públicos reales de Statuspage.",
        sec1_title: "1. Velocidad Orbital Aparente vs. Volumen Diario de Incidentes",
        sec1_desc: "La velocidad angular geocéntrica diaria de Mercurio (naranja) cae bajo cero tres veces al año durante cada retrogradación. La media móvil de 14 días de incidentes (cian) sigue semanas laborales y congelamientos de código, no las órbitas.",
        sec2_title: "2. Modelo GLM de Poisson Controlado por Confusores (IRR)",
        sec2_desc: "Al controlar los confusores reales de ingeniería (fines de semana, ventanas Mar–Jue, Patch Tuesday y Code Freeze de fin de año), todos los predictores astrológicos colapsan alrededor de IRR = 1.0.",
        sec3_title: "3. Escaneo de P-Hacking: 57 Hipótesis y Corrección FDR / Bonferroni",
        sec3_desc: "Probar 57 hipótesis planetarias, lunares y zodiacales sin ajuste produce falsos positivos con p < 0.05. La corrección FDR de Benjamini-Hochberg elimina el ruido aleatorio y revela que el único sobreviviente (Sol en Capricornio) es confusión estacional por el Code Freeze de diciembre.",
        top_hits_title: "Menores p-values crudos antes y después de corregir por múltiples hipótesis",
        sec4_title: "4. Auditoría sobre Incidentes Reales de Statuspage (8 Plataformas)",
        sec4_desc: "Al contrastar 400 incidentes reales de GitHub, Cloudflare, npm, Discord, Reddit, Bitbucket, Vercel y DigitalOcean contra la tasa base exacta de cada ventana temporal, no aparece exceso de riesgo.",
        sec5_title: "5. Explorador Interactivo de Hipótesis",
        sec5_desc: "Explora cualquier estado planetario o fase lunar directamente en el navegador y activa filtros de días laborales para observar el sesgo de selección de calendario.",
        lbl_hypothesis: "Condición Astrológica",
        lbl_slice: "Filtro de Calendario",
        footer_note: "Construido con astronomy-engine, statsmodels y Plotly. La lógica de efemérides replica AstrologyEngine.kt de one-ui-extra-widgets.",
      }
    };

    const THEME = {
      text: "#e2e8f0",
      grid: "#1e293b",
      border: "#334155",
      muted: "#94a3b8",
      mutedLight: "#cbd5e1",
      nullColor: "#64748b",
      accent: "#38bdf8",
      accent2: "#f97316",
      ok: "#10b981",
      danger: "#ef4444",
    };

    const layoutBase = {
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(15,23,42,0.65)",
      font: { color: THEME.text, family: "Inter, sans-serif" },
      margin: { t: 48, r: 28, b: 52, l: 60 },
      xaxis: { gridcolor: THEME.grid, zerolinecolor: THEME.border },
      yaxis: { gridcolor: THEME.grid, zerolinecolor: THEME.border },
    };

    function setLang(lang) {
      currentLang = lang;
      document.getElementById("btn-en").classList.toggle("active", lang === "en");
      document.getElementById("btn-es").classList.toggle("active", lang === "es");
      renderAll();
    }

    function renderStaticText() {
      const dict = I18N[currentLang];
      document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (dict[key]) el.textContent = dict[key];
      });
    }

    function renderKpis() {
      const s = STUDY_DATA.summary;
      const scan = STUDY_DATA.phacking_scan;
      const retroGlm = STUDY_DATA.controlled_glm.terms.find(t => t.term === "is_mercury_retrograde");
      const isEs = currentLang === "es";

      const cards = [
        {
          label: isEs ? "Días Analizados" : "Panel Horizon",
          value: s.panel_days.toLocaleString(),
          sub: `${s.start_date} -> ${s.end_date}`,
        },
        {
          label: isEs ? "Incidentes Reales Statuspage" : "Real Statuspage Incidents",
          value: s.real_public_incidents_count.toLocaleString(),
          sub: isEs ? `${s.real_public_sources_count} plataformas tech públicas` : `${s.real_public_sources_count} public tech platforms`,
        },
        {
          label: isEs ? "IRR Mercurio Retrógrado (GLM)" : "Mercury Retrograde IRR (GLM)",
          value: `${retroGlm.irr.toFixed(2)}x`,
          sub: `95% CI [${retroGlm.ci_low.toFixed(2)}, ${retroGlm.ci_high.toFixed(2)}] · p=${retroGlm.p_value.toFixed(2)}`,
        },
        {
          label: isEs ? "Hits Ingenuos vs FDR" : "Naive Hits vs FDR",
          value: `${scan.naive_hits_count} -> ${scan.fdr_survivors_count}`,
          sub: isEs ? `de ${scan.total_hypotheses} hipótesis (1 confusión estacional)` : `of ${scan.total_hypotheses} tests (1 seasonal confounder)`,
        },
      ];

      document.getElementById("kpi-grid").innerHTML = cards.map(c => `
        <div class="card">
          <div class="kpi-label">${c.label}</div>
          <div class="kpi-value">${c.value}</div>
          <div class="kpi-sub">${c.sub}</div>
        </div>
      `).join("");

      const verdictHtml = isEs
        ? `<strong>Veredicto estadístico:</strong> Los despliegues no fallan por Mercurio retrógrado. El factor dominante es el calendario humano: los fines de semana reducen los incidentes un <strong>69%</strong> (IRR = 0.31, p &lt; 0.0001) y las ventanas de despliegue de martes a jueves los elevan un <strong>23%</strong> (IRR = 1.23, p &lt; 0.0001).`
        : `<strong>Statistical Verdict:</strong> Production outages do not track Mercury retrograde. Human release calendars drive the variance: weekends reduce incident rates by <strong>69%</strong> (IRR = 0.31, p &lt; 0.0001), while Tue–Thu deploy windows raise them by <strong>23%</strong> (IRR = 1.23, p &lt; 0.0001).`;
      document.getElementById("verdict-callout").innerHTML = verdictHtml;
    }

    function renderTimeline() {
      const isEs = currentLang === "es";
      const rows = STUDY_DATA.timeline;
      const dates = rows.map(r => r.date);
      const speeds = rows.map(r => r.mercury_daily_speed_deg);
      const counts = rows.map(r => r.incident_count);

      // 14-day rolling mean
      const rolling = counts.map((_, idx) => {
        const start = Math.max(0, idx - 13);
        const slice = counts.slice(start, idx + 1);
        return slice.reduce((a, b) => a + b, 0) / slice.length;
      });

      const traceInc = {
        x: dates,
        y: rolling,
        name: isEs ? "Incidentes (Media móvil 14d)" : "Incidents (14d Rolling Mean)",
        type: "scatter",
        mode: "lines",
        line: { color: THEME.accent, width: 2 },
      };

      const traceSpeed = {
        x: dates,
        y: speeds,
        name: isEs ? "Velocidad Mercurio (°/día)" : "Mercury Speed (°/day)",
        type: "scatter",
        mode: "lines",
        yaxis: "y2",
        line: { color: THEME.accent2, width: 1.4 },
        opacity: 0.85,
      };

      const layout = {
        ...layoutBase,
        title: isEs ? "Serie Temporal 2021–2026: Velocidad de Mercurio vs Incidentes" : "2021–2026 Time Series: Mercury Speed vs Incidents",
        yaxis: { ...layoutBase.yaxis, title: isEs ? "Incidentes / día (14d MA)" : "Incidents / day (14d MA)" },
        yaxis2: {
          title: isEs ? "Velocidad (°/día)" : "Speed (°/day)",
          overlaying: "y",
          side: "right",
          gridcolor: "rgba(0,0,0,0)",
          zeroline: true,
          zerolinecolor: THEME.danger,
        },
        legend: { orientation: "h", y: 1.12 },
      };
      Plotly.newPlot("chart-timeline", [traceInc, traceSpeed], layout, { responsive: true });
    }

    function renderForest() {
      const isEs = currentLang === "es";
      const terms = [...STUDY_DATA.controlled_glm.terms].reverse();
      const labels = terms.map(t => isEs ? t.label_es : t.label_en);
      const irrs = terms.map(t => t.irr);
      const errPlus = terms.map(t => t.ci_high - t.irr);
      const errMinus = terms.map(t => t.irr - t.ci_low);
      const colors = terms.map(t => t.category === "engineering" ? THEME.accent : THEME.accent2);

      const trace = {
        x: irrs,
        y: labels,
        type: "scatter",
        mode: "markers",
        marker: { color: colors, size: 11 },
        error_x: {
          type: "data",
          symmetric: false,
          array: errPlus,
          arrayminus: errMinus,
          color: THEME.mutedLight,
          thickness: 1.8,
        },
        hovertemplate: "%{y}<br>IRR: %{x:.3f}<extra></extra>",
      };

      const layout = {
        ...layoutBase,
        margin: { t: 48, r: 30, b: 50, l: 250 },
        title: isEs ? "Forest Plot GLM Controlado (IRR con IC 95%)" : "Controlled GLM Forest Plot (IRR with 95% CI)",
        xaxis: { ...layoutBase.xaxis, title: "Incident Rate Ratio (1.0 = No Effect)" },
        shapes: [{
          type: "line", x0: 1.0, x1: 1.0, y0: -0.5, y1: terms.length - 0.5,
          line: { color: THEME.muted, dash: "dash", width: 1.5 },
        }],
      };
      Plotly.newPlot("chart-forest", [trace], layout, { responsive: true });
    }

    function renderVolcano() {
      const isEs = currentLang === "es";
      const scan = STUDY_DATA.phacking_scan;
      const hyps = scan.hypotheses;

      const groups = [
        {
          key: "null",
          name: isEs ? "Nulo (p >= 0.05)" : "Null (p >= 0.05)",
          color: THEME.nullColor,
          items: hyps.filter(h => !h.naive_hit),
        },
        {
          key: "naive",
          name: isEs ? "Falso Hit Ingenuo (p < 0.05, falla FDR)" : "Naive Hit Only (fails FDR)",
          color: THEME.accent2,
          items: hyps.filter(h => h.naive_hit && !h.survives_fdr),
        },
        {
          key: "fdr",
          name: isEs ? "Sobrevive FDR (Confusión estacional Dic)" : "Survives FDR (Dec Freeze Confounder)",
          color: THEME.ok,
          items: hyps.filter(h => h.survives_fdr),
        },
      ];

      const traces = groups.map(g => ({
        x: g.items.map(h => h.log2_fold_change),
        y: g.items.map(h => h.neg_log10_p),
        text: g.items.map(h => `${isEs ? h.label_es : h.label_en}<br>RR=${h.rate_ratio} · p_raw=${h.p_raw} · q_FDR=${h.q_fdr}`),
        name: g.name,
        mode: "markers",
        type: "scatter",
        marker: { color: g.color, size: 10 },
        hovertemplate: "%{text}<extra></extra>",
      }));

      const bonfY = -Math.log10(0.05 / scan.total_hypotheses);
      const rawY = -Math.log10(0.05);

      const layout = {
        ...layoutBase,
        title: isEs ? "Gráfico Volcán de 57 Hipótesis Astrológicas" : "Volcano Plot of 57 Astrological Hypotheses",
        xaxis: { ...layoutBase.xaxis, title: "log2(Incident Rate Ratio)" },
        yaxis: { ...layoutBase.yaxis, title: "-log10(raw p-value)" },
        legend: { orientation: "h", y: 1.13 },
        shapes: [
          { type: "line", x0: -0.6, x1: 0.6, y0: rawY, y1: rawY, line: { color: THEME.accent2, dash: "dash" } },
          { type: "line", x0: -0.6, x1: 0.6, y0: bonfY, y1: bonfY, line: { color: THEME.danger, dash: "dot" } },
        ],
      };
      Plotly.newPlot("chart-volcano", traces, layout, { responsive: true });

      const topRows = hyps.slice(0, 10);
      const headers = isEs
        ? ["Hipótesis", "Familia", "N Expuesto", "Rate Ratio", "p crudo", "q (BH-FDR)", "p (Bonf.)", "Estado"]
        : ["Hypothesis", "Family", "Exposed N", "Rate Ratio", "Raw p", "q (BH-FDR)", "Bonferroni p", "Status"];

      const tableHtml = `
        <thead><tr>${headers.map(h => `<th>${h}</th>`).join("")}</tr></thead>
        <tbody>
          ${topRows.map(r => {
            const label = isEs ? r.label_es : r.label_en;
            const badge = r.survives_fdr
              ? `<span class="badge badge-fdr">${isEs ? "Sobrevive FDR (Confusión Dic)" : "FDR Survivor (Dec Confounder)"}</span>`
              : r.naive_hit
              ? `<span class="badge badge-hit">${isEs ? "Falso Positivo Ingenuo" : "Naive False Hit"}</span>`
              : `<span class="badge badge-null">${isEs ? "Nulo" : "Null"}</span>`;
            return `<tr>
              <td>${label}</td>
              <td>${r.family}</td>
              <td>${r.n_exposed}</td>
              <td>${r.rate_ratio.toFixed(3)}x</td>
              <td>${r.p_raw.toFixed(4)}</td>
              <td>${r.q_fdr.toFixed(4)}</td>
              <td>${r.p_bonferroni.toFixed(4)}</td>
              <td>${badge}</td>
            </tr>`;
          }).join("")}
        </tbody>
      `;
      document.getElementById("top-hits-table").innerHTML = tableHtml;
    }

    function renderRealAudit() {
      const isEs = currentLang === "es";
      const tests = STUDY_DATA.real_statuspage_audit.tests || [];
      const labels = tests.map(t => `${isEs ? t.label_es : t.label_en} (p=${t.p_value.toFixed(2)})`);

      const traceObs = {
        x: labels,
        y: tests.map(t => t.observed_pct),
        name: isEs ? "Observado (%)" : "Observed (%)",
        type: "bar",
        marker: { color: THEME.accent2 },
      };
      const traceExp = {
        x: labels,
        y: tests.map(t => t.expected_pct),
        name: isEs ? "Esperado por Ventana (%)" : "Window-Expected (%)",
        type: "bar",
        marker: { color: THEME.accent },
      };

      const layout = {
        ...layoutBase,
        barmode: "group",
        title: isEs
          ? "400 Incidentes Reales de Statuspage: Observado vs Tasa Astronómica Esperada"
          : "400 Real Statuspage Incidents: Observed vs Expected Astronomical Base Rate",
        yaxis: { ...layoutBase.yaxis, title: isEs ? "Porcentaje de Incidentes (%)" : "Share of Incidents (%)" },
        legend: { orientation: "h", y: 1.12 },
      };
      Plotly.newPlot("chart-real-audit", [traceObs, traceExp], layout, { responsive: true });
    }

    function populateExplorerDropdowns() {
      const isEs = currentLang === "es";
      const hypSel = document.getElementById("select-hypothesis");
      const prevHyp = hypSel.value || "mercury_retrograde";
      const opts = Object.values(STUDY_DATA.explorer.options);
      hypSel.innerHTML = opts.map(o => `<option value="${o.id}">${isEs ? o.label_es : o.label_en}</option>`).join("");
      hypSel.value = opts.some(o => o.id === prevHyp) ? prevHyp : opts[0].id;

      const sliceSel = document.getElementById("select-slice");
      const prevSlice = sliceSel.value || "all";
      const slices = [
        { id: "all", en: "All Days (Unfiltered)", es: "Todos los días (Sin filtro)" },
        { id: "weekdays", en: "Weekdays Only (Mon–Fri)", es: "Solo laborales (Lun–Vie)" },
        { id: "weekends", en: "Weekends Only (Sat–Sun)", es: "Solo fines de semana (Sáb–Dom)" },
      ];
      sliceSel.innerHTML = slices.map(s => `<option value="${s.id}">${isEs ? s.es : s.en}</option>`).join("");
      sliceSel.value = prevSlice;
    }

    function renderExplorer() {
      const isEs = currentLang === "es";
      const hypId = document.getElementById("select-hypothesis").value;
      const sliceId = document.getElementById("select-slice").value;
      const option = STUDY_DATA.explorer.options[hypId];
      const data = option.slices[sliceId];

      const statsCards = [
        { label: isEs ? "Días Expuestos" : "Exposed Days", val: `${data.n_exposed} / ${data.n_exposed + data.n_baseline}` },
        { label: isEs ? "Media Expuesta vs Base" : "Exposed vs Baseline Mean", val: `${data.mean_exposed.toFixed(2)} vs ${data.mean_baseline.toFixed(2)}` },
        { label: "Rate Ratio", val: `${data.rate_ratio.toFixed(3)}x (${data.pct_diff >= 0 ? "+" : ""}${data.pct_diff.toFixed(1)}%)` },
        { label: "Welch p / Perm p", val: `${data.p_raw.toFixed(4)} / ${data.p_perm.toFixed(4)}` },
        { label: "BH-FDR q", val: data.q_fdr !== null && data.q_fdr !== undefined ? data.q_fdr.toFixed(4) : "N/A (Slice)" },
      ];

      document.getElementById("explorer-stats").innerHTML = statsCards.map(s => `
        <div class="mini-stat">
          <div class="label">${s.label}</div>
          <div class="val">${s.val}</div>
        </div>
      `).join("");

      const bins = STUDY_DATA.explorer.bins;
      const tExp = {
        x: bins,
        y: data.exposed_hist_pct,
        name: isEs ? "Días Expuestos (%)" : "Exposed Days (%)",
        type: "bar",
        marker: { color: THEME.accent2 },
        opacity: 0.78,
      };
      const tBase = {
        x: bins,
        y: data.baseline_hist_pct,
        name: isEs ? "Línea Base (%)" : "Baseline Days (%)",
        type: "bar",
        marker: { color: THEME.accent },
        opacity: 0.78,
      };
      const layout = {
        ...layoutBase,
        barmode: "group",
        title: `${isEs ? option.label_es : option.label_en}`,
        xaxis: { ...layoutBase.xaxis, title: isEs ? "Incidentes diarios" : "Daily Incident Count" },
        yaxis: { ...layoutBase.yaxis, title: isEs ? "Frecuencia (%)" : "Share of Days (%)" },
        legend: { orientation: "h", y: 1.15 },
      };
      Plotly.newPlot("chart-explorer", [tExp, tBase], layout, { responsive: true });
    }

    function renderAll() {
      renderStaticText();
      renderKpis();
      renderTimeline();
      renderForest();
      renderVolcano();
      renderRealAudit();
      populateExplorerDropdowns();
      renderExplorer();
    }

    renderAll();
  </script>
</body>
</html>
"""


def build_static_site(
    data_dir: Path | str = Path("data"),
    site_dir: Path | str = Path("site"),
    refresh_data: bool = False,
) -> Path:
    """Ensure study results exist and write standalone ``site/index.html``."""
    data_path = Path(data_dir)
    out_dir = Path(site_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    merged_csv = data_path / "daily_incidents_ephemeris.csv"
    study_json = data_path / "study_results.json"

    if refresh_data or not merged_csv.exists():
        build_and_save_dataset(data_dir=data_path, force_refresh=refresh_data)
    if refresh_data or not study_json.exists():
        study_payload = run_full_study(data_dir=data_path)
    else:
        study_payload = json.loads(study_json.read_text(encoding="utf-8"))

    compact_json = json.dumps(study_payload, separators=(",", ":"))
    html_output = HTML_TEMPLATE.replace("__STUDY_JSON__", compact_json)
    index_path = out_dir / "index.html"
    index_path.write_text(html_output, encoding="utf-8")
    return index_path


if __name__ == "__main__":
    output_file = build_static_site()
    print(f"Generated static site at: {output_file}")
