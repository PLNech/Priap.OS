#!/usr/bin/env python3
"""
Configuration file for Leek Wars Dataset Builder
"""

# Leek Wars API credentials
LOGIN = "PriapOS"
PASSWORD = "REDACTED_PASSWORD"

# Dataset settings
MAX_FIGHTS = 100
OUTPUT_PREFIX = "leekwars_fights"

# Rate limiting settings (in seconds)
REQUEST_DELAY = 1.0

# API endpoints
BASE_URL = "http://leekwars.com/api"