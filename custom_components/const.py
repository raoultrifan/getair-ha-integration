"""Constants for the getAir integration."""

DOMAIN = "getair"

AUTH_URL = "https://auth.getair.eu"
API_URL = "https://be01.ga-cc.de"
CLIENT_ID = "7jPuzDmLiKFF6oPtvsFUhBkyPahA7Lh5"

DEFAULT_SCAN_INTERVAL = 300  # 5 minutes in seconds

MODES = {
    "Heat Recovery": "ventilate_hr",
    "Left (Normal)": "ventilate",
    "Right (Inverse)": "ventilate_inv",
    "Rush HR": "rush_hr",
}

MODES_REVERSE = {v: k for k, v in MODES.items()}
