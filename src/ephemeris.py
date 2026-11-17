"""Offline astronomical and astrological ephemeris calculator.

Direct Python port of ``AstrologyEngine.kt`` using ``astronomy-engine`` to guarantee
100% behavioral parity with the One UI Extra Widgets mobile engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import math
from typing import Iterable

import astronomy
import pandas as pd


SYNODIC_MONTH_DAYS = 29.530588


class ZodiacSign(Enum):
    """Twelve tropical zodiac signs mapped from 30-degree ecliptic segments."""

    ARIES = ("♈", "Aries", "Aries")
    TAURUS = ("♉", "Tauro", "Taurus")
    GEMINI = ("♊", "Géminis", "Gemini")
    CANCER = ("♋", "Cáncer", "Cancer")
    LEO = ("♌", "Leo", "Leo")
    VIRGO = ("♍", "Virgo", "Virgo")
    LIBRA = ("♎", "Libra", "Libra")
    SCORPIO = ("♏", "Escorpio", "Scorpio")
    SAGITTARIUS = ("♐", "Sagitario", "Sagittarius")
    CAPRICORN = ("♑", "Capricornio", "Capricorn")
    AQUARIUS = ("♒", "Acuario", "Aquarius")
    PISCES = ("♓", "Piscis", "Pisces")

    def __init__(self, symbol: str, name_es: str, name_en: str) -> None:
        self.symbol = symbol
        self.name_es = name_es
        self.name_en = name_en

    def localized_name(self, is_spanish: bool) -> str:
        """Return the localized sign name in Spanish or English."""
        return self.name_es if is_spanish else self.name_en

    @classmethod
    def from_ecliptic_longitude(cls, longitude_deg: float) -> ZodiacSign:
        """Map an ecliptic longitude in degrees to its tropical zodiac sign."""
        normalized = ((longitude_deg % 360.0) + 360.0) % 360.0
        index = max(0, min(11, int(normalized / 30.0)))
        return list(cls)[index]


class PlanetaryMotionState(Enum):
    """Apparent geocentric planetary motion state relative to Earth."""

    DIRECT = ("Directo", "Direct")
    RETROGRADE = ("Retrógrado", "Retrograde")
    PRE_SHADOW = ("Sombra Pre-Retrógrada", "Pre-Retrograde Shadow")
    POST_SHADOW = ("Sombra Post-Retrógrada", "Post-Retrograde Shadow")

    def __init__(self, badge_es: str, badge_en: str) -> None:
        self.badge_es = badge_es
        self.badge_en = badge_en

    def localized_badge(self, is_spanish: bool) -> str:
        """Return the localized motion badge in Spanish or English."""
        return self.badge_es if is_spanish else self.badge_en


@dataclass(frozen=True)
class LunarPhaseStatus:
    """Scientific and zodiacal lunar metrics for a single instant."""

    phase_angle_deg: float
    illumination_fraction: float
    phase_name_es: str
    phase_name_en: str
    moon_sign: ZodiacSign

    @property
    def illumination_percent(self) -> int:
        """Return lunar illumination percentage clamped to [0, 100]."""
        return max(0, min(100, int(self.illumination_fraction * 100.0)))

    @property
    def normalized_phase_angle_deg(self) -> float:
        """Return lunar phase angle normalized into [0, 360)."""
        return ((self.phase_angle_deg % 360.0) + 360.0) % 360.0

    @property
    def synodic_age_days(self) -> float:
        """Return approximate days elapsed since New Moon."""
        return (self.normalized_phase_angle_deg / 360.0) * SYNODIC_MONTH_DAYS

    @property
    def is_waxing(self) -> bool:
        """Return True during waxing phases (phase angle < 180 deg)."""
        return self.normalized_phase_angle_deg < 180.0

    def localized_phase_name(self, is_spanish: bool) -> str:
        """Return the localized lunar phase classification."""
        return self.phase_name_es if is_spanish else self.phase_name_en

    def localized_cycle_trend(self, is_spanish: bool) -> str:
        """Return localized waxing/waning trend label."""
        if self.is_waxing:
            return "Creciente" if is_spanish else "Waxing"
        return "Menguante" if is_spanish else "Waning"


@dataclass(frozen=True)
class PlanetTransitStatus:
    """Ephemeris transit status for a single tracked planet."""

    body: astronomy.Body
    symbol: str
    name_es: str
    name_en: str
    zodiac_sign: ZodiacSign
    degree_in_sign: float
    daily_speed_deg: float
    motion_state: PlanetaryMotionState

    @property
    def is_retrograde(self) -> bool:
        """Return True if the planet is currently in apparent retrograde motion."""
        return self.motion_state == PlanetaryMotionState.RETROGRADE

    def localized_name(self, is_spanish: bool) -> str:
        """Return the localized planet name."""
        return self.name_es if is_spanish else self.name_en


@dataclass(frozen=True)
class AstrologySnapshot:
    """Aggregated solar, lunar, and planetary snapshot for a timestamp."""

    sun_sign: ZodiacSign
    sun_degree_in_sign: float
    lunar_status: LunarPhaseStatus
    planets: tuple[PlanetTransitStatus, ...]

    @property
    def mercury_status(self) -> PlanetTransitStatus:
        """Return the Mercury transit status from the snapshot."""
        return next(p for p in self.planets if p.body == astronomy.Body.Mercury)


@dataclass(frozen=True)
class _PlanetMeta:
    body: astronomy.Body
    symbol: str
    name_es: str
    name_en: str
    shadow_window_days: float


class AstrologyEngine:
    """100% offline ephemeris calculator matching ``AstrologyEngine.kt``."""

    TRACKED_PLANETS: tuple[_PlanetMeta, ...] = (
        _PlanetMeta(astronomy.Body.Mercury, "☿", "Mercurio", "Mercury", shadow_window_days=14.0),
        _PlanetMeta(astronomy.Body.Venus, "♀", "Venus", "Venus", shadow_window_days=28.0),
        _PlanetMeta(astronomy.Body.Mars, "♂", "Marte", "Mars", shadow_window_days=35.0),
        _PlanetMeta(astronomy.Body.Jupiter, "♃", "Júpiter", "Jupiter", shadow_window_days=25.0),
        _PlanetMeta(astronomy.Body.Saturn, "♄", "Saturno", "Saturn", shadow_window_days=25.0),
    )

    @staticmethod
    def to_astronomy_time(dt: datetime) -> astronomy.Time:
        """Convert a Python ``datetime`` into an ``astronomy.Time`` in UTC."""
        utc_dt = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
        seconds = utc_dt.second + utc_dt.microsecond / 1_000_000.0
        return astronomy.Time.Make(
            utc_dt.year,
            utc_dt.month,
            utc_dt.day,
            utc_dt.hour,
            utc_dt.minute,
            seconds,
        )

    @staticmethod
    def geocentric_ecliptic_longitude(body: astronomy.Body, time: astronomy.Time) -> float:
        """Compute apparent geocentric ecliptic longitude in [0, 360) degrees."""
        vec = astronomy.GeoVector(body, time, True)
        ecl = astronomy.Ecliptic(vec)
        return ((ecl.elon % 360.0) + 360.0) % 360.0

    @staticmethod
    def angular_delta_degrees(from_deg: float, to_deg: float) -> float:
        """Wrap signed angular difference ``to_deg - from_deg`` into (-180, 180]."""
        diff = (to_deg - from_deg) % 360.0
        if diff > 180.0:
            diff -= 360.0
        return diff

    @staticmethod
    def classify_moon_phase_name(angle_deg: float) -> tuple[str, str]:
        """Classify lunar phase angle [0, 360) into eight bilingual phase labels."""
        a = ((angle_deg % 360.0) + 360.0) % 360.0
        if a < 22.5 or a >= 337.5:
            return ("Luna Nueva", "New Moon")
        if a < 67.5:
            return ("Luna Creciente", "Waxing Crescent")
        if a < 112.5:
            return ("Cuarto Creciente", "First Quarter")
        if a < 157.5:
            return ("Gibosa Creciente", "Waxing Gibbous")
        if a < 202.5:
            return ("Luna Llena", "Full Moon")
        if a < 247.5:
            return ("Gibosa Menguante", "Waning Gibbous")
        if a < 292.5:
            return ("Cuarto Menguante", "Last Quarter")
        return ("Luna Menguante", "Waning Crescent")

    @classmethod
    def compute_snapshot(cls, dt: datetime | None = None) -> AstrologySnapshot:
        """Compute a deterministic solar, lunar, and planetary snapshot for ``dt``."""
        target_dt = datetime.now(timezone.utc) if dt is None else dt
        time = cls.to_astronomy_time(target_dt)

        # 1. Sun Sign & position
        sun_ecliptic = astronomy.SunPosition(time)
        sun_sign = ZodiacSign.from_ecliptic_longitude(sun_ecliptic.elon)
        sun_deg_in_sign = ((sun_ecliptic.elon % 360.0) + 360.0) % 30.0

        # 2. Moon Phase, Illumination & Moon Zodiac Transit
        phase_angle = astronomy.MoonPhase(time)
        moon_illum = astronomy.Illumination(astronomy.Body.Moon, time).phase_fraction
        moon_ecliptic = astronomy.EclipticGeoMoon(time)
        moon_sign = ZodiacSign.from_ecliptic_longitude(moon_ecliptic.lon)
        phase_es, phase_en = cls.classify_moon_phase_name(phase_angle)

        lunar_status = LunarPhaseStatus(
            phase_angle_deg=phase_angle,
            illumination_fraction=moon_illum,
            phase_name_es=phase_es,
            phase_name_en=phase_en,
            moon_sign=moon_sign,
        )

        # 3. Planetary Positions & Retrograde / Shadow Detection
        planet_statuses: list[PlanetTransitStatus] = []
        for meta in cls.TRACKED_PLANETS:
            lon_now = cls.geocentric_ecliptic_longitude(meta.body, time)
            lon_tomorrow = cls.geocentric_ecliptic_longitude(meta.body, time.AddDays(1.0))
            daily_speed = cls.angular_delta_degrees(lon_now, lon_tomorrow)

            if daily_speed < 0.0:
                motion_state = PlanetaryMotionState.RETROGRADE
            else:
                lon_future = cls.geocentric_ecliptic_longitude(meta.body, time.AddDays(meta.shadow_window_days))
                lon_future_next = cls.geocentric_ecliptic_longitude(
                    meta.body, time.AddDays(meta.shadow_window_days + 1.0)
                )
                future_speed = cls.angular_delta_degrees(lon_future, lon_future_next)

                lon_past = cls.geocentric_ecliptic_longitude(meta.body, time.AddDays(-meta.shadow_window_days))
                lon_past_next = cls.geocentric_ecliptic_longitude(
                    meta.body, time.AddDays(-meta.shadow_window_days + 1.0)
                )
                past_speed = cls.angular_delta_degrees(lon_past, lon_past_next)

                if future_speed < 0.0:
                    motion_state = PlanetaryMotionState.PRE_SHADOW
                elif past_speed < 0.0:
                    motion_state = PlanetaryMotionState.POST_SHADOW
                else:
                    motion_state = PlanetaryMotionState.DIRECT

            planet_statuses.append(
                PlanetTransitStatus(
                    body=meta.body,
                    symbol=meta.symbol,
                    name_es=meta.name_es,
                    name_en=meta.name_en,
                    zodiac_sign=ZodiacSign.from_ecliptic_longitude(lon_now),
                    degree_in_sign=((lon_now % 360.0) + 360.0) % 30.0,
                    daily_speed_deg=daily_speed,
                    motion_state=motion_state,
                )
            )

        return AstrologySnapshot(
            sun_sign=sun_sign,
            sun_degree_in_sign=sun_deg_in_sign,
            lunar_status=lunar_status,
            planets=tuple(planet_statuses),
        )


PLANET_LABELS: dict[str, tuple[str, str]] = {
    meta.name_en.lower(): (meta.name_en, meta.name_es)
    for meta in AstrologyEngine.TRACKED_PLANETS
}

STATE_LABELS: dict[str, tuple[str, str]] = {
    "RETROGRADE": ("Retrograde", PlanetaryMotionState.RETROGRADE.badge_es),
    "PRE_SHADOW": ("Pre-Shadow", PlanetaryMotionState.PRE_SHADOW.badge_es),
    "POST_SHADOW": ("Post-Shadow", PlanetaryMotionState.POST_SHADOW.badge_es),
    "DIRECT": ("Direct", PlanetaryMotionState.DIRECT.badge_es),
}

LUNAR_PHASES_EN_ES: list[tuple[str, str]] = [
    ("New Moon", "Luna Nueva"),
    ("Waxing Crescent", "Luna Creciente"),
    ("First Quarter", "Cuarto Creciente"),
    ("Waxing Gibbous", "Gibosa Creciente"),
    ("Full Moon", "Luna Llena"),
    ("Waning Gibbous", "Gibosa Menguante"),
    ("Last Quarter", "Cuarto Menguante"),
    ("Waning Crescent", "Luna Menguante"),
]


def generate_ephemeris_df(
    start_date: str,
    end_date: str,
    hour_utc: int = 12,
) -> pd.DataFrame:
    """Generate a daily ephemeris DataFrame evaluated at ``hour_utc`` UTC."""
    dates: Iterable[pd.Timestamp] = pd.date_range(start=start_date, end=end_date, freq="D", tz="UTC")
    rows: list[dict[str, object]] = []

    for ts in dates:
        dt = ts.to_pydatetime().replace(hour=hour_utc, minute=0, second=0, microsecond=0)
        snap = AstrologyEngine.compute_snapshot(dt)
        lunar = snap.lunar_status
        phase_rad = math.radians(lunar.normalized_phase_angle_deg)

        row: dict[str, object] = {
            "date": ts.strftime("%Y-%m-%d"),
            "sun_sign": snap.sun_sign.name_en,
            "sun_degree_in_sign": round(snap.sun_degree_in_sign, 4),
            "moon_phase_angle_deg": round(lunar.normalized_phase_angle_deg, 4),
            "moon_illumination_fraction": round(lunar.illumination_fraction, 6),
            "moon_illumination_percent": lunar.illumination_percent,
            "moon_synodic_age_days": round(lunar.synodic_age_days, 4),
            "moon_is_waxing": lunar.is_waxing,
            "moon_phase_name_en": lunar.phase_name_en,
            "moon_phase_name_es": lunar.phase_name_es,
            "moon_sign": lunar.moon_sign.name_en,
            "moon_phase_sin": round(math.sin(phase_rad), 6),
            "moon_phase_cos": round(math.cos(phase_rad), 6),
            "is_full_moon": lunar.phase_name_en == "Full Moon",
            "is_new_moon": lunar.phase_name_en == "New Moon",
        }

        retrograde_count = 0
        personal_retrograde = False
        for planet in snap.planets:
            key = planet.name_en.lower()
            row[f"{key}_sign"] = planet.zodiac_sign.name_en
            row[f"{key}_degree_in_sign"] = round(planet.degree_in_sign, 4)
            row[f"{key}_daily_speed_deg"] = round(planet.daily_speed_deg, 5)
            row[f"{key}_motion_state"] = planet.motion_state.name
            row[f"{key}_is_retrograde"] = planet.is_retrograde
            row[f"{key}_is_pre_shadow"] = planet.motion_state == PlanetaryMotionState.PRE_SHADOW
            row[f"{key}_is_post_shadow"] = planet.motion_state == PlanetaryMotionState.POST_SHADOW
            if planet.is_retrograde:
                retrograde_count += 1
                if key in {"mercury", "venus", "mars"}:
                    personal_retrograde = True

        row["any_retrograde_count"] = retrograde_count
        row["any_personal_retrograde"] = personal_retrograde
        rows.append(row)

    return pd.DataFrame(rows)
