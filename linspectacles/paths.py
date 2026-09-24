#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2026 brunonlinespace
# GPL-3.0-or-later

"""Runtime storage paths for portable and packaged LinSpectacles builds.

The portable edition retains its historical self-contained layout.  Packaged
(RPM) launchers opt in by setting ``LINSPECTACLES_INSTALL_MODE=rpm``; in that
mode every mutable path is user-owned and follows XDG base-directory defaults.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _xdg_home(env_name, fallback):
    value = os.environ.get(env_name, "").strip()
    if value:
        candidate = Path(value).expanduser()
        if candidate.is_absolute():
            return candidate
    return Path(fallback).expanduser()


@dataclass(frozen=True)
class RuntimePaths:
    program_root: Path
    mode: str
    config_root: Path
    data_root: Path
    config_file: Path
    applet_store: Path
    module_store: Path
    module_storage_root: Path
    system_applet_store: Optional[Path] = None
    system_module_store: Optional[Path] = None

    @property
    def packaged(self):
        return self.mode == "rpm"

    @property
    def build_label(self):
        return "RPM experiment" if self.packaged else "Modular portable source"

    @classmethod
    def for_program(cls, program_root):
        program_root = Path(program_root).resolve()
        requested = os.environ.get("LINSPECTACLES_INSTALL_MODE", "").strip().lower()
        packaged = requested == "rpm"
        if packaged:
            config_root = _xdg_home("XDG_CONFIG_HOME", Path.home() / ".config") / "linspectacles"
            data_root = _xdg_home("XDG_DATA_HOME", Path.home() / ".local" / "share") / "linspectacles"
            return cls(
                program_root=program_root,
                mode="rpm",
                config_root=config_root,
                data_root=data_root,
                config_file=config_root / "linspectacles.json",
                applet_store=data_root / "applets",
                module_store=data_root / "modules",
                module_storage_root=config_root / "modules",
                system_applet_store=program_root / "applets",
                system_module_store=program_root / "modules",
            )
        config_root = program_root / "config"
        data_root = program_root
        return cls(
            program_root=program_root,
            mode="portable",
            config_root=config_root,
            data_root=data_root,
            config_file=config_root / "linspectacles.json",
            applet_store=program_root / "applets",
            module_store=program_root / "modules",
            module_storage_root=config_root / "modules",
        )

    def ensure_mutable_dirs(self):
        for path in (
            self.config_root,
            self.applet_store,
            self.module_store,
            self.module_storage_root,
        ):
            path.mkdir(parents=True, exist_ok=True)
