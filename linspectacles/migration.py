#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2026 brunonlinespace
# GPL-3.0-or-later

"""Safe Source Portable <-> Integrated migration for LinSpectacles Hub."""

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .launcher import (
    install_source_launcher,
    remove_source_launchers,
    restore_source_launchers,
)
from .paths import RuntimePaths
from .runtime import SOURCE_INTEGRATED, SOURCE_PORTABLE, write_source_mode_marker


@dataclass(frozen=True)
class MigrationPlan:
    current: RuntimePaths
    target: RuntimePaths
    target_mode: str
    config_conflict: bool
    applet_conflicts: tuple
    module_conflicts: tuple


@dataclass(frozen=True)
class MigrationResult:
    target_mode: str
    copied_applets: tuple
    copied_modules: tuple
    skipped_applets: tuple
    skipped_modules: tuple
    config_action: str


def _child_names(directory):
    path = Path(directory)
    if not path.is_dir():
        return []
    try:
        return sorted(
            child.name for child in path.iterdir()
            if child.is_dir() and not child.is_symlink() and not child.name.startswith("_")
        )
    except OSError:
        return []


def build_plan(runtime_paths, target_mode):
    if runtime_paths.packaged:
        raise ValueError("Packaged LinSpectacles Hub runtimes cannot switch Portable/Integrated mode.")
    target_mode = str(target_mode).strip().lower()
    if target_mode not in {SOURCE_PORTABLE, SOURCE_INTEGRATED}:
        raise ValueError("Unsupported Source runtime target.")
    if target_mode == runtime_paths.runtime.source_mode:
        raise ValueError("LinSpectacles is already using that Source runtime mode.")

    target = RuntimePaths.for_source_mode(runtime_paths.program_root, target_mode)
    source_applets = runtime_paths.active_manual_applet_store
    source_modules = runtime_paths.active_manual_module_store
    target_applets = target.active_manual_applet_store
    target_modules = target.active_manual_module_store

    applet_conflicts = tuple(sorted(set(_child_names(source_applets)) & set(_child_names(target_applets))))
    module_conflicts = tuple(sorted(set(_child_names(source_modules)) & set(_child_names(target_modules))))
    config_conflict = target.config_file.exists() and target.config_file.resolve() != runtime_paths.config_file.resolve()
    return MigrationPlan(
        current=runtime_paths,
        target=target,
        target_mode=target_mode,
        config_conflict=config_conflict,
        applet_conflicts=applet_conflicts,
        module_conflicts=module_conflicts,
    )


def _backup_existing(path):
    path = Path(path)
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = path.with_name(path.name + f".pre-migration-{stamp}.bak")
    counter = 1
    while candidate.exists():
        candidate = path.with_name(path.name + f".pre-migration-{stamp}-{counter}.bak")
        counter += 1
    shutil.copy2(path, candidate)
    return candidate


def _copy_components(source_dir, target_dir, enabled, skip_conflicts):
    copied = []
    skipped = []
    if not enabled:
        return copied, skipped
    source_dir = Path(source_dir)
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    if not source_dir.is_dir():
        return copied, skipped
    for child in sorted(source_dir.iterdir(), key=lambda p: p.name.casefold()):
        if not child.is_dir() or child.is_symlink() or child.name.startswith("_"):
            continue
        destination = target_dir / child.name
        if destination.exists():
            if child.name in skip_conflicts:
                skipped.append(child.name)
                continue
            raise FileExistsError(f"Destination component already exists: {destination}")
        shutil.copytree(child, destination, symlinks=True)
        copied.append(child.name)
    return copied, skipped



def copy_legacy_manual_root(source_root, target_root):
    """Copy legacy 0.1.5 Manual components into the runtime-owned Manual root.

    Existing destination component folders are skipped, never overwritten.
    The legacy source is never removed.
    """
    source_root = Path(source_root)
    target_root = Path(target_root)
    copied_applets, skipped_applets = _copy_components(
        source_root / "applets", target_root / "applets", True,
        set(_child_names(source_root / "applets")) & set(_child_names(target_root / "applets")),
    )
    copied_modules, skipped_modules = _copy_components(
        source_root / "modules", target_root / "modules", True,
        set(_child_names(source_root / "modules")) & set(_child_names(target_root / "modules")),
    )
    return {
        "copied_applets": tuple(copied_applets),
        "skipped_applets": tuple(skipped_applets),
        "copied_modules": tuple(copied_modules),
        "skipped_modules": tuple(skipped_modules),
    }


def migrate_source_runtime(
    plan,
    *,
    copy_applets=True,
    copy_modules=True,
    config_policy="replace",
    skip_component_conflicts=True,
):
    """Execute a copy-first runtime migration.

    config_policy: "replace" (backup destination first) or "keep".
    Existing component directories are never overwritten. When
    skip_component_conflicts is True, they are reported as skipped.
    """
    if config_policy not in {"replace", "keep"}:
        raise ValueError("Unsupported configuration conflict policy.")

    current = plan.current
    target = plan.target
    target.ensure_config_dirs()
    target.ensure_active_manual_dirs()

    # Ensure the current in-use configuration is on disk before copying it.
    source_config = current.config_file
    target_config = target.config_file
    config_action = "none"
    if source_config.exists() and source_config.resolve() != target_config.resolve():
        if target_config.exists():
            if config_policy == "replace":
                _backup_existing(target_config)
                shutil.copy2(source_config, target_config)
                config_action = "replaced"
            else:
                config_action = "kept"
        else:
            target_config.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_config, target_config)
            config_action = "copied"

    applet_skips = set(plan.applet_conflicts) if skip_component_conflicts else set()
    module_skips = set(plan.module_conflicts) if skip_component_conflicts else set()
    copied_applets, skipped_applets = _copy_components(
        current.active_manual_applet_store,
        target.active_manual_applet_store,
        copy_applets,
        applet_skips,
    )
    copied_modules, skipped_modules = _copy_components(
        current.active_manual_module_store,
        target.active_manual_module_store,
        copy_modules,
        module_skips,
    )

    removed_launchers = []
    created_launcher = None
    try:
        if plan.target_mode == SOURCE_PORTABLE:
            removed_launchers = remove_source_launchers(current.program_root)
        else:
            created_launcher = install_source_launcher(current.program_root)

        # Persist the mode last. This is the commit point for the runtime switch.
        write_source_mode_marker(current.program_root, plan.target_mode)
    except Exception:
        if created_launcher is not None:
            try:
                Path(created_launcher).unlink(missing_ok=True)
            except OSError:
                pass
        if removed_launchers:
            try:
                restore_source_launchers(removed_launchers)
            except OSError:
                pass
        raise

    return MigrationResult(
        target_mode=plan.target_mode,
        copied_applets=tuple(copied_applets),
        copied_modules=tuple(copied_modules),
        skipped_applets=tuple(skipped_applets),
        skipped_modules=tuple(skipped_modules),
        config_action=config_action,
    )
