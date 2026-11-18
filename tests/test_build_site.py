"""Unit tests for the static Data Story HTML generator."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from src.build_site import build_static_site
from src.ephemeris import generate_ephemeris_df
from src.incidents import aggregate_real_incidents_by_day, build_operational_panel


def test_build_static_site_embeds_study_json_and_accessibility_styles(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    site_dir = tmp_path / "site"
    data_dir.mkdir(parents=True)

    raw_df = pd.DataFrame(
        [
            {
                "incident_id": "inc-1",
                "source": "github",
                "name": "Sample outage",
                "impact": "major",
                "is_critical_major": True,
                "status": "resolved",
                "created_at_utc": "2024-04-10T10:00:00+00:00",
                "date": "2024-04-10",
                "duration_minutes": 40.0,
            },
            {
                "incident_id": "inc-2",
                "source": "vercel",
                "name": "Sample edge blip",
                "impact": "minor",
                "is_critical_major": False,
                "status": "resolved",
                "created_at_utc": "2024-06-15T14:00:00+00:00",
                "date": "2024-06-15",
                "duration_minutes": 15.0,
            },
        ]
    )
    raw_df.to_csv(data_dir / "raw_public_incidents.csv", index=False)

    real_daily = aggregate_real_incidents_by_day(raw_df)
    panel = build_operational_panel("2024-01-01", "2024-12-31", real_daily_df=real_daily, seed=42)
    eph = generate_ephemeris_df("2024-01-01", "2024-12-31")
    panel.merge(eph, on="date", how="inner").to_csv(data_dir / "daily_incidents_ephemeris.csv", index=False)

    output_path = build_static_site(data_dir=data_dir, site_dir=site_dir, refresh_data=False)
    assert output_path == site_dir / "index.html"
    assert output_path.exists()

    html = output_path.read_text(encoding="utf-8")
    assert "__STUDY_JSON__" not in html
    assert ":focus-visible" in html
    assert "color-scheme: dark" in html
    assert "aria-pressed" in html
    assert "getComputedStyle" in html

    template_without_root = re.sub(r":root\s*\{.*?\}", "", html, count=1, flags=re.DOTALL)
    template_without_data = re.sub(r"const STUDY_DATA = \{.*?\};", "", template_without_root, count=1, flags=re.DOTALL)
    assert re.findall(r"#[0-9a-fA-F]{3,8}\b", template_without_data) == []

    match = re.search(r"const STUDY_DATA = (\{.*?\});", html, flags=re.DOTALL)
    assert match is not None
    embedded = json.loads(match.group(1))
    assert embedded["phacking_scan"]["total_hypotheses"] == 57
    personal_retro = embedded["explorer"]["options"]["any_personal_retrograde"]["slices"]["all"]
    assert personal_retro["q_fdr"] is not None
    assert personal_retro["p_bonferroni"] is not None
