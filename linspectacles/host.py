#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# LinSpectacles - Linux Inspection Suite
# Copyright (C) 2026 brunonlinespace
# GPL-3.0-or-later

"""Compatibility import surface for the LinSpectacles Hub.

The implementation was decomposed in 0.1.1. Existing callers importing the
previous host-owned window/dialog/delegate classes and constants continue to
resolve them from ``linspectacles.host`` unchanged.
"""

from .main_window import Linspectacles, run
from .ui.about import AboutDialog
from .ui.component_location import ManualComponentLocationDialog
from .ui.configuration_dialog import ConfigurationDialog
from .ui.navigation import AppletNavDelegate
from .ui.common import (
    APPLET_LOGICAL_ROLE,
    DASHBOARD_ID,
    MODULE_CATALOG,
    NAV_LOGICAL_ROLE,
    NAV_META_ROLE,
)

__all__ = [
    "Linspectacles",
    "run",
    "AboutDialog",
    "ManualComponentLocationDialog",
    "ConfigurationDialog",
    "AppletNavDelegate",
    "DASHBOARD_ID",
    "NAV_META_ROLE",
    "NAV_LOGICAL_ROLE",
    "APPLET_LOGICAL_ROLE",
    "MODULE_CATALOG",
]
