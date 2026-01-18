#!/usr/bin/env python3
"""
Configuration file for Leek Wars Dataset Builder

Credentials are loaded from environment variables:
    export LEEKWARS_USER="your_email"
    export LEEKWARS_PASS="your_password"
"""

import os

# Leek Wars API credentials (from environment)
LOGIN = os.environ.get("LEEKWARS_USER", "")
PASSWORD = os.environ.get("LEEKWARS_PASS", "")

# Dataset settings
MAX_FIGHTS = 100
OUTPUT_PREFIX = "leekwars_fights"

# Rate limiting settings (in seconds)
REQUEST_DELAY = 1.0

# API endpoints
BASE_URL = "http://leekwars.com/api"
