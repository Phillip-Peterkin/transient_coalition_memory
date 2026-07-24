"""Locked FluSight locations for year_multi_domain medical lane.

FIPS / hub codes. Locked before any scores.
"""

# Hub location codes (US + state FIPS).
FLUSIGHT_LOCATIONS = [
    "US",
    "06",  # CA
    "48",  # TX
    "36",  # NY
    "12",  # FL
    "17",  # IL
    "42",  # PA
    "39",  # OH
    "13",  # GA
    "37",  # NC
    "26",  # MI
    "53",  # WA
]

LOCATION_NAMES = {
    "US": "US",
    "06": "CA",
    "48": "TX",
    "36": "NY",
    "12": "FL",
    "17": "IL",
    "42": "PA",
    "39": "OH",
    "13": "GA",
    "37": "NC",
    "26": "MI",
    "53": "WA",
}

# Prefer models that historically submit often; collector keeps intersection
# with models present on each reference week (min 4 required at eval open).
PREFERRED_MODELS = [
    "FluSight-baseline",
    "FluSight-ensemble",
    "CEPH-Rtrend_fluH",
    "CMU-TimeSeries",
    "GT-FluFNP",
    "UMass-trends_ensemble",
    "PSI-PROF",
    "NU_UCSD-GLEAM_AI_FLUH",
]

# Inclusive reference-date window (~year of weekly FluSight activity).
MEDICAL_WINDOW_START = "2023-10-14"
MEDICAL_WINDOW_END = "2024-10-12"
