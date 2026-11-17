"""Parity unit tests mirroring ``AstrologyEngineTest.kt``."""

from datetime import datetime, timezone

import astronomy
import pytest

from src.ephemeris import (
    SYNODIC_MONTH_DAYS,
    AstrologyEngine,
    LunarPhaseStatus,
    PlanetaryMotionState,
    ZodiacSign,
    generate_ephemeris_df,
)


def test_zodiac_sign_mapping_including_wrap_around() -> None:
    assert ZodiacSign.from_ecliptic_longitude(0.0) == ZodiacSign.ARIES
    assert ZodiacSign.from_ecliptic_longitude(29.9) == ZodiacSign.ARIES
    assert ZodiacSign.from_ecliptic_longitude(30.0) == ZodiacSign.TAURUS
    assert ZodiacSign.from_ecliptic_longitude(234.0) == ZodiacSign.SCORPIO
    assert ZodiacSign.from_ecliptic_longitude(359.5) == ZodiacSign.PISCES
    assert ZodiacSign.from_ecliptic_longitude(360.0) == ZodiacSign.ARIES
    assert ZodiacSign.from_ecliptic_longitude(-1.0) == ZodiacSign.PISCES


def test_zodiac_sign_and_motion_state_bilingual_labels() -> None:
    assert ZodiacSign.SCORPIO.localized_name(is_spanish=True) == "Escorpio"
    assert ZodiacSign.SCORPIO.localized_name(is_spanish=False) == "Scorpio"
    assert PlanetaryMotionState.RETROGRADE.localized_badge(is_spanish=True) == "Retrógrado"
    assert PlanetaryMotionState.RETROGRADE.localized_badge(is_spanish=False) == "Retrograde"


def test_compute_snapshot_returns_five_planets_and_valid_lunar_status() -> None:
    sample_dt = datetime(2026, 11, 16, 12, 0, 0, tzinfo=timezone.utc)
    snapshot = AstrologyEngine.compute_snapshot(sample_dt)

    assert snapshot.sun_sign == ZodiacSign.SCORPIO
    assert 0.0 <= snapshot.sun_degree_in_sign <= 30.0
    assert len(snapshot.planets) == 5
    assert any(p.body == astronomy.Body.Mercury for p in snapshot.planets)
    assert 0 <= snapshot.lunar_status.illumination_percent <= 100
    assert 0.0 <= snapshot.lunar_status.phase_angle_deg <= 360.0
    assert snapshot.lunar_status.localized_phase_name(is_spanish=True).strip() != ""
    assert snapshot.lunar_status.localized_phase_name(is_spanish=False).strip() != ""


def test_mercury_retrograde_detected_in_april_2024_window() -> None:
    retro_dt = datetime(2024, 4, 10, 12, 0, 0, tzinfo=timezone.utc)
    mercury = AstrologyEngine.compute_snapshot(retro_dt).mercury_status

    assert mercury.motion_state == PlanetaryMotionState.RETROGRADE
    assert mercury.is_retrograde is True
    assert mercury.daily_speed_deg < 0.0


def test_mercury_direct_detected_outside_retrograde_and_shadow_windows() -> None:
    direct_dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    mercury = AstrologyEngine.compute_snapshot(direct_dt).mercury_status

    assert mercury.motion_state == PlanetaryMotionState.DIRECT
    assert mercury.is_retrograde is False
    assert mercury.daily_speed_deg > 0.0


def test_lunar_phase_status_synodic_age_and_trend() -> None:
    sample_dt = datetime(2026, 11, 16, 12, 0, 0, tzinfo=timezone.utc)
    lunar = AstrologyEngine.compute_snapshot(sample_dt).lunar_status

    assert 0.0 <= lunar.synodic_age_days <= 29.54
    assert 0.0 <= lunar.normalized_phase_angle_deg <= 360.0
    expected_es = "Creciente" if lunar.is_waxing else "Menguante"
    expected_en = "Waxing" if lunar.is_waxing else "Waning"
    assert lunar.localized_cycle_trend(is_spanish=True) == expected_es
    assert lunar.localized_cycle_trend(is_spanish=False) == expected_en


def test_lunar_phase_status_exact_boundaries() -> None:
    first_quarter = LunarPhaseStatus(
        phase_angle_deg=90.0,
        illumination_fraction=0.5,
        phase_name_es="Cuarto Creciente",
        phase_name_en="First Quarter",
        moon_sign=ZodiacSign.ARIES,
    )
    assert first_quarter.normalized_phase_angle_deg == pytest.approx(90.0, abs=1e-6)
    assert first_quarter.synodic_age_days == pytest.approx(SYNODIC_MONTH_DAYS * 0.25, abs=1e-4)
    assert first_quarter.is_waxing is True
    assert first_quarter.localized_cycle_trend(is_spanish=True) == "Creciente"
    assert first_quarter.localized_cycle_trend(is_spanish=False) == "Waxing"
    assert first_quarter.illumination_percent == 50

    full_moon = LunarPhaseStatus(
        phase_angle_deg=180.0,
        illumination_fraction=1.2,
        phase_name_es="Luna Llena",
        phase_name_en="Full Moon",
        moon_sign=ZodiacSign.ARIES,
    )
    assert full_moon.normalized_phase_angle_deg == pytest.approx(180.0, abs=1e-6)
    assert full_moon.synodic_age_days == pytest.approx(SYNODIC_MONTH_DAYS * 0.5, abs=1e-4)
    assert full_moon.is_waxing is False
    assert full_moon.localized_cycle_trend(is_spanish=True) == "Menguante"
    assert full_moon.localized_cycle_trend(is_spanish=False) == "Waning"
    assert full_moon.illumination_percent == 100

    negative_angle = LunarPhaseStatus(
        phase_angle_deg=-90.0,
        illumination_fraction=-0.1,
        phase_name_es="Cuarto Menguante",
        phase_name_en="Last Quarter",
        moon_sign=ZodiacSign.ARIES,
    )
    assert negative_angle.normalized_phase_angle_deg == pytest.approx(270.0, abs=1e-6)
    assert negative_angle.is_waxing is False
    assert negative_angle.illumination_percent == 0


def test_generate_ephemeris_df_returns_expected_columns_and_rows() -> None:
    df = generate_ephemeris_df("2024-04-08", "2024-04-12")
    assert len(df) == 5
    assert df["mercury_is_retrograde"].all()
    assert "moon_phase_sin" in df.columns
    assert "saturn_motion_state" in df.columns
