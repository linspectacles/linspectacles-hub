#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2026 brunonlinespace
# GPL-3.0-or-later

"""Runtime classification for LinSpectacles Hub.

This module answers one question only: how is *this Hub* deployed?

Source Hub:
  * Portable   -> Hub-owned configuration/data live beside the source tree.
  * Integrated -> Hub-owned configuration/data live in XDG user locations.

Packaged Hub:
  * Always integrated with the operating system.
  * Hub-owned mutable configuration/data live in XDG user locations.

Component-source policy is intentionally separate.  Applet/module discovery and
Manual-vs-Managed presentation are not decided here.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path

RUNTIME_SOURCE = "source"
RUNTIME_PACKAGED = "packaged"
SOURCE_PORTABLE = "portable"
SOURCE_INTEGRATED = "integrated"
SOURCE_MODE_VALUES = {SOURCE_PORTABLE, SOURCE_INTEGRATED}
RUNTIME_MARKER_NAME = "linspectacles-runtime.json"
SOURCE_AUTO = "auto"
SOURCE_MARKER_VALUES = {SOURCE_AUTO, SOURCE_PORTABLE, SOURCE_INTEGRATED}


from .launcher import desktop_entry_targets_program


def _read_source_mode_marker(program_root):
    marker = Path(program_root) / RUNTIME_MARKER_NAME
    try:
        raw = json.loads(marker.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    if not isinstance(raw, dict):
        return None
    value = str(raw.get("source_mode", "")).strip().lower()
    return value if value in SOURCE_MARKER_VALUES else None



def write_source_mode_marker(program_root, source_mode):
    source_mode = str(source_mode).strip().lower()
    if source_mode not in SOURCE_MODE_VALUES:
        raise ValueError("Unsupported Source runtime mode.")
    marker = Path(program_root).resolve() / RUNTIME_MARKER_NAME
    payload = {
        "schema": 1,
        "distribution": RUNTIME_SOURCE,
        "source_mode": source_mode,
    }
    tmp = marker.with_suffix(marker.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, marker)
    return marker


@dataclass(frozen=True)
class RuntimeProfile:
    program_root: Path
    distribution: str
    source_mode: str | None
    managed_provider: str | None

    @classmethod
    def detect(cls, program_root, integrated_source=False):
        program_root = Path(program_root).resolve()

        # Backward-compatible with the current Fedora launcher while allowing
        # future package providers to use the generic packaged classification.
        install_mode = os.environ.get("LINSPECTACLES_INSTALL_MODE", "").strip().lower()
        explicit_kind = os.environ.get("LINSPECTACLES_RUNTIME_KIND", "").strip().lower()
        packaged = explicit_kind == RUNTIME_PACKAGED or install_mode in {
            "rpm", "deb", "flatpak", RUNTIME_PACKAGED,
        }

        if packaged:
            provider = os.environ.get("LINSPECTACLES_PACKAGE_PROVIDER", "").strip()
            if not provider:
                provider = install_mode.upper() if install_mode and install_mode != RUNTIME_PACKAGED else "Managed"
            return cls(
                program_root=program_root,
                distribution=RUNTIME_PACKAGED,
                source_mode=None,
                managed_provider=provider,
            )

        requested_mode = os.environ.get("LINSPECTACLES_SOURCE_MODE", "").strip().lower()
        if requested_mode not in SOURCE_MODE_VALUES:
            marker_mode = _read_source_mode_marker(program_root)
            if marker_mode in SOURCE_MODE_VALUES:
                # An explicit user-selected Source mode outranks launcher context.
                requested_mode = marker_mode
            elif integrated_source or desktop_entry_targets_program(program_root):
                requested_mode = SOURCE_INTEGRATED
            else:
                requested_mode = SOURCE_PORTABLE

        return cls(
            program_root=program_root,
            distribution=RUNTIME_SOURCE,
            source_mode=requested_mode,
            managed_provider=None,
        )

    @property
    def packaged(self):
        return self.distribution == RUNTIME_PACKAGED

    @property
    def source(self):
        return self.distribution == RUNTIME_SOURCE

    @property
    def portable(self):
        return self.source and self.source_mode == SOURCE_PORTABLE

    @property
    def integrated(self):
        return self.packaged or self.source_mode == SOURCE_INTEGRATED

    @property
    def mode(self):
        if self.packaged:
            return RUNTIME_PACKAGED
        return self.source_mode or SOURCE_PORTABLE

    @property
    def display_name(self):
        if self.packaged:
            provider = self.managed_provider or "Managed"
            return f"Packaged — {provider}"
        return "Source — Integrated" if self.integrated else "Source — Portable"

    @property
    def desktop_integration_expected(self):
        return self.integrated

    @property
    def uses_xdg_state(self):
        return self.integrated
