"""Unit tests for Statuspage ingestion, panel generation, and caching fallback."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest
import requests

from src.incidents import (
    _parse_iso_utc,
    aggregate_real_incidents_by_day,
    build_and_save_dataset,
    fetch_public_statuspage_incidents,
)


class _DummyResponse:
    def __init__(self, payload: dict, status_error: Exception | None = None) -> None:
        self._payload = payload
        self._status_error = status_error

    def raise_for_status(self) -> None:
        if self._status_error is not None:
            raise self._status_error

    def json(self) -> dict:
        return self._payload


def test_parse_iso_utc_handles_valid_and_invalid_values() -> None:
    assert _parse_iso_utc("2024-04-10T12:30:00Z") == datetime(2024, 4, 10, 12, 30, 0, tzinfo=UTC)
    assert _parse_iso_utc("2024-04-10T10:30:00-02:00") == datetime(2024, 4, 10, 12, 30, 0, tzinfo=UTC)
    assert _parse_iso_utc("2024-04-10T12:30:00") == datetime(2024, 4, 10, 12, 30, 0, tzinfo=UTC)
    assert _parse_iso_utc(None) is None
    assert _parse_iso_utc("") is None
    assert _parse_iso_utc("not-a-timestamp") is None


def test_fetch_public_statuspage_incidents_dedups_and_tracks_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    sample_payload = {
        "incidents": [
            {
                "id": "inc-1",
                "name": "API Degradation",
                "impact": "major",
                "status": "resolved",
                "created_at": "2024-04-10T10:00:00Z",
                "resolved_at": "2024-04-10T11:30:00Z",
            },
            {
                "id": "inc-1",
                "name": "API Degradation",
                "impact": "major",
                "status": "resolved",
                "created_at": "2024-04-10T10:00:00Z",
                "resolved_at": "2024-04-10T11:30:00Z",
            },
            {
                "id": "inc-2",
                "name": "Bad Timestamp Ignored",
                "impact": "minor",
                "status": "resolved",
                "created_at": "invalid-date",
                "resolved_at": None,
            },
        ]
    }

    def fake_get(self, url: str, timeout: float = 8.0) -> _DummyResponse:
        if "failing" in url:
            raise requests.ConnectionError("Network unreachable")
        return _DummyResponse(sample_payload)

    monkeypatch.setattr(requests.Session, "get", fake_get)

    df, succeeded, failed = fetch_public_statuspage_incidents(
        sources={
            "github": "https://ok.example.com/incidents.json",
            "cloudflare": "https://failing.example.com/incidents.json",
        }
    )
    assert succeeded == ["github"]
    assert failed == ["cloudflare"]
    assert len(df) == 1
    row = df.iloc[0]
    assert row["incident_id"] == "inc-1"
    assert bool(row["is_critical_major"]) is True
    assert row["duration_minutes"] == pytest.approx(90.0)


def test_aggregate_real_incidents_by_day_empty_and_nonempty() -> None:
    empty = aggregate_real_incidents_by_day(pd.DataFrame())
    assert empty.empty
    assert list(empty.columns) == [
        "date",
        "real_incident_count",
        "real_critical_major_count",
        "real_mean_duration_min",
        "real_sources_affected",
    ]

    raw = pd.DataFrame(
        [
            {
                "incident_id": "a",
                "source": "github",
                "is_critical_major": True,
                "duration_minutes": 30.0,
                "date": "2024-04-10",
            },
            {
                "incident_id": "b",
                "source": "vercel",
                "is_critical_major": False,
                "duration_minutes": 60.0,
                "date": "2024-04-10",
            },
        ]
    )
    agg = aggregate_real_incidents_by_day(raw)
    assert len(agg) == 1
    assert agg.iloc[0]["real_incident_count"] == 2
    assert agg.iloc[0]["real_critical_major_count"] == 1
    assert agg.iloc[0]["real_mean_duration_min"] == pytest.approx(45.0)
    assert agg.iloc[0]["real_sources_affected"] == 2


def test_build_and_save_dataset_falls_back_to_cached_raw_on_empty_refresh(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cached_raw = pd.DataFrame(
        [
            {
                "incident_id": "cached-1",
                "source": "github",
                "name": "Cached outage",
                "impact": "major",
                "is_critical_major": True,
                "status": "resolved",
                "created_at_utc": "2024-04-10T08:00:00+00:00",
                "date": "2024-04-10",
                "duration_minutes": 45.0,
            }
        ]
    )
    raw_path = tmp_path / "raw_public_incidents.csv"
    cached_raw.to_csv(raw_path, index=False)

    monkeypatch.setattr(
        "src.incidents.fetch_public_statuspage_incidents",
        lambda: (pd.DataFrame(columns=cached_raw.columns), [], ["github"]),
    )

    combined_df, raw_df, summary = build_and_save_dataset(
        data_dir=tmp_path,
        start_date="2024-04-08",
        end_date="2024-04-12",
        force_refresh=True,
    )
    assert len(raw_df) == 1
    assert summary.raw_incidents_fetched == 1
    assert summary.sources_succeeded == ("github",)
    assert summary.panel_days == 5
    assert (tmp_path / "daily_incidents_ephemeris.csv").exists()
    assert int(combined_df["real_incident_count"].sum()) == 1
