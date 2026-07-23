"""Locked city set for the clean Weather harness (do not edit after lock)."""

from __future__ import annotations

# (symbol, latitude, longitude, display name)
CITIES: list[tuple[str, float, float, str]] = [
    ("NYC", 40.7128, -74.0060, "New York"),
    ("CHI", 41.8781, -87.6298, "Chicago"),
    ("DEN", 39.7392, -104.9903, "Denver"),
    ("SEA", 47.6062, -122.3321, "Seattle"),
    ("LON", 51.5074, -0.1278, "London"),
    ("BER", 52.5200, 13.4050, "Berlin"),
    ("TOK", 35.6762, 139.6503, "Tokyo"),
    ("SYD", -33.8688, 151.2093, "Sydney"),
    ("SAO", -23.5505, -46.6333, "Sao Paulo"),
    ("JNB", -26.2041, 28.0473, "Johannesburg"),
    ("DEL", 28.6139, 77.2090, "Delhi"),
    ("CAI", 30.0444, 31.2357, "Cairo"),
]

MODELS: list[str] = [
    "gfs_seamless",
    "ecmwf_ifs025",
    "icon_seamless",
    "gem_seamless",
    "meteofrance_seamless",
    "jma_seamless",
    # cma_grapes_global omitted: ~9% missing days on this window (incomplete lock).
]

START_DATE = "2024-06-01"
END_DATE = "2025-12-31"
TIMEZONE = "UTC"
