#!/usr/bin/env python3
"""Offline Card2 First Dose tests. Synthetic only; no network or private user data."""
import unittest
from pathlib import Path
suite=unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent),pattern='test_card2_first_dose.py')
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
