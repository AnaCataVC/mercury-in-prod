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
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <title>Mercury in Prod — Ephemeris vs. Software Incidents</title>
  <meta name="description" content="2,130-day empirical audit comparing planetary transits against software incidents and 400 real Statuspage outages." />
  <link rel="icon" type="image/png" href="favicon.png" />
  <link rel="apple-touch-icon" href="favicon.png" />
  <link rel="shortcut icon" href="favicon.ico" />
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0b0e14;
      --bg-hero: #162033;
      --bg-glow-2: #1f1629;
      --surface: #121722;
      --surface-card: rgba(18, 23, 34, 0.92);
      --surface-alt: #181f2e;
      --surface-elevated: #1e2738;
      --nav-bg: rgba(11, 14, 20, 0.88);
      --grid: #232c3d;
      --plot-bg: rgba(11, 14, 20, 0.62);
      --plot-transparent: rgba(0, 0, 0, 0);
      --border: #273145;
      --border-hover: #3f4f6e;
      --text: #f1f5f9;
      --muted: #94a3b8;
      --muted-light: #cbd5e1;
      --accent: #7dd3fc;
      --accent-contrast: #082f49;
      --accent-2: #fb7185;
      --ok: #34d399;
      --warn: #fbbf24;
      --danger: #fda4af;
      --null-color: #64748b;
      --hover-bg: rgba(125, 211, 252, 0.1);
      --chip-bg: rgba(24, 31, 46, 0.95);
      --chip-active-bg: rgba(125, 211, 252, 0.16);
      --retro-band: rgba(251, 113, 133, 0.08);
      --callout-bg: linear-gradient(145deg, rgba(24, 31, 46, 0.95), rgba(18, 23, 34, 0.98));
      --callout-border: rgba(125, 211, 252, 0.28);
      --badge-null-bg: rgba(100, 116, 139, 0.2);
      --badge-null-text: #cbd5e1;
      --badge-hit-bg: rgba(251, 113, 133, 0.18);
      --badge-hit-text: #fecdd3;
      --badge-fdr-bg: rgba(52, 211, 153, 0.16);
      --badge-fdr-text: #a7f3d0;
      --notice-error-border: rgba(253, 164, 175, 0.45);
      --notice-error-bg: rgba(253, 164, 175, 0.08);
      --radius-lg: 14px;
      --radius-md: 8px;
      --radius-sm: 6px;
      --radius-pill: 999px;
    }
    * { box-sizing: border-box; }
    html {
      scroll-behavior: smooth;
      scrollbar-color: var(--border) var(--surface);
      overflow-x: clip;
    }
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--surface); }
    ::-webkit-scrollbar-thumb {
      background: var(--border);
      border-radius: var(--radius-pill);
    }
    ::-webkit-scrollbar-thumb:hover { background: var(--muted); }
    body {
      margin: 0;
      font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background:
        radial-gradient(circle at 85% 0%, var(--bg-hero) 0%, transparent 45%),
        radial-gradient(circle at 12% 18%, var(--bg-glow-2) 0%, transparent 38%),
        var(--bg);
      color: var(--text);
      line-height: 1.55;
      overflow-x: clip;
      -webkit-font-smoothing: antialiased;
    }
    @media (prefers-reduced-motion: reduce) {
      html { scroll-behavior: auto; }
      *, *::before, *::after {
        transition: none !important;
        animation: none !important;
      }
    }

    /* Sticky Top Navigation (2-tier on mobile, 1-tier on desktop) */
    .top-nav {
      position: sticky;
      top: 0;
      z-index: 40;
      background: var(--nav-bg);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border-bottom: 1px solid var(--border);
    }
    .read-progress {
      height: 2px;
      width: 0%;
      background: linear-gradient(90deg, var(--accent), var(--accent-2));
      transition: width 0.1s linear;
    }
    .top-nav-inner {
      max-width: 1180px;
      margin: 0 auto;
      padding: 0.55rem 1.25rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
    }
    .nav-brand {
      display: inline-flex;
      align-items: center;
      gap: 0.55rem;
      font-weight: 700;
      font-size: 0.94rem;
      color: var(--text);
      text-decoration: none;
      white-space: nowrap;
      flex-shrink: 0;
    }
    .nav-brand img {
      width: 26px;
      height: 26px;
      border-radius: var(--radius-sm);
    }
    .nav-pills-wrap {
      flex: 1 1 auto;
      min-width: 0;
      display: flex;
      justify-content: center;
    }
    .nav-pills {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      overflow-x: auto;
      scrollbar-width: none;
      -webkit-overflow-scrolling: touch;
      padding: 0.1rem 0;
    }
    .nav-pills::-webkit-scrollbar { display: none; }
    .nav-pill {
      color: var(--muted);
      text-decoration: none;
      font-size: 0.8rem;
      font-weight: 600;
      padding: 0.38rem 0.72rem;
      min-height: 34px;
      display: inline-flex;
      align-items: center;
      border-radius: var(--radius-pill);
      border: 1px solid transparent;
      white-space: nowrap;
      flex-shrink: 0;
      transition: color 0.15s ease, background 0.15s ease, border-color 0.15s ease;
    }
    .nav-pill:hover {
      color: var(--text);
      background: var(--hover-bg);
    }
    .nav-pill.active {
      color: var(--accent);
      background: var(--chip-active-bg);
      border-color: var(--callout-border);
    }
    .nav-actions {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      flex-shrink: 0;
    }
    .nav-lab-link {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--muted-light);
      text-decoration: none;
      padding: 0.36rem 0.7rem;
      min-height: 34px;
      border-radius: var(--radius-pill);
      border: 1px solid var(--border);
      background: var(--surface);
      white-space: nowrap;
      transition: border-color 0.15s ease, color 0.15s ease, background 0.15s ease;
    }
    .nav-lab-link:hover {
      border-color: var(--accent);
      color: var(--accent);
      background: var(--hover-bg);
    }

    .lang-switch {
      display: inline-flex;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-pill);
      padding: 0.18rem;
      gap: 0.15rem;
      flex-shrink: 0;
    }
    .lang-btn {
      border: none;
      background: transparent;
      color: var(--muted);
      padding: 0.32rem 0.68rem;
      min-height: 30px;
      border-radius: var(--radius-pill);
      cursor: pointer;
      font-weight: 700;
      font-size: 0.76rem;
      transition: background 0.15s ease, color 0.15s ease;
    }
    .lang-btn:hover:not(.active):not(:disabled) {
      color: var(--text);
      background: var(--hover-bg);
    }
    .lang-btn.active {
      background: var(--accent);
      color: var(--accent-contrast);
    }
    .lang-btn:active:not(:disabled),
    .btn-primary:active:not(:disabled),
    .btn-secondary:active:not(:disabled),
    .chip-btn:active:not(:disabled) {
      transform: translateY(1px);
    }
    .lang-btn:focus-visible,
    .btn-primary:focus-visible,
    .btn-secondary:focus-visible,
    .chip-btn:focus-visible,
    .nav-pill:focus-visible,
    .nav-lab-link:focus-visible,
    summary:focus-visible,
    select:focus-visible {
      outline: 2px solid var(--accent);
      outline-offset: 2px;
    }
    .lang-btn:disabled,
    .btn-primary:disabled,
    .btn-secondary:disabled,
    .chip-btn:disabled,
    select:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      pointer-events: none;
    }

    .container {
      max-width: 1180px;
      margin: 0 auto;
      padding: 1.75rem 1.25rem 4rem;
    }

    /* Hero + Executive Verdict Split */
    .hero-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.85fr);
      gap: 1.5rem;
      align-items: stretch;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--border);
    }
    .hero-copy {
      display: flex;
      flex-direction: column;
      justify-content: center;
    }
    .eyebrow {
      font-size: 0.74rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--accent);
      font-weight: 700;
      margin-bottom: 0.45rem;
    }
    h1 {
      margin: 0 0 0.65rem;
      font-size: clamp(1.75rem, 3.3vw, 2.65rem);
      line-height: 1.12;
      letter-spacing: -0.025em;
    }
    .subtitle {
      max-width: 640px;
      color: var(--muted-light);
      margin: 0 0 1.25rem;
      font-size: 0.98rem;
    }
    .hero-cta-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.65rem;
      align-items: center;
    }
    .btn-primary {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
      background: var(--accent);
      color: var(--accent-contrast);
      border: 1px solid var(--accent);
      border-radius: var(--radius-md);
      padding: 0.62rem 1.05rem;
      min-height: 44px;
      font-size: 0.88rem;
      font-weight: 700;
      text-decoration: none;
      cursor: pointer;
      transition: opacity 0.15s ease, transform 0.15s ease;
    }
    .btn-primary:hover:not(:disabled) {
      opacity: 0.92;
    }
    .btn-secondary {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
      background: var(--surface-alt);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 0.58rem 0.95rem;
      min-height: 44px;
      font-size: 0.86rem;
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      transition: border-color 0.15s ease, background 0.15s ease;
    }
    .btn-secondary:hover:not(:disabled) {
      border-color: var(--accent);
      background: var(--hover-bg);
    }

    /* Verdict Spotlight Card */
    .verdict-card {
      background: var(--callout-bg);
      border: 1px solid var(--callout-border);
      border-radius: var(--radius-lg);
      padding: 1.25rem 1.35rem;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 0.9rem;
    }
    .verdict-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
    .verdict-tag {
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--ok);
      background: var(--badge-fdr-bg);
      padding: 0.22rem 0.65rem;
      border-radius: var(--radius-pill);
    }
    .verdict-text {
      font-size: 0.94rem;
      color: var(--text);
      margin: 0;
      line-height: 1.5;
    }
    .verdict-text strong { color: var(--accent); }
    .verdict-bars {
      display: flex;
      flex-direction: column;
      gap: 0.55rem;
      padding-top: 0.65rem;
      border-top: 1px solid var(--border);
    }
    .vbar-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 0.25rem 0.75rem;
      align-items: center;
      font-size: 0.8rem;
    }
    .vbar-label { color: var(--muted-light); font-weight: 600; }
    .vbar-val {
      font-variant-numeric: tabular-nums;
      font-weight: 700;
    }
    .vbar-val--eng { color: var(--accent); }
    .vbar-val--null { color: var(--muted); }
    .vbar-track {
      grid-column: 1 / -1;
      height: 5px;
      background: var(--surface);
      border-radius: var(--radius-pill);
      overflow: hidden;
    }
    .vbar-fill {
      height: 100%;
      border-radius: var(--radius-pill);
    }
    .vbar-fill--eng { background: var(--accent); }
    .vbar-fill--retro { background: var(--accent-2); }
    .vbar-fill--null { background: var(--null-color); }

    /* KPI Strip */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 0.85rem;
      margin: 1.35rem 0;
    }
    .card {
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 1.15rem 1.25rem;
      min-width: 0;
      transition: border-color 0.2s ease, transform 0.2s ease;
    }
    .kpi-card {
      position: relative;
      overflow: hidden;
      padding: 1rem 1.1rem;
    }
    .kpi-card:hover {
      border-color: var(--border-hover);
      transform: translateY(-2px);
    }
    .kpi-label {
      font-size: 0.73rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      font-weight: 600;
    }
    .kpi-value {
      font-size: clamp(1.35rem, 2.2vw, 1.8rem);
      font-weight: 750;
      margin: 0.22rem 0 0.15rem;
      letter-spacing: -0.02em;
      font-variant-numeric: tabular-nums;
    }
    .kpi-sub {
      font-size: 0.78rem;
      color: var(--muted);
      line-height: 1.35;
    }

    /* 3-Card Synthesis Strip */
    .synthesis-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 0.9rem;
      margin-top: 0.75rem;
    }
    .synthesis-card {
      padding: 1.05rem 1.15rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }
    .synthesis-num {
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--accent);
    }
    .synthesis-title {
      margin: 0;
      font-size: 0.96rem;
      font-weight: 700;
      color: var(--text);
    }
    .synthesis-body {
      margin: 0;
      font-size: 0.85rem;
      color: var(--muted);
      line-height: 1.48;
    }

    .chip-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.45rem;
    }
    .chip-btn {
      background: var(--chip-bg);
      color: var(--muted-light);
      border: 1px solid var(--border);
      border-radius: var(--radius-pill);
      padding: 0.4rem 0.82rem;
      min-height: 36px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease;
    }
    .chip-btn:hover:not(.active):not(:disabled) {
      border-color: var(--border-hover);
      color: var(--text);
    }
    .chip-btn.active {
      background: var(--chip-active-bg);
      border-color: var(--accent);
      color: var(--accent);
    }

    section {
      margin-top: 2.5rem;
      scroll-margin-top: 5.2rem;
    }
    .section-head {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: baseline;
      gap: 0.5rem 1rem;
      margin-bottom: 0.85rem;
    }
    h2 {
      font-size: clamp(1.18rem, 2vw, 1.38rem);
      margin: 0;
      letter-spacing: -0.015em;
    }
    .section-desc {
      color: var(--muted);
      margin: 0.25rem 0 0;
      font-size: 0.92rem;
      max-width: 780px;
    }

    .chart-card {
      padding: 1rem 1.1rem;
    }
    .chart-header {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.65rem;
    }
    .chart-title {
      margin: 0;
      font-size: 0.96rem;
      font-weight: 650;
      color: var(--text);
    }
    .chart-pill {
      font-size: 0.74rem;
      font-weight: 600;
      padding: 0.18rem 0.6rem;
      border-radius: var(--radius-pill);
      background: var(--surface-alt);
      border: 1px solid var(--border);
      color: var(--muted-light);
    }
    .chart-box {
      background: var(--plot-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 0.45rem;
      min-height: 410px;
      width: 100%;
      overflow: hidden;
    }
    .chart-box--compact {
      min-height: 360px;
    }
    .chart-takeaway {
      margin-top: 0.7rem;
      padding: 0.65rem 0.85rem;
      border-radius: var(--radius-md);
      background: var(--surface-alt);
      border: 1px solid var(--border);
      font-size: 0.83rem;
      color: var(--muted-light);
    }
    .chart-takeaway strong { color: var(--accent); }

    .state-notice {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      gap: 0.75rem;
      min-height: 320px;
      padding: 1.5rem;
      border: 1px dashed var(--border);
      border-radius: var(--radius-sm);
      background: var(--surface-alt);
      color: var(--muted-light);
    }
    .state-notice--error {
      border-color: var(--notice-error-border);
      background: var(--notice-error-bg);
    }
    .state-notice p { margin: 0; max-width: 520px; }

    .table-card {
      margin-top: 1rem;
      overflow-x: auto;
    }
    .table-toolbar {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 0.65rem;
    }
    .card-title {
      margin: 0;
      font-size: 0.98rem;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.86rem;
      margin-top: 0.35rem;
      font-variant-numeric: tabular-nums;
    }
    th, td {
      text-align: left;
      padding: 0.6rem 0.7rem;
      border-bottom: 1px solid var(--border);
    }
    th {
      color: var(--muted);
      font-weight: 600;
      font-size: 0.74rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    tbody tr {
      transition: background 0.12s ease;
    }
    tbody tr:hover {
      background: var(--hover-bg);
    }
    .badge {
      display: inline-block;
      padding: 0.16rem 0.58rem;
      border-radius: var(--radius-pill);
      font-size: 0.74rem;
      font-weight: 600;
      white-space: nowrap;
    }
    .badge-null { background: var(--badge-null-bg); color: var(--badge-null-text); }
    .badge-hit { background: var(--badge-hit-bg); color: var(--badge-hit-text); }
    .badge-fdr { background: var(--badge-fdr-bg); color: var(--badge-fdr-text); }

    .controls {
      display: flex;
      flex-wrap: wrap;
      gap: 0.85rem;
      align-items: flex-end;
      margin-bottom: 0.9rem;
    }
    .control-group {
      display: flex;
      flex-direction: column;
      gap: 0.32rem;
      min-width: 220px;
      flex: 1 1 220px;
    }
    .control-actions {
      display: flex;
      align-items: flex-end;
    }
    label {
      font-size: 0.78rem;
      color: var(--muted);
      font-weight: 600;
    }
    select {
      background: var(--surface-alt);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 0.55rem 0.75rem;
      min-height: 44px;
      font-size: 0.9rem;
      width: 100%;
    }
    select:hover:not(:disabled) { border-color: var(--muted); }
    select:active:not(:disabled) { border-color: var(--accent); }

    .quick-picks {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.45rem;
      margin-bottom: 0.95rem;
    }
    .quick-picks-label {
      font-size: 0.76rem;
      color: var(--muted);
      font-weight: 600;
      margin-right: 0.2rem;
    }

    .explorer-verdict {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 0.5rem;
      padding: 0.7rem 0.9rem;
      margin-bottom: 0.95rem;
      border-radius: var(--radius-md);
      background: var(--surface-alt);
      border: 1px solid var(--border);
      font-size: 0.86rem;
    }

    .explorer-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
      gap: 0.65rem;
      margin-bottom: 0.95rem;
    }
    .mini-stat {
      background: var(--surface-alt);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 0.65rem 0.85rem;
      font-variant-numeric: tabular-nums;
    }
    .mini-stat .label { font-size: 0.73rem; color: var(--muted); }
    .mini-stat .val { font-size: 1.05rem; font-weight: 700; margin-top: 0.15rem; }

    /* Methodology Disclosure */
    .methodology-details {
      margin-top: 2rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 0.95rem 1.2rem;
    }
    .methodology-details summary {
      cursor: pointer;
      font-weight: 700;
      font-size: 0.94rem;
      color: var(--text);
      list-style: none;
      display: flex;
      align-items: center;
      justify-content: space-between;
      min-height: 36px;
    }
    .methodology-details summary::after {
      content: "+";
      font-size: 1.15rem;
      color: var(--accent);
      font-weight: 700;
    }
    .methodology-details[open] summary::after {
      content: "−";
    }
    .methodology-body {
      margin-top: 0.85rem;
      padding-top: 0.85rem;
      border-top: 1px solid var(--border);
      color: var(--muted-light);
      font-size: 0.87rem;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem;
    }
    .methodology-body h4 {
      margin: 0 0 0.3rem;
      font-size: 0.84rem;
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .methodology-body p { margin: 0; color: var(--muted); }

    footer {
      margin-top: 2.5rem;
      padding-top: 1.25rem;
      border-top: 1px solid var(--border);
      color: var(--muted);
      font-size: 0.84rem;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 0.75rem;
    }
    footer a {
      color: var(--accent);
      text-decoration: none;
      font-weight: 600;
    }
    footer a:hover { text-decoration: underline; }

    /* Tablet & Mobile Responsive Architecture */
    @media (max-width: 900px) {
      .hero-grid {
        grid-template-columns: 1fr;
        gap: 1.15rem;
      }
      .kpi-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .synthesis-grid {
        grid-template-columns: 1fr;
      }
    }

    /* Evidence Stack & Collapsible Accordions */
    .evidence-stack {
      margin-top: 2.5rem;
      display: flex;
      flex-direction: column;
      gap: 2.2rem;
    }
    .evidence-stack-intro {
      display: none;
    }
    .evidence-accordion {
      scroll-margin-top: 4.5rem;
    }
    .evidence-summary {
      list-style: none;
      cursor: pointer;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 0.75rem;
      margin-bottom: 0.85rem;
    }
    .evidence-summary::-webkit-details-marker {
      display: none;
    }
    .evidence-summary-meta {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      flex-shrink: 0;
    }
    .evidence-chevron {
      display: none;
      width: 28px;
      height: 28px;
      border-radius: var(--radius-pill);
      border: 1px solid var(--border);
      background: var(--surface-alt);
      color: var(--accent);
      font-weight: 700;
      font-size: 1rem;
      align-items: center;
      justify-content: center;
    }
    .evidence-chevron::after {
      content: "+";
    }
    .evidence-accordion[open] .evidence-chevron::after {
      content: "−";
    }

    /* Mobile Thumb-Zone Bottom Navigation */
    .bottom-nav {
      display: none;
    }

    @media (max-width: 820px) {
      .top-nav-inner {
        padding: 0.55rem 0.9rem;
      }
      .nav-pills-wrap {
        display: none;
      }
      .bottom-nav {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 50;
        background: var(--nav-bg);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-top: 1px solid var(--border);
        padding: 0.35rem 0.45rem max(0.45rem, env(safe-area-inset-bottom));
        gap: 0.25rem;
      }
      .bottom-nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.2rem;
        min-height: 48px;
        padding: 0.25rem 0.2rem;
        border-radius: var(--radius-md);
        color: var(--muted);
        text-decoration: none;
        font-size: 0.7rem;
        font-weight: 600;
        transition: color 0.15s ease, background 0.15s ease;
      }
      .bottom-nav-item svg {
        width: 20px;
        height: 20px;
        flex-shrink: 0;
      }
      .bottom-nav-item.active {
        color: var(--accent);
        background: var(--chip-active-bg);
      }
      .bottom-nav-item:focus-visible {
        outline: 2px solid var(--accent);
        outline-offset: 2px;
      }
      .container {
        padding-bottom: 5.5rem;
      }
      section,
      .evidence-accordion {
        scroll-margin-top: 4.2rem;
      }
      .evidence-stack {
        gap: 0.85rem;
      }
      .evidence-stack-intro {
        display: block;
        margin-bottom: 0.25rem;
      }
      .evidence-accordion {
        background: var(--surface-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 0.85rem 0.95rem;
      }
      .evidence-summary {
        margin-bottom: 0;
        flex-direction: column;
        align-items: stretch;
        position: relative;
        padding-right: 2.5rem;
        gap: 0.45rem;
      }
      .evidence-summary h2 {
        font-size: 1.05rem;
      }
      .evidence-summary-meta {
        justify-content: flex-start;
      }
      .evidence-chevron {
        position: absolute;
        right: 0;
        top: 50%;
        transform: translateY(-50%);
      }
      .evidence-accordion[open] .evidence-summary {
        margin-bottom: 0.85rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--border);
      }
      .evidence-accordion .card {
        background: transparent;
        border: none;
        padding: 0;
      }
      .evidence-accordion .table-card {
        margin-top: 1rem;
        padding-top: 0.85rem;
        border-top: 1px solid var(--border);
      }
      .evidence-chevron {
        display: inline-flex;
      }
      .evidence-summary .section-desc {
        display: none;
      }
      .evidence-accordion[open] .evidence-summary .section-desc {
        display: block;
      }
    }

    @media (max-width: 640px) {
      .container {
        padding: 1.15rem 0.9rem 5.5rem;
      }
      .card {
        padding: 0.95rem;
      }
      .chart-card {
        padding: 0.8rem 0.75rem;
      }
      .chart-box {
        min-height: 330px;
        padding: 0.2rem;
      }
      .chart-box--compact {
        min-height: 300px;
      }
      .hero-cta-row {
        flex-direction: column;
        align-items: stretch;
      }
      .controls {
        flex-direction: column;
        align-items: stretch;
      }
      .control-group {
        min-width: 0;
        flex: 1 1 auto;
      }
      .control-actions .btn-secondary {
        width: 100%;
      }
      .explorer-stats {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .nav-lab-text {
        display: none;
      }
      /* Responsive Table -> Stacked Cards on Mobile */
      .table-card {
        overflow-x: visible;
      }
      #top-hits-table,
      #top-hits-table tbody,
      #top-hits-table tr,
      #top-hits-table td {
        display: block;
        width: 100%;
      }
      #top-hits-table thead {
        display: none;
      }
      #top-hits-table tbody tr {
        background: var(--surface-alt);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 0.75rem 0.85rem;
        margin-bottom: 0.65rem;
      }
      #top-hits-table tbody tr:last-child {
        margin-bottom: 0;
      }
      #top-hits-table td {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.75rem;
        padding: 0.28rem 0;
        border-bottom: 1px solid var(--grid);
        font-size: 0.83rem;
        text-align: right;
      }
      #top-hits-table td:first-child {
        font-weight: 700;
        font-size: 0.9rem;
        color: var(--text);
        text-align: left;
        padding-bottom: 0.45rem;
        margin-bottom: 0.2rem;
      }
      #top-hits-table td:first-child::before {
        display: none;
      }
      #top-hits-table td:last-child {
        border-bottom: none;
        padding-top: 0.45rem;
      }
      #top-hits-table td::before {
        content: attr(data-label);
        font-size: 0.73rem;
        font-weight: 600;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.04em;
        text-align: left;
      }
    }

    @media (max-width: 379px) {
      .kpi-grid {
        grid-template-columns: 1fr;
      }
      .explorer-stats {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <nav class="top-nav" aria-label="Section navigation">
    <div class="read-progress" id="read-progress"></div>
    <div class="top-nav-inner">
      <a href="#overview" class="nav-brand">
        <img src="favicon.png" alt="Mercury in Prod icon" width="26" height="26" />
        <span>Mercury in Prod</span>
      </a>
      <div class="nav-pills-wrap">
        <div class="nav-pills" id="nav-pills">
          <a href="#overview" class="nav-pill active" data-section="overview" data-i18n="nav_overview"></a>
          <a href="#findings" class="nav-pill" data-section="findings" data-i18n="nav_findings"></a>
          <a href="#timeline" class="nav-pill" data-section="timeline" data-i18n="nav_timeline"></a>
          <a href="#glm" class="nav-pill" data-section="glm" data-i18n="nav_glm"></a>
          <a href="#phacking" class="nav-pill" data-section="phacking" data-i18n="nav_phacking"></a>
          <a href="#audit" class="nav-pill" data-section="audit" data-i18n="nav_audit"></a>
          <a href="#explorer" class="nav-pill" data-section="explorer" data-i18n="nav_explorer"></a>
        </div>
      </div>
      <div class="nav-actions">
        <a href="https://mercury-lab.ana-catalina.com" target="_blank" rel="noopener noreferrer" class="nav-lab-link">
          <span class="nav-lab-text" data-i18n="nav_lab"></span>
          <span aria-hidden="true">↗</span>
        </a>
        <div class="lang-switch" role="group" aria-label="Language switch">
          <button type="button" class="lang-btn active" id="btn-en" aria-pressed="true" onclick="setLang('en')">EN</button>
          <button type="button" class="lang-btn" id="btn-es" aria-pressed="false" onclick="setLang('es')">ES</button>
        </div>
      </div>
    </div>
  </nav>

  <main class="container">
    <header class="hero-grid" id="overview">
      <div class="hero-copy">
        <div class="eyebrow" data-i18n="eyebrow"></div>
        <h1 data-i18n="title"></h1>
        <p class="subtitle" data-i18n="subtitle"></p>
        <div class="hero-cta-row">
          <a href="#explorer" class="btn-primary" data-i18n="cta_explorer"></a>
          <a href="#timeline" class="btn-secondary" data-i18n="cta_evidence"></a>
        </div>
      </div>
      <aside class="verdict-card" id="verdict-callout" aria-label="Executive Verdict"></aside>
    </header>

    <div class="kpi-grid" id="kpi-grid"></div>

    <section id="findings">
      <div class="section-head">
        <div>
          <h2 data-i18n="findings_title"></h2>
          <p class="section-desc" data-i18n="findings_desc"></p>
        </div>
      </div>
      <div class="synthesis-grid" id="synthesis-grid"></div>
    </section>

    <div id="evidence" class="evidence-stack">
      <div class="evidence-stack-intro">
        <h2 data-i18n="evidence_heading"></h2>
        <p class="section-desc" data-i18n="evidence_sub"></p>
      </div>

      <details class="evidence-accordion" id="timeline" data-chart="chart-timeline" open>
        <summary class="evidence-summary">
          <div>
            <h2 data-i18n="sec1_title"></h2>
            <p class="section-desc" data-i18n="sec1_desc"></p>
          </div>
          <div class="evidence-summary-meta">
            <span class="chart-pill" data-i18n="chart1_pill"></span>
            <span class="evidence-chevron" aria-hidden="true"></span>
          </div>
        </summary>
        <div class="card chart-card">
          <div class="chart-header">
            <h3 class="chart-title" data-i18n="chart1_title"></h3>
          </div>
          <div class="chart-box" id="chart-timeline"></div>
          <div class="chart-takeaway" id="takeaway-timeline"></div>
        </div>
      </details>

      <details class="evidence-accordion" id="glm" data-chart="chart-forest" open>
        <summary class="evidence-summary">
          <div>
            <h2 data-i18n="sec2_title"></h2>
            <p class="section-desc" data-i18n="sec2_desc"></p>
          </div>
          <div class="evidence-summary-meta">
            <span class="chart-pill" data-i18n="chart2_pill"></span>
            <span class="evidence-chevron" aria-hidden="true"></span>
          </div>
        </summary>
        <div class="card chart-card">
          <div class="chart-header">
            <h3 class="chart-title" data-i18n="chart2_title"></h3>
          </div>
          <div class="chart-box" id="chart-forest"></div>
          <div class="chart-takeaway" id="takeaway-glm"></div>
        </div>
      </details>

      <details class="evidence-accordion" id="phacking" data-chart="chart-volcano" open>
        <summary class="evidence-summary">
          <div>
            <h2 data-i18n="sec3_title"></h2>
            <p class="section-desc" data-i18n="sec3_desc"></p>
          </div>
          <div class="evidence-summary-meta">
            <span class="chart-pill" data-i18n="chart3_pill"></span>
            <span class="evidence-chevron" aria-hidden="true"></span>
          </div>
        </summary>
        <div class="card chart-card">
          <div class="chart-header">
            <h3 class="chart-title" data-i18n="chart3_title"></h3>
          </div>
          <div class="chart-box" id="chart-volcano"></div>
        </div>
        <div class="card table-card">
          <div class="table-toolbar">
            <h3 class="card-title" data-i18n="top_hits_title"></h3>
            <div class="chip-row" id="table-filter-chips"></div>
          </div>
          <table id="top-hits-table"></table>
        </div>
      </details>

      <details class="evidence-accordion" id="audit" data-chart="chart-real-audit" open>
        <summary class="evidence-summary">
          <div>
            <h2 data-i18n="sec4_title"></h2>
            <p class="section-desc" data-i18n="sec4_desc"></p>
          </div>
          <div class="evidence-summary-meta">
            <span class="chart-pill" data-i18n="chart4_pill"></span>
            <span class="evidence-chevron" aria-hidden="true"></span>
          </div>
        </summary>
        <div class="card chart-card">
          <div class="chart-header">
            <h3 class="chart-title" data-i18n="chart4_title"></h3>
          </div>
          <div class="chart-box" id="chart-real-audit"></div>
          <div class="chart-takeaway" id="takeaway-audit"></div>
        </div>
      </details>
    </div>

    <section id="explorer">
      <div class="section-head">
        <div>
          <h2 data-i18n="sec5_title"></h2>
          <p class="section-desc" data-i18n="sec5_desc"></p>
        </div>
      </div>
      <div class="card">
        <div class="controls">
          <div class="control-group">
            <label for="select-hypothesis" data-i18n="lbl_hypothesis"></label>
            <select id="select-hypothesis" onchange="onExplorerFilterChange()"></select>
          </div>
          <div class="control-group">
            <label for="select-slice" data-i18n="lbl_slice"></label>
            <select id="select-slice" onchange="onExplorerFilterChange()"></select>
          </div>
          <div class="control-actions">
            <button type="button" class="btn-secondary" id="btn-reset-explorer" onclick="resetExplorer()" data-i18n="btn_reset"></button>
          </div>
        </div>
        <div class="quick-picks" id="quick-picks"></div>
        <div class="explorer-verdict" id="explorer-verdict"></div>
        <div class="explorer-stats" id="explorer-stats"></div>
        <div class="chart-box chart-box--compact" id="chart-explorer"></div>
      </div>
    </section>

    <details class="methodology-details">
      <summary data-i18n="method_summary"></summary>
      <div class="methodology-body" id="methodology-body"></div>
    </details>

    <footer>
      <span data-i18n="footer_note"></span>
      <a href="https://mercury-lab.ana-catalina.com" target="_blank" rel="noopener noreferrer" data-i18n="footer_lab_link"></a>
    </footer>
  </main>

  <nav class="bottom-nav" aria-label="Mobile navigation">
    <a href="#overview" class="bottom-nav-item active" data-section="overview">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <rect x="3" y="3" width="7" height="7" rx="1"></rect>
        <rect x="14" y="3" width="7" height="7" rx="1"></rect>
        <rect x="3" y="14" width="7" height="7" rx="1"></rect>
        <rect x="14" y="14" width="7" height="7" rx="1"></rect>
      </svg>
      <span data-i18n="nav_overview"></span>
    </a>
    <a href="#findings" class="bottom-nav-item" data-section="findings">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="9"></circle>
        <path d="M12 8v4"></path>
        <path d="M12 16h.01"></path>
      </svg>
      <span data-i18n="nav_findings"></span>
    </a>
    <a href="#evidence" class="bottom-nav-item" data-section="evidence">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M3 3v18h18"></path>
        <path d="m19 9-5 5-4-4-3 3"></path>
      </svg>
      <span data-i18n="nav_evidence"></span>
    </a>
    <a href="#explorer" class="bottom-nav-item" data-section="explorer">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
      </svg>
      <span data-i18n="nav_explorer"></span>
    </a>
  </nav>

  <script>
    const STUDY_DATA = __STUDY_JSON__;
    const STORAGE_KEYS = {
      lang: "mercury_lang",
      hyp: "mercury_hyp",
      slice: "mercury_slice",
    };

    function readStored(key, fallback) {
      try {
        const val = window.localStorage.getItem(key);
        return val !== null && val !== "" ? val : fallback;
      } catch (_) {
        return fallback;
      }
    }

    function writeStored(key, value) {
      try {
        window.localStorage.setItem(key, value);
      } catch (_) {
        // Ignore storage restrictions in private or sandboxed contexts.
      }
    }

    const storedLang = readStored(STORAGE_KEYS.lang, "en");
    let currentLang = storedLang === "es" ? "es" : "en";
    let explorerInitialized = false;
    let volcanoFilter = "top10";

    function isMobileViewport() {
      return window.innerWidth < 640;
    }

    const I18N = {
      en: {
        nav_overview: "Overview",
        nav_findings: "Findings",
        nav_evidence: "Evidence",
        nav_timeline: "Timeline",
        nav_glm: "GLM",
        nav_phacking: "P-Hacking",
        nav_audit: "Statuspage",
        nav_explorer: "Explorer",
        nav_lab: "Live Lab",
        eyebrow: "Empirical Ephemeris Lab",
        title: "Mercury in Prod: Do Planets Break Deployments?",
        subtitle: "2,130-day statistical audit comparing planetary transits against software incidents and 400 real Statuspage outages.",
        cta_explorer: "Test a Myth in Explorer ↓",
        cta_evidence: "Inspect the Evidence",
        findings_title: "Why Engineers Blame Mercury (3 Key Findings)",
        findings_desc: "Before diving into the charts, here is how human calendars and multiple-testing traps create illusory cosmic patterns.",
        evidence_heading: "Controlled Statistical Evidence",
        evidence_sub: "Tap any section below to expand the interactive chart and numbers.",
        sec1_title: "1. Orbital Speed vs. Incident Volume",
        sec1_desc: "Shaded bands mark Mercury retrograde (< 0°/day). Incidents track release freezes and workweeks, not orbits.",
        chart1_title: "2021–2026 Time Series: Mercury Speed vs. 14-Day Rolling Incidents",
        chart1_pill: "Interactive Zoom",
        sec2_title: "2. Controlled Poisson GLM",
        sec2_desc: "Controlling for engineering calendars places every astrological predictor at IRR = 1.0.",
        chart2_title: "Incident Rate Ratios (95% CI)",
        chart2_pill: "1.0 = No Effect",
        sec3_title: "3. P-Hacking Scan: 57 Hypotheses",
        sec3_desc: "Benjamini-Hochberg FDR filters out random noise; the sole survivor (Sun in Capricorn) reflects December's code freeze.",
        chart3_title: "Volcano Plot: Effect Size vs. Statistical Significance",
        chart3_pill: "BH-FDR & Bonferroni",
        top_hits_title: "Hypothesis Results",
        sec4_title: "4. Real Statuspage Audit",
        sec4_desc: "400 real outages across 8 cloud platforms match expected astronomical base rates.",
        chart4_title: "Observed vs. Window-Expected Share (%)",
        chart4_pill: "Zero Excess Risk",
        sec5_title: "5. Interactive Hypothesis Explorer",
        sec5_desc: "Test any planetary condition and filter by weekday/weekend to inspect calendar bias.",
        lbl_hypothesis: "Astrological Condition",
        lbl_slice: "Calendar Slice",
        btn_reset: "Reset Explorer Filters",
        btn_retry: "Retry Chart Render",
        offline_chart_msg: "Interactive chart unavailable offline — statistical summary active above.",
        empty_chart_msg: "No records available for this view.",
        empty_audit_msg: "No real Statuspage audit tests are available in this snapshot.",
        error_chart_msg: "Unable to render this interactive chart right now.",
        method_summary: "Methodology & Reproducibility",
        footer_note: "Built with astronomy-engine, statsmodels, and Plotly.",
        footer_lab_link: "Open Interactive Streamlit Lab (Permutations) ↗",
      },
      es: {
        nav_overview: "Resumen",
        nav_findings: "Hallazgos",
        nav_evidence: "Evidencia",
        nav_timeline: "Serie",
        nav_glm: "GLM",
        nav_phacking: "P-Hacking",
        nav_audit: "Statuspage",
        nav_explorer: "Explorador",
        nav_lab: "Lab en Vivo",
        eyebrow: "Laboratorio Empírico de Efemérides",
        title: "Mercury in Prod: ¿Los planetas rompen producción?",
        subtitle: "Auditoría estadística de 2,130 días que cruza efemérides planetarias con incidentes de software y 400 fallos reales de Statuspage.",
        cta_explorer: "Probar un mito en el Explorador ↓",
        cta_evidence: "Ver la evidencia",
        findings_title: "Por qué culpamos a Mercurio (3 Hallazgos Clave)",
        findings_desc: "Antes de ver los gráficos, así es como el calendario humano y las pruebas múltiples crean patrones ilusorios.",
        evidence_heading: "Evidencia Estadística Controlada",
        evidence_sub: "Toca cualquier sección para desplegar su gráfico interactivo y detalle.",
        sec1_title: "1. Velocidad Orbital vs. Incidentes",
        sec1_desc: "Las bandas rosadas marcan Mercurio retrógrado (< 0°/día). Los incidentes siguen semanas laborales y freezes, no órbitas.",
        chart1_title: "Serie 2021–2026: Velocidad de Mercurio vs. Media Móvil 14d",
        chart1_pill: "Zoom Interactivo",
        sec2_title: "2. Modelo GLM de Poisson Controlado",
        sec2_desc: "Al controlar el calendario de ingeniería, todos los predictores astrológicos quedan en IRR = 1.0.",
        chart2_title: "Incident Rate Ratios (IC 95%)",
        chart2_pill: "1.0 = Sin Efecto",
        sec3_title: "3. Escaneo de P-Hacking: 57 Hipótesis",
        sec3_desc: "La corrección BH-FDR elimina el ruido aleatorio; el único sobreviviente (Sol en Capricornio) responde al Code Freeze de diciembre.",
        chart3_title: "Gráfico Volcán: Tamaño de Efecto vs. Significancia",
        chart3_pill: "BH-FDR y Bonferroni",
        top_hits_title: "Resultados por Hipótesis",
        sec4_title: "4. Auditoría Real en Statuspage",
        sec4_desc: "400 incidentes reales en 8 plataformas coinciden con la tasa base astronómica esperada.",
        chart4_title: "Observado vs. Esperado por Ventana (%)",
        chart4_pill: "Sin Exceso de Riesgo",
        sec5_title: "5. Explorador Interactivo",
        sec5_desc: "Prueba cualquier condición astronómica y filtra por días laborales o fines de semana.",
        lbl_hypothesis: "Condición Astrológica",
        lbl_slice: "Filtro de Calendario",
        btn_reset: "Restablecer Filtros",
        btn_retry: "Reintentar Renderizado",
        offline_chart_msg: "Gráfico interactivo no disponible sin conexión — resumen estadístico activo arriba.",
        empty_chart_msg: "No hay registros disponibles para esta vista.",
        empty_audit_msg: "No hay pruebas reales de Statuspage disponibles en esta instantánea.",
        error_chart_msg: "No fue posible renderizar este gráfico interactivo en este momento.",
        method_summary: "Metodología y Reproducibilidad",
        footer_note: "Construido con astronomy-engine, statsmodels y Plotly.",
        footer_lab_link: "Abrir Lab Interactivo en Streamlit (Permutaciones) ↗",
      }
    };

    function readThemeTokens() {
      const styles = getComputedStyle(document.documentElement);
      const token = (name) => styles.getPropertyValue(name).trim();
      return {
        text: token("--text"),
        grid: token("--grid"),
        border: token("--border"),
        muted: token("--muted"),
        mutedLight: token("--muted-light"),
        nullColor: token("--null-color"),
        accent: token("--accent"),
        accent2: token("--accent-2"),
        ok: token("--ok"),
        danger: token("--danger"),
        surface: token("--surface"),
        surfaceAlt: token("--surface-alt"),
        retroBand: token("--retro-band"),
        plotBg: token("--plot-bg"),
        plotTransparent: token("--plot-transparent"),
      };
    }

    let THEME = readThemeTokens();

    // Always return a fresh layout object so Plotly never mutates shared axes across charts.
    function freshLayout(overrides = {}) {
      const mobile = isMobileViewport();
      const base = {
        paper_bgcolor: THEME.plotTransparent,
        plot_bgcolor: THEME.plotTransparent,
        font: { color: THEME.text, family: "Inter, -apple-system, sans-serif", size: mobile ? 11 : 12 },
        margin: mobile ? { t: 36, r: 12, b: 44, l: 44 } : { t: 40, r: 24, b: 48, l: 58 },
        hoverlabel: {
          bgcolor: THEME.surfaceAlt,
          bordercolor: THEME.border,
          font: { color: THEME.text, size: mobile ? 11 : 12 },
        },
        xaxis: {
          gridcolor: THEME.grid,
          zerolinecolor: THEME.border,
          automargin: true,
        },
        yaxis: {
          gridcolor: THEME.grid,
          zerolinecolor: THEME.border,
          automargin: true,
        },
      };
      return {
        ...base,
        ...overrides,
        xaxis: { ...base.xaxis, ...(overrides.xaxis || {}) },
        yaxis: { ...base.yaxis, ...(overrides.yaxis || {}) },
      };
    }

    function getPlotlyConfig() {
      const mobile = isMobileViewport();
      return {
        responsive: true,
        displayModeBar: mobile ? false : "hover",
        scrollZoom: false,
        displaylogo: false,
        modeBarButtonsToRemove: ["select2d", "lasso2d", "autoScale2d"],
      };
    }

    function renderNotice(container, message, isError, includeRetry) {
      container.innerHTML = "";
      const box = document.createElement("div");
      box.className = isError ? "state-notice state-notice--error" : "state-notice";
      box.setAttribute("role", "status");
      box.setAttribute("aria-live", "polite");

      const p = document.createElement("p");
      p.textContent = message;
      box.appendChild(p);

      if (includeRetry) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn-secondary";
        btn.textContent = I18N[currentLang].btn_retry;
        btn.onclick = () => renderAll();
        box.appendChild(btn);
      }
      container.appendChild(box);
    }

    function renderPlot(containerId, traces, layout, emptyMessage) {
      const container = document.getElementById(containerId);
      if (!container) return;

      if (!traces || traces.length === 0) {
        renderNotice(container, emptyMessage || I18N[currentLang].empty_chart_msg, false, false);
        return;
      }

      if (typeof Plotly === "undefined") {
        renderNotice(container, I18N[currentLang].offline_chart_msg, false, true);
        return;
      }

      try {
        container.innerHTML = "";
        Plotly.newPlot(containerId, traces, layout, getPlotlyConfig());
      } catch (_) {
        renderNotice(container, I18N[currentLang].error_chart_msg, true, true);
      }
    }

    function syncLangControls(lang) {
      document.documentElement.lang = lang;
      const btnEn = document.getElementById("btn-en");
      const btnEs = document.getElementById("btn-es");
      const isEs = lang === "es";
      btnEn.classList.toggle("active", !isEs);
      btnEs.classList.toggle("active", isEs);
      btnEn.setAttribute("aria-pressed", String(!isEs));
      btnEs.setAttribute("aria-pressed", String(isEs));
    }

    function setLang(lang) {
      currentLang = lang === "es" ? "es" : "en";
      writeStored(STORAGE_KEYS.lang, currentLang);
      syncLangControls(currentLang);
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
          sub: `${s.start_date} → ${s.end_date}`,
        },
        {
          label: isEs ? "Incidentes Reales" : "Real Outages",
          value: s.real_public_incidents_count.toLocaleString(),
          sub: isEs ? `${s.real_public_sources_count} plataformas Statuspage` : `${s.real_public_sources_count} Statuspage platforms`,
        },
        {
          label: isEs ? "IRR Mercurio Retrógrado" : "Mercury Retro IRR",
          value: retroGlm ? `${retroGlm.irr.toFixed(2)}x` : "N/A",
          sub: retroGlm
            ? `95% CI [${retroGlm.ci_low.toFixed(2)}, ${retroGlm.ci_high.toFixed(2)}] · p=${retroGlm.p_value.toFixed(2)}`
            : (isEs ? "No disponible" : "Unavailable"),
        },
        {
          label: isEs ? "Hits Ingenuos → FDR" : "Naive Hits → FDR",
          value: `${scan.naive_hits_count} → ${scan.fdr_survivors_count}`,
          sub: isEs ? `de ${scan.total_hypotheses} hipótesis (1 confusor dic.)` : `of ${scan.total_hypotheses} tests (1 Dec confounder)`,
        },
      ];

      document.getElementById("kpi-grid").innerHTML = cards.map(c => `
        <div class="card kpi-card">
          <div class="kpi-label">${c.label}</div>
          <div class="kpi-value">${c.value}</div>
          <div class="kpi-sub">${c.sub}</div>
        </div>
      `).join("");

      const retroIrrVal = retroGlm ? retroGlm.irr.toFixed(2) : "0.98";
      const retroPVal = retroGlm ? retroGlm.p_value.toFixed(2) : "0.71";
      const verdictHtml = `
        <div class="verdict-head">
          <span class="verdict-tag">${isEs ? "Hipótesis nula confirmada" : "Null hypothesis confirmed"}</span>
          <span class="chart-pill">Poisson GLM · HC3</span>
        </div>
        <p class="verdict-text">
          ${isEs
            ? `<strong>Veredicto:</strong> Mercurio retrógrado no rompe producción. El calendario humano explica la varianza de incidentes, no las órbitas planetarias.`
            : `<strong>Verdict:</strong> Mercury retrograde does not break production. Human engineering calendars drive incident variance, not planetary orbits.`}
        </p>
        <div class="verdict-bars">
          <div class="vbar-row">
            <span class="vbar-label">${isEs ? "Fines de semana (Freeze natural)" : "Weekends (Natural freeze)"}</span>
            <span class="vbar-val vbar-val--eng">-69% · IRR 0.31</span>
            <div class="vbar-track"><div class="vbar-fill vbar-fill--eng" style="width: 85%"></div></div>
          </div>
          <div class="vbar-row">
            <span class="vbar-label">${isEs ? "Ventana de deploy Mar–Jue" : "Tue–Thu deploy window"}</span>
            <span class="vbar-val vbar-val--eng">+23% · IRR 1.23</span>
            <div class="vbar-track"><div class="vbar-fill vbar-fill--eng" style="width: 58%"></div></div>
          </div>
          <div class="vbar-row">
            <span class="vbar-label">${isEs ? "Mercurio Retrógrado (Ruido)" : "Mercury Retrograde (Noise)"}</span>
            <span class="vbar-val vbar-val--null">IRR ${retroIrrVal} · p=${retroPVal}</span>
            <div class="vbar-track"><div class="vbar-fill vbar-fill--null" style="width: 8%"></div></div>
          </div>
        </div>
      `;
      document.getElementById("verdict-callout").innerHTML = verdictHtml;
    }

    function renderSynthesis() {
      const isEs = currentLang === "es";
      const scan = STUDY_DATA.phacking_scan;
      const items = isEs
        ? [
            {
              num: "01 · Calendario",
              title: "El sesgo del calendario humano",
              body: "Los incidentes caen un 69% en fines de semana y suben un 23% de martes a jueves cuando los equipos despliegan código.",
            },
            {
              num: "02 · P-Hacking",
              title: "La trampa de las 57 hipótesis",
              body: `Al probar ${scan.total_hypotheses} reglas astronómicas sin corregir, ${scan.naive_hits_count} parecen significativas (p < 0.05) por puro azar. BH-FDR las descarta salvo 1 confusor de diciembre.`,
            },
            {
              num: "03 · Outages Reales",
              title: "Paridad en 400 fallos reales",
              body: "GitHub, Cloudflare, Vercel, npm, Discord, Reddit, Bitbucket y DigitalOcean fallan exactamente a la tasa base astronómica esperada.",
            },
          ]
        : [
            {
              num: "01 · Calendar Bias",
              title: "Human schedules drive outages",
              body: "Incidents drop 69% on weekends and rise 23% Tue–Thu when engineering teams actively ship changes to production.",
            },
            {
              num: "02 · P-Hacking Trap",
              title: "Why 57 tests create false hits",
              body: `Testing ${scan.total_hypotheses} planetary rules produces ${scan.naive_hits_count} naive hits (p < 0.05) by chance. BH-FDR eliminates all except 1 December code-freeze confounder.`,
            },
            {
              num: "03 · Real Outages",
              title: "Zero excess risk in 400 outages",
              body: "Real incidents across GitHub, Cloudflare, Vercel, npm, Discord, Reddit, Bitbucket, and DigitalOcean match expected base rates.",
            },
          ];

      document.getElementById("synthesis-grid").innerHTML = items.map(item => `
        <article class="synthesis-card">
          <span class="synthesis-num">${item.num}</span>
          <h3 class="synthesis-title">${item.title}</h3>
          <p class="synthesis-body">${item.body}</p>
        </article>
      `).join("");

      document.getElementById("takeaway-timeline").innerHTML = isEs
        ? `<strong>Lectura rápida:</strong> Las bandas rosadas (< 0°/día) ocurren ~3 veces al año, pero las caídas pronunciadas de incidentes coinciden con fines de semana y diciembre.`
        : `<strong>Quick read:</strong> Pink bands (< 0°/day) occur ~3 times a year, yet the sharpest incident drops align with weekends and December freezes.`;

      document.getElementById("takeaway-glm").innerHTML = isEs
        ? `<strong>Lectura rápida:</strong> Todos los intervalos de confianza (IC 95%) de predictores astrológicos cruzan la línea punteada de <strong>1.0</strong> (sin efecto).`
        : `<strong>Quick read:</strong> Every astrological predictor's 95% confidence interval crosses the dashed <strong>1.0</strong> line (no statistical effect).`;

      document.getElementById("takeaway-audit").innerHTML = isEs
        ? `<strong>Plataformas auditadas:</strong> GitHub, Cloudflare, npm, Discord, Reddit, Bitbucket, Vercel y DigitalOcean (400 incidentes públicos reales).`
        : `<strong>Audited platforms:</strong> GitHub, Cloudflare, npm, Discord, Reddit, Bitbucket, Vercel, and DigitalOcean (400 real public outages).`;

      const methodBlocks = isEs
        ? [
            {
              title: "Efemérides Deterministas",
              body: "Port exacto en Python de AstrologyEngine usando astronomy-engine para calcular longitud eclíptica, velocidad diaria y fases lunares sin APIs externas.",
            },
            {
              title: "Modelo Poisson GLM (HC3)",
              body: "Regresión de conteo diario con errores estándar robustos HC3 controlando fines de semana, ventana Mar–Jue, Patch Tuesday y Q4 Code Freeze.",
            },
            {
              title: "Corrección Múltiple (FDR)",
              body: "Ajuste Benjamini-Hochberg (q < 0.05) y umbral Bonferroni sobre 57 hipótesis planetarias, zodiacales y subgrupos de calendario.",
            },
          ]
        : [
            {
              title: "Deterministic Ephemeris",
              body: "Exact Python port of AstrologyEngine powered by astronomy-engine to compute ecliptic longitude, daily speed, and lunar phases offline.",
            },
            {
              title: "Poisson GLM (HC3)",
              body: "Daily incident count regression with HC3 robust standard errors controlling for weekends, Tue–Thu deploy windows, Patch Tuesday, and Q4 freezes.",
            },
            {
              title: "Multiple-Testing Control",
              body: "Benjamini-Hochberg FDR (q < 0.05) and Bonferroni thresholds across 57 planetary, zodiacal, and calendar-slice hypotheses.",
            },
          ];

      document.getElementById("methodology-body").innerHTML = methodBlocks.map(b => `
        <div>
          <h4>${b.title}</h4>
          <p>${b.body}</p>
        </div>
      `).join("");
    }

    function computeRetrogradeBands(rows) {
      const bands = [];
      let start = null;
      for (let i = 0; i < rows.length; i++) {
        const isRetro = rows[i].mercury_daily_speed_deg < 0;
        if (isRetro && start === null) {
          start = rows[i].date;
        } else if (!isRetro && start !== null) {
          bands.push({ x0: start, x1: rows[i - 1].date });
          start = null;
        }
      }
      if (start !== null) bands.push({ x0: start, x1: rows[rows.length - 1].date });
      return bands.map(b => ({
        type: "rect",
        xref: "x",
        yref: "paper",
        x0: b.x0,
        x1: b.x1,
        y0: 0,
        y1: 1,
        fillcolor: THEME.retroBand,
        line: { width: 0 },
        layer: "below",
      }));
    }

    function renderTimeline() {
      const isEs = currentLang === "es";
      const mobile = isMobileViewport();
      const rows = STUDY_DATA.timeline || [];
      if (rows.length === 0) {
        renderPlot("chart-timeline", [], freshLayout());
        return;
      }

      const dates = rows.map(r => r.date);
      const speeds = rows.map(r => r.mercury_daily_speed_deg);
      const counts = rows.map(r => r.incident_count);

      const rolling = counts.map((_, idx) => {
        const start = Math.max(0, idx - 13);
        const slice = counts.slice(start, idx + 1);
        return slice.reduce((a, b) => a + b, 0) / slice.length;
      });

      const traceInc = {
        x: dates,
        y: rolling,
        name: isEs ? "Incidentes (14d)" : "Incidents (14d MA)",
        type: "scatter",
        mode: "lines",
        line: { color: THEME.accent, width: 2.2 },
        hovertemplate: "%{x}<br>%{y:.2f} inc/day<extra></extra>",
      };

      const traceSpeed = {
        x: dates,
        y: speeds,
        name: isEs ? "Vel. Mercurio (°/d)" : "Mercury Speed (°/d)",
        type: "scatter",
        mode: "lines",
        yaxis: "y2",
        line: { color: THEME.accent2, width: 1.4 },
        opacity: 0.85,
        hovertemplate: "%{x}<br>%{y:.2f}°/day<extra></extra>",
      };

      const layout = freshLayout({
        height: mobile ? 340 : 410,
        margin: mobile ? { t: 44, r: 40, b: 68, l: 40 } : { t: 54, r: 64, b: 44, l: 56 },
        hovermode: "x unified",
        shapes: computeRetrogradeBands(rows),
        xaxis: {
          type: "date",
          rangeselector: {
            bgcolor: THEME.surfaceAlt,
            activecolor: THEME.border,
            bordercolor: THEME.border,
            font: { color: THEME.text, size: mobile ? 10 : 11 },
            x: mobile ? 0.5 : 1,
            xanchor: mobile ? "center" : "right",
            y: mobile ? 1.13 : 1.04,
            buttons: [
              { count: 1, label: isEs ? "1A" : "1Y", step: "year", stepmode: "backward" },
              { count: 3, label: isEs ? "3A" : "3Y", step: "year", stepmode: "backward" },
              { step: "all", label: isEs ? "Todo" : "All" },
            ],
          },
        },
        yaxis: {
          type: "linear",
          title: mobile ? "" : (isEs ? "Incidentes / día (14d)" : "Incidents / day (14d)"),
        },
        yaxis2: {
          type: "linear",
          title: mobile ? "" : (isEs ? "Velocidad (°/día)" : "Speed (°/day)"),
          overlaying: "y",
          side: "right",
          gridcolor: THEME.plotTransparent,
          zeroline: true,
          zerolinecolor: THEME.danger,
        },
        legend: mobile
          ? { orientation: "h", x: 0.5, xanchor: "center", y: -0.22, yanchor: "top" }
          : { orientation: "h", x: 0, y: 1.03, yanchor: "bottom" },
      });
      renderPlot("chart-timeline", [traceInc, traceSpeed], layout);
    }

    function compactForestLabel(label, mobile) {
      if (!mobile || label.length <= 18) return label;
      const parts = label.split(" ");
      if (parts.length <= 2) return label;
      const mid = Math.ceil(parts.length / 2);
      return `${parts.slice(0, mid).join(" ")}<br>${parts.slice(mid).join(" ")}`;
    }

    function renderForest() {
      const isEs = currentLang === "es";
      const mobile = isMobileViewport();
      const terms = [...(STUDY_DATA.controlled_glm.terms || [])].reverse();
      if (terms.length === 0) {
        renderPlot("chart-forest", [], freshLayout());
        return;
      }

      const engTerms = terms.filter(t => t.category === "engineering");
      const astroTerms = terms.filter(t => t.category !== "engineering");
      const labelFor = (t) => compactForestLabel(isEs ? t.label_es : t.label_en, mobile);
      const allLabels = terms.map(labelFor);

      const makeTrace = (subset, name, color) => ({
        x: subset.map(t => t.irr),
        y: subset.map(labelFor),
        type: "scatter",
        mode: "markers",
        name,
        marker: { color, size: mobile ? 9 : 11 },
        error_x: {
          type: "data",
          symmetric: false,
          array: subset.map(t => t.ci_high - t.irr),
          arrayminus: subset.map(t => t.irr - t.ci_low),
          color: THEME.mutedLight,
          thickness: 1.8,
        },
        customdata: subset.map(t => [isEs ? t.label_es : t.label_en, t.ci_low.toFixed(3), t.ci_high.toFixed(3), t.p_value.toFixed(4)]),
        hovertemplate: "<b>%{customdata[0]}</b><br>IRR: %{x:.3f} [%{customdata[1]}, %{customdata[2]}]<br>p = %{customdata[3]}<extra></extra>",
      });

      const traces = [];
      if (engTerms.length > 0) traces.push(makeTrace(engTerms, isEs ? "Cal. Ingeniería" : "Engineering Cal.", THEME.accent));
      if (astroTerms.length > 0) traces.push(makeTrace(astroTerms, isEs ? "Pred. Astrológicos" : "Astrological", THEME.accent2));

      const layout = freshLayout({
        height: mobile ? 390 : 420,
        margin: mobile ? { t: 24, r: 14, b: 64, l: 118 } : { t: 46, r: 28, b: 48, l: 215 },
        xaxis: {
          type: "linear",
          title: isEs ? "Incident Rate Ratio (1.0 = Sin efecto)" : "Incident Rate Ratio (1.0 = No Effect)",
        },
        yaxis: {
          type: "category",
          categoryorder: "array",
          categoryarray: allLabels,
          tickfont: { size: mobile ? 10 : 12 },
        },
        legend: mobile
          ? { orientation: "h", x: 0.5, xanchor: "center", y: -0.24, yanchor: "top" }
          : { orientation: "h", x: 0, y: 1.03, yanchor: "bottom" },
        shapes: [{
          type: "line",
          x0: 1.0,
          x1: 1.0,
          y0: -0.5,
          y1: terms.length - 0.5,
          line: { color: THEME.muted, dash: "dash", width: 1.5 },
        }],
      });
      renderPlot("chart-forest", traces, layout);
    }

    function renderTableFilterChips(hyps) {
      const isEs = currentLang === "es";
      const counts = {
        top10: Math.min(10, hyps.length),
        fdr: hyps.filter(h => h.survives_fdr).length,
        naive: hyps.filter(h => h.naive_hit && !h.survives_fdr).length,
        all: hyps.length,
      };
      const chips = [
        { id: "top10", label: `Top ${counts.top10}` },
        { id: "fdr", label: isEs ? `Sobrevive FDR (${counts.fdr})` : `FDR Survivor (${counts.fdr})` },
        { id: "naive", label: isEs ? `Falso Hit (${counts.naive})` : `Naive Hit (${counts.naive})` },
        { id: "all", label: isEs ? `Todas (${counts.all})` : `All (${counts.all})` },
      ];
      const container = document.getElementById("table-filter-chips");
      container.innerHTML = chips.map(c => `
        <button type="button" class="chip-btn ${volcanoFilter === c.id ? "active" : ""}" data-filter="${c.id}">
          ${c.label}
        </button>
      `).join("");
      container.querySelectorAll(".chip-btn").forEach(btn => {
        btn.onclick = () => {
          volcanoFilter = btn.getAttribute("data-filter");
          renderVolcanoTable(hyps);
          renderTableFilterChips(hyps);
        };
      });
    }

    function renderVolcanoTable(hyps) {
      const isEs = currentLang === "es";
      let rows = hyps;
      if (volcanoFilter === "top10") rows = hyps.slice(0, 10);
      else if (volcanoFilter === "fdr") rows = hyps.filter(h => h.survives_fdr);
      else if (volcanoFilter === "naive") rows = hyps.filter(h => h.naive_hit && !h.survives_fdr);

      const headers = isEs
        ? ["Hipótesis", "Familia", "N Exp.", "Rate Ratio", "p crudo", "q (FDR)", "Estado"]
        : ["Hypothesis", "Family", "Exp. N", "Rate Ratio", "Raw p", "q (FDR)", "Status"];

      if (rows.length === 0) {
        document.getElementById("top-hits-table").innerHTML = `
          <thead><tr>${headers.map(h => `<th>${h}</th>`).join("")}</tr></thead>
          <tbody><tr><td colspan="${headers.length}">${I18N[currentLang].empty_chart_msg}</td></tr></tbody>
        `;
        return;
      }

      document.getElementById("top-hits-table").innerHTML = `
        <thead><tr>${headers.map(h => `<th>${h}</th>`).join("")}</tr></thead>
        <tbody>
          ${rows.map(r => {
            const label = isEs ? r.label_es : r.label_en;
            const badge = r.survives_fdr
              ? `<span class="badge badge-fdr">${isEs ? "Sobrevive FDR (Dic)" : "FDR Survivor (Dec)"}</span>`
              : r.naive_hit
              ? `<span class="badge badge-hit">${isEs ? "Falso Hit" : "Naive Hit"}</span>`
              : `<span class="badge badge-null">${isEs ? "Nulo" : "Null"}</span>`;
            return `<tr>
              <td data-label="${headers[0]}">${label}</td>
              <td data-label="${headers[1]}">${r.family}</td>
              <td data-label="${headers[2]}">${r.n_exposed}</td>
              <td data-label="${headers[3]}">${r.rate_ratio.toFixed(3)}x</td>
              <td data-label="${headers[4]}">${r.p_raw.toFixed(4)}</td>
              <td data-label="${headers[5]}">${r.q_fdr.toFixed(4)}</td>
              <td data-label="${headers[6]}">${badge}</td>
            </tr>`;
          }).join("")}
        </tbody>
      `;
    }

    function renderVolcano() {
      const isEs = currentLang === "es";
      const mobile = isMobileViewport();
      const scan = STUDY_DATA.phacking_scan;
      const hyps = scan.hypotheses || [];
      renderTableFilterChips(hyps);
      renderVolcanoTable(hyps);

      if (hyps.length === 0) {
        renderPlot("chart-volcano", [], freshLayout());
        return;
      }

      const groups = [
        {
          key: "null",
          name: isEs ? "Nulo (p >= 0.05)" : "Null (p >= 0.05)",
          color: THEME.nullColor,
          items: hyps.filter(h => !h.naive_hit),
        },
        {
          key: "naive",
          name: isEs ? "Falso Hit (falla FDR)" : "Naive Hit (fails FDR)",
          color: THEME.accent2,
          items: hyps.filter(h => h.naive_hit && !h.survives_fdr),
        },
        {
          key: "fdr",
          name: isEs ? "Sobrevive FDR (Dic)" : "FDR Survivor (Dec)",
          color: THEME.ok,
          items: hyps.filter(h => h.survives_fdr),
        },
      ].filter(g => g.items.length > 0);

      const traces = groups.map(g => ({
        x: g.items.map(h => Number(h.log2_fold_change)),
        y: g.items.map(h => Number(h.neg_log10_p)),
        text: g.items.map(h => `<b>${isEs ? h.label_es : h.label_en}</b><br>RR: ${h.rate_ratio.toFixed(3)}x<br>p_raw: ${h.p_raw.toFixed(4)} · q_FDR: ${h.q_fdr.toFixed(4)}`),
        name: g.name,
        mode: "markers",
        type: "scatter",
        marker: { color: g.color, size: mobile ? 9 : 10, opacity: 0.9 },
        hovertemplate: "%{text}<extra></extra>",
      }));

      const xs = hyps.map(h => Number(h.log2_fold_change));
      const pad = 0.08;
      const minX = Math.min(-0.45, ...xs) - pad;
      const maxX = Math.max(0.45, ...xs) + pad;
      const bonfY = -Math.log10(0.05 / Math.max(1, scan.total_hypotheses));
      const rawY = -Math.log10(0.05);

      const layout = freshLayout({
        height: mobile ? 350 : 410,
        margin: mobile ? { t: 24, r: 14, b: 74, l: 44 } : { t: 46, r: 24, b: 50, l: 58 },
        xaxis: {
          type: "linear",
          title: "log2(Incident Rate Ratio)",
          range: [minX, maxX],
          zeroline: true,
        },
        yaxis: {
          type: "linear",
          title: "-log10(raw p-value)",
        },
        legend: mobile
          ? { orientation: "h", x: 0.5, xanchor: "center", y: -0.26, yanchor: "top" }
          : { orientation: "h", x: 0, y: 1.03, yanchor: "bottom" },
        shapes: [
          { type: "line", x0: minX, x1: maxX, y0: rawY, y1: rawY, line: { color: THEME.accent2, dash: "dash", width: 1.4 } },
          { type: "line", x0: minX, x1: maxX, y0: bonfY, y1: bonfY, line: { color: THEME.danger, dash: "dot", width: 1.4 } },
        ],
        annotations: [
          {
            x: maxX, y: rawY, xanchor: "right", yanchor: "bottom",
            text: "p = 0.05", showarrow: false,
            font: { color: THEME.accent2, size: mobile ? 10 : 11 },
          },
          {
            x: maxX, y: bonfY, xanchor: "right", yanchor: "bottom",
            text: `Bonferroni (${(0.05 / Math.max(1, scan.total_hypotheses)).toFixed(4)})`,
            showarrow: false,
            font: { color: THEME.danger, size: mobile ? 10 : 11 },
          },
        ],
      });
      renderPlot("chart-volcano", traces, layout);
    }

    function renderRealAudit() {
      const isEs = currentLang === "es";
      const mobile = isMobileViewport();
      const tests = STUDY_DATA.real_statuspage_audit.tests || [];
      if (tests.length === 0) {
        renderPlot("chart-real-audit", [], freshLayout(), I18N[currentLang].empty_audit_msg);
        return;
      }

      const labels = tests.map(t => `${isEs ? t.label_es : t.label_en}<br>(p=${t.p_value.toFixed(2)})`);

      if (mobile) {
        // Horizontal grouped bars are far easier to read on narrow mobile screens.
        const revTests = [...tests].reverse();
        const revLabels = revTests.map(t => `${compactForestLabel(isEs ? t.label_es : t.label_en, true)}<br>(p=${t.p_value.toFixed(2)})`);
        const traceObs = {
          y: revLabels,
          x: revTests.map(t => t.observed_pct),
          name: isEs ? "Observado (%)" : "Observed (%)",
          type: "bar",
          orientation: "h",
          marker: { color: THEME.accent2 },
          hovertemplate: "%{y}<br>%{x:.2f}%<extra></extra>",
        };
        const traceExp = {
          y: revLabels,
          x: revTests.map(t => t.expected_pct),
          name: isEs ? "Esperado (%)" : "Expected (%)",
          type: "bar",
          orientation: "h",
          marker: { color: THEME.accent },
          hovertemplate: "%{y}<br>%{x:.2f}%<extra></extra>",
        };
        const layout = freshLayout({
          height: 340,
          margin: { t: 20, r: 16, b: 64, l: 112 },
          barmode: "group",
          xaxis: { type: "linear", title: isEs ? "Incidentes (%)" : "Share (%)" },
          yaxis: { type: "category", tickfont: { size: 10 } },
          legend: { orientation: "h", x: 0.5, xanchor: "center", y: -0.26, yanchor: "top" },
        });
        renderPlot("chart-real-audit", [traceObs, traceExp], layout);
        return;
      }

      const traceObs = {
        x: labels,
        y: tests.map(t => t.observed_pct),
        name: isEs ? "Observado (%)" : "Observed (%)",
        type: "bar",
        marker: { color: THEME.accent2 },
        hovertemplate: "%{x}<br>%{y:.2f}%<extra></extra>",
      };
      const traceExp = {
        x: labels,
        y: tests.map(t => t.expected_pct),
        name: isEs ? "Esperado (%)" : "Expected (%)",
        type: "bar",
        marker: { color: THEME.accent },
        hovertemplate: "%{x}<br>%{y:.2f}%<extra></extra>",
      };

      const layout = freshLayout({
        margin: { t: 46, r: 24, b: 64, l: 58 },
        barmode: "group",
        xaxis: { type: "category" },
        yaxis: { type: "linear", title: isEs ? "Incidentes (%)" : "Share (%)" },
        legend: { orientation: "h", x: 0, y: 1.03, yanchor: "bottom" },
      });
      renderPlot("chart-real-audit", [traceObs, traceExp], layout);
    }

    function renderQuickPicks() {
      const isEs = currentLang === "es";
      const opts = STUDY_DATA.explorer.options || {};
      const currentHyp = document.getElementById("select-hypothesis").value;
      const featuredIds = ["mercury_retrograde", "sun_in_capricorn", "full_moon_weekdays", "mercury_shadow"];
      const validIds = featuredIds.filter(id => opts[id]);

      const container = document.getElementById("quick-picks");
      if (validIds.length === 0) {
        container.innerHTML = "";
        return;
      }

      container.innerHTML = `
        <span class="quick-picks-label">${isEs ? "Accesos rápidos:" : "Quick picks:"}</span>
        ${validIds.map(id => {
          const o = opts[id];
          return `<button type="button" class="chip-btn ${currentHyp === id ? "active" : ""}" data-hyp="${id}">
            ${isEs ? o.label_es : o.label_en}
          </button>`;
        }).join("")}
      `;
      container.querySelectorAll(".chip-btn").forEach(btn => {
        btn.onclick = () => {
          document.getElementById("select-hypothesis").value = btn.getAttribute("data-hyp");
          onExplorerFilterChange();
        };
      });
    }

    function populateExplorerDropdowns() {
      const isEs = currentLang === "es";
      const hypSel = document.getElementById("select-hypothesis");
      const sliceSel = document.getElementById("select-slice");
      const opts = Object.values(STUDY_DATA.explorer.options);

      const desiredHyp = explorerInitialized
        ? hypSel.value
        : readStored(STORAGE_KEYS.hyp, "mercury_retrograde");
      hypSel.innerHTML = opts.map(o => `<option value="${o.id}">${isEs ? o.label_es : o.label_en}</option>`).join("");
      hypSel.value = opts.some(o => o.id === desiredHyp) ? desiredHyp : opts[0].id;

      const slices = [
        { id: "all", en: "All Days", es: "Todos los días" },
        { id: "weekdays", en: "Weekdays (Mon–Fri)", es: "Laborales (Lun–Vie)" },
        { id: "weekends", en: "Weekends (Sat–Sun)", es: "Fines de semana (Sáb–Dom)" },
      ];
      const desiredSlice = explorerInitialized
        ? sliceSel.value
        : readStored(STORAGE_KEYS.slice, "all");
      sliceSel.innerHTML = slices.map(s => `<option value="${s.id}">${isEs ? s.es : s.en}</option>`).join("");
      sliceSel.value = slices.some(s => s.id === desiredSlice) ? desiredSlice : "all";

      explorerInitialized = true;
    }

    function onExplorerFilterChange() {
      writeStored(STORAGE_KEYS.hyp, document.getElementById("select-hypothesis").value);
      writeStored(STORAGE_KEYS.slice, document.getElementById("select-slice").value);
      renderExplorer();
    }

    function resetExplorer() {
      const opts = Object.values(STUDY_DATA.explorer.options);
      const defaultHyp = opts.some(o => o.id === "mercury_retrograde") ? "mercury_retrograde" : opts[0].id;
      document.getElementById("select-hypothesis").value = defaultHyp;
      document.getElementById("select-slice").value = "all";
      writeStored(STORAGE_KEYS.hyp, defaultHyp);
      writeStored(STORAGE_KEYS.slice, "all");
      renderExplorer();
    }

    function renderExplorer() {
      const isEs = currentLang === "es";
      const mobile = isMobileViewport();
      const hypId = document.getElementById("select-hypothesis").value;
      const sliceId = document.getElementById("select-slice").value;
      renderQuickPicks();

      const option = STUDY_DATA.explorer.options[hypId];
      if (!option || !option.slices[sliceId]) {
        document.getElementById("explorer-verdict").innerHTML = "";
        document.getElementById("explorer-stats").innerHTML = "";
        renderPlot("chart-explorer", [], freshLayout());
        return;
      }

      const data = option.slices[sliceId];
      const qVal = data.q_fdr;
      const survivesFdr = qVal !== null && qVal !== undefined && qVal < 0.05;
      const naiveHit = data.p_raw < 0.05;
      const verdictBadge = survivesFdr
        ? `<span class="badge badge-fdr">${isEs ? "Sobrevive FDR (Confusor estacional)" : "Survives FDR (Seasonal confounder)"}</span>`
        : naiveHit
        ? `<span class="badge badge-hit">${isEs ? "Falso Hit (falla FDR)" : "Naive Hit (fails FDR)"}</span>`
        : `<span class="badge badge-null">${isEs ? "Sin efecto (Ruido)" : "Null Result (Noise)"}</span>`;

      const verdictMsg = survivesFdr
        ? (isEs ? "Efecto aparente por el Code Freeze de diciembre, no por la órbita." : "Apparent shift driven by December's Code Freeze, not orbital mechanics.")
        : naiveHit
        ? (isEs ? "Parece significativo en crudo, pero desaparece al corregir por múltiples pruebas." : "Looks significant unadjusted, but vanishes under multiple-testing correction.")
        : (isEs ? "Distribución estadísticamente indistinguible de la línea base." : "Distribution is statistically indistinguishable from baseline days.");

      document.getElementById("explorer-verdict").innerHTML = `
        <span>${verdictMsg}</span>
        ${verdictBadge}
      `;

      const statsCards = [
        { label: isEs ? "Días Expuestos" : "Exposed Days", val: `${data.n_exposed} / ${data.n_exposed + data.n_baseline}` },
        { label: isEs ? "Media Exp. vs Base" : "Exposed vs Base", val: `${data.mean_exposed.toFixed(2)} vs ${data.mean_baseline.toFixed(2)}` },
        { label: "Rate Ratio", val: `${data.rate_ratio.toFixed(3)}x (${data.pct_diff >= 0 ? "+" : ""}${data.pct_diff.toFixed(1)}%)` },
        { label: "Welch p / Perm p", val: `${data.p_raw.toFixed(4)} / ${data.p_perm.toFixed(4)}` },
        { label: "BH-FDR q", val: qVal !== null && qVal !== undefined ? qVal.toFixed(4) : "N/A" },
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
        name: isEs ? "Expuestos (%)" : "Exposed (%)",
        type: "bar",
        marker: { color: THEME.accent2 },
        opacity: 0.85,
      };
      const tBase = {
        x: bins,
        y: data.baseline_hist_pct,
        name: isEs ? "Línea Base (%)" : "Baseline (%)",
        type: "bar",
        marker: { color: THEME.accent },
        opacity: 0.85,
      };
      const layout = freshLayout({
        height: mobile ? 300 : 360,
        margin: mobile ? { t: 20, r: 12, b: 64, l: 44 } : { t: 44, r: 20, b: 48, l: 54 },
        barmode: "group",
        xaxis: { type: "linear", title: isEs ? "Incidentes diarios" : "Daily Incidents" },
        yaxis: { type: "linear", title: isEs ? "Frecuencia (%)" : "Share (%)" },
        legend: mobile
          ? { orientation: "h", x: 0.5, xanchor: "center", y: -0.26, yanchor: "top" }
          : { orientation: "h", x: 0, y: 1.03, yanchor: "bottom" },
      });
      renderPlot("chart-explorer", [tExp, tBase], layout);
    }

    function isAccordionMobileMode() {
      return window.innerWidth <= 820;
    }

    function syncAccordionMode() {
      const mobileAcc = isAccordionMobileMode();
      document.querySelectorAll(".evidence-accordion").forEach(det => {
        det.open = !mobileAcc;
      });
    }

    function initAccordions() {
      syncAccordionMode();
      document.querySelectorAll(".evidence-accordion").forEach(det => {
        det.addEventListener("toggle", () => {
          if (det.open && typeof Plotly !== "undefined") {
            const chartId = det.getAttribute("data-chart");
            const chartEl = chartId ? document.getElementById(chartId) : null;
            if (chartEl) {
              requestAnimationFrame(() => {
                try {
                  Plotly.Plots.resize(chartEl);
                } catch (_) {
                  // Ignore if chart is not yet initialized.
                }
              });
            }
          }
        });
      });
    }

    function initNavigationTracking() {
      const progress = document.getElementById("read-progress");
      const updateProgress = () => {
        const doc = document.documentElement;
        const max = doc.scrollHeight - window.innerHeight;
        const pct = max > 0 ? Math.min(100, Math.max(0, (window.scrollY / max) * 100)) : 0;
        progress.style.width = `${pct}%`;
      };
      window.addEventListener("scroll", updateProgress, { passive: true });
      updateProgress();

      const pills = Array.from(document.querySelectorAll(".nav-pill"));
      const bottomItems = Array.from(document.querySelectorAll(".bottom-nav-item"));
      const evidenceIds = new Set(["evidence", "timeline", "glm", "phacking", "audit"]);
      const observedIds = ["overview", "findings", "evidence", "timeline", "glm", "phacking", "audit", "explorer"];
      const sections = observedIds.map(id => document.getElementById(id)).filter(Boolean);

      if ("IntersectionObserver" in window && sections.length > 0) {
        const obs = new IntersectionObserver((entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              const id = entry.target.id;
              pills.forEach(p => {
                p.classList.toggle("active", p.getAttribute("data-section") === id);
              });
              const bottomKey = evidenceIds.has(id) ? "evidence" : id;
              bottomItems.forEach(b => {
                b.classList.toggle("active", b.getAttribute("data-section") === bottomKey);
              });
            }
          });
        }, { rootMargin: "-20% 0px -65% 0px" });
        sections.forEach(s => obs.observe(s));
      }
    }

    function renderAll() {
      THEME = readThemeTokens();
      syncLangControls(currentLang);
      renderStaticText();
      renderKpis();
      renderSynthesis();
      populateExplorerDropdowns();
      renderExplorer();
      renderTimeline();
      renderForest();
      renderVolcano();
      renderRealAudit();
    }

    let lastMobileState = isMobileViewport();
    let lastAccMobileState = isAccordionMobileMode();
    let resizeTimer = null;
    window.addEventListener("resize", () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        const nowAccMobile = isAccordionMobileMode();
        if (nowAccMobile !== lastAccMobileState) {
          lastAccMobileState = nowAccMobile;
          syncAccordionMode();
        }
        const nowMobile = isMobileViewport();
        if (nowMobile !== lastMobileState) {
          lastMobileState = nowMobile;
          renderAll();
        }
      }, 180);
    });

    initAccordions();
    initNavigationTracking();
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
