#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# LinSpectacles - Linux Inspection Suite
# Copyright (C) 2026 brunonlinespace
# GPL-3.0-or-later

import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidgetItem

DASHBOARD_ID = "__dashboard__"
NAV_META_ROLE = Qt.ItemDataRole.UserRole + 1
NAV_LOGICAL_ROLE = Qt.ItemDataRole.UserRole + 2
APPLET_LOGICAL_ROLE = Qt.ItemDataRole.UserRole + 2



def _natural_sort_key(value):
    """Case-insensitive natural key used by Configuration table items."""
    if isinstance(value, bool):
        return (0, int(value))
    if isinstance(value, (int, float)):
        return (0, float(value))
    text = str(value if value is not None else "")
    parts = re.split(r"(\d+)", text.casefold())
    return (1, tuple(int(part) if part.isdigit() else part for part in parts))


class SortableTableWidgetItem(QTableWidgetItem):
    """QTableWidgetItem with an explicit stable sort value when needed."""

    def __init__(self, text="", sort_value=None):
        super().__init__(str(text))
        self._sort_value = text if sort_value is None else sort_value

    def set_sort_value(self, value):
        self._sort_value = value

    def __lt__(self, other):
        if isinstance(other, SortableTableWidgetItem):
            return _natural_sort_key(self._sort_value) < _natural_sort_key(other._sort_value)
        return super().__lt__(other)


def component_ownership_label(manifest):
    """User-facing ownership label for a discovered component instance."""
    return "User" if getattr(manifest, "origin", "") == "manual" else "Package-managed"


def component_provider_label(manifest, runtime_paths=None):
    """Human provenance without exposing the obsolete Shared terminology."""
    if manifest is None:
        return "—"
    if getattr(manifest, "origin", "") == "manual":
        if runtime_paths is not None and getattr(runtime_paths, "portable", False):
            return "Portable folder"
        return "XDG user data"
    source = str(getattr(manifest, "source", "") or "").strip()
    if source and source.casefold() not in {"managed", "system"}:
        return source
    provider = getattr(runtime_paths, "managed_provider", None) if runtime_paths is not None else None
    return str(provider or "Package provider")

# Permissive offline module catalogue. This enriches Configuration only; it is
# never a whitelist and never performs network/store/install operations.
MODULE_CATALOG = {
    "applet-organizer": {"name": "Applet Organizer", "dashboard_reorderable": True},
    "boot-environment": {"name": "Boot Environment", "dashboard_reorderable": True},
    "encyclopedia": {"name": "Encyclopedia & What's This?", "dashboard_reorderable": True},
    "privileged-helpers": {"name": "Privileged Helpers", "dashboard_reorderable": False},
    "system-identity": {"name": "System Identity", "dashboard_reorderable": True},
    "system-pulse": {"name": "System Pulse", "dashboard_reorderable": True},
}
