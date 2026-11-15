#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2026 brunonlinespace
# GPL-3.0-or-later

"""Runtime storage and component-source paths for LinSpectacles Hub.

Source Portable keeps config and manual components inside the Hub tree. Source
Integrated and Packaged use XDG user locations for mutable state/manual
components. Managed/package components remain a separate discovered source.
"""

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from .runtime import RuntimeProfile, SOURCE_INTEGRATED, SOURCE_PORTABLE, RUNTIME_SOURCE


MANUAL_SHARED = "shared"
MANUAL_PORTABLE = "portable"
MANUAL_CUSTOM = "custom"
MANUAL_LOCATION_VALUES = {MANUAL_SHARED, MANUAL_PORTABLE, MANUAL_CUSTOM}


def _xdg_home(env_name, fallback):
    value = os.environ.get(env_name, "").strip()
    if value:
        candidate = Path(value).expanduser()
        if candidate.is_absolute():
            return candidate
    return Path(fallback).expanduser()


def _system_root():
    value = os.environ.get("LINSPECTACLES_SYSTEM_ROOT", "").strip()
    if value:
        candidate = Path(value).expanduser()
        if candidate.is_absolute():
            return candidate
    return Path("/usr/libexec/linspectacles")


@dataclass(frozen=True)
class RuntimePaths:
    program_root: Path
    runtime: RuntimeProfile
    config_root: Path
    data_root: Path
    config_file: Path
    module_storage_root: Path
    shared_root: Path
    portable_root: Path
    system_root: Path

    @property
    def mode(self):
        return self.runtime.mode

    @property
    def packaged(self):
        return self.runtime.packaged

    @property
    def portable(self):
        return self.runtime.portable

    @property
    def integrated(self):
        return self.runtime.integrated

    @property
    def build_label(self):
        return self.runtime.display_name

    @property
    def desktop_integration_expected(self):
        return self.runtime.desktop_integration_expected

    @property
    def managed_provider(self):
        return self.runtime.managed_provider

    @property
    def shared_applet_store(self):
        return self.shared_root / "applets"

    @property
    def shared_module_store(self):
        return self.shared_root / "modules"

    @property
    def portable_applet_store(self):
        return self.portable_root / "applets"

    @property
    def portable_module_store(self):
        return self.portable_root / "modules"

    @property
    def system_applet_store(self):
        return self.system_root / "applets"

    @property
    def system_module_store(self):
        return self.system_root / "modules"

    @property
    def active_manual_root(self):
        return self.portable_root if self.portable else self.shared_root

    @property
    def active_manual_applet_store(self):
        return self.active_manual_root / "applets"

    @property
    def active_manual_module_store(self):
        return self.active_manual_root / "modules"

    @property
    def active_manual_source_label(self):
        return "Portable" if self.portable else "Shared"

    @property
    def active_manual_source_key(self):
        return "portable" if self.portable else "shared"

    @classmethod
    def _from_runtime(cls, program_root, runtime):
        program_root = Path(program_root).resolve()
        xdg_config = _xdg_home("XDG_CONFIG_HOME", Path.home() / ".config") / "linspectacles"
        xdg_data = _xdg_home("XDG_DATA_HOME", Path.home() / ".local" / "share") / "linspectacles"

        if runtime.uses_xdg_state:
            config_root = xdg_config
            data_root = xdg_data
        else:
            config_root = program_root / "config"
            data_root = program_root

        system_root = program_root if runtime.packaged else _system_root()
        return cls(
            program_root=program_root,
            runtime=runtime,
            config_root=config_root,
            data_root=data_root,
            config_file=config_root / "linspectacles.json",
            module_storage_root=config_root / "modules",
            shared_root=xdg_data,
            portable_root=program_root,
            system_root=system_root,
        )

    @classmethod
    def for_program(cls, program_root, integrated_source=False):
        program_root = Path(program_root).resolve()
        runtime = RuntimeProfile.detect(program_root, integrated_source=integrated_source)
        return cls._from_runtime(program_root, runtime)

    @classmethod
    def for_source_mode(cls, program_root, source_mode):
        program_root = Path(program_root).resolve()
        source_mode = str(source_mode).strip().lower()
        if source_mode not in {SOURCE_PORTABLE, SOURCE_INTEGRATED}:
            raise ValueError("Unsupported Source runtime mode.")
        runtime = RuntimeProfile(
            program_root=program_root,
            distribution=RUNTIME_SOURCE,
            source_mode=source_mode,
            managed_provider=None,
        )
        return cls._from_runtime(program_root, runtime)

    def manual_root(self, location, custom_root=""):
        location = str(location or MANUAL_SHARED).strip().lower()
        if location not in MANUAL_LOCATION_VALUES:
            location = MANUAL_SHARED
        if location == MANUAL_PORTABLE:
            if self.packaged:
                raise ValueError("Portable manual storage is available only when running the Hub from source.")
            return self.portable_root
        if location == MANUAL_CUSTOM:
            text = str(custom_root or "").strip()
            if not text:
                raise ValueError("A custom manual component location has not been selected.")
            path = Path(text).expanduser()
            if not path.is_absolute():
                raise ValueError("The custom manual component location must be an absolute path.")
            return path.resolve()
        return self.shared_root

    def manual_source_key(self, location, custom_root=""):
        location = str(location or MANUAL_SHARED).strip().lower()
        if location == MANUAL_PORTABLE:
            return "portable"
        if location == MANUAL_CUSTOM:
            root = str(self.manual_root(location, custom_root))
            digest = hashlib.sha256(root.encode("utf-8")).hexdigest()[:12]
            return f"custom-{digest}"
        return "shared"

    def manual_source_label(self, location):
        location = str(location or MANUAL_SHARED).strip().lower()
        if location == MANUAL_PORTABLE:
            return "Portable"
        if location == MANUAL_CUSTOM:
            return "Custom"
        return "Shared"

    def manual_applet_store(self, location, custom_root=""):
        return self.manual_root(location, custom_root) / "applets"

    def manual_module_store(self, location, custom_root=""):
        return self.manual_root(location, custom_root) / "modules"

    def ensure_config_dirs(self):
        for path in (self.config_root, self.module_storage_root):
            path.mkdir(parents=True, exist_ok=True)

    def ensure_active_manual_dirs(self):
        for path in (self.active_manual_applet_store, self.active_manual_module_store):
            path.mkdir(parents=True, exist_ok=True)

    def ensure_manual_dirs(self, location, custom_root=""):
        for path in (
            self.manual_applet_store(location, custom_root),
            self.manual_module_store(location, custom_root),
        ):
            path.mkdir(parents=True, exist_ok=True)
