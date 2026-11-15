#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2026 brunonlinespace
# GPL-3.0-or-later

"""Desktop integration for source LinSpectacles Hub runtimes."""

import os
import shlex
import sys
from pathlib import Path


def _xdg_data_home():
    value = os.environ.get("XDG_DATA_HOME", "").strip()
    if value:
        candidate = Path(value).expanduser()
        if candidate.is_absolute():
            return candidate
    return Path.home() / ".local" / "share"


def applications_dir():
    return _xdg_data_home() / "applications"


def _desktop_target(entry):
    """Return explicit/Exec main.py targets from one desktop entry."""
    try:
        text = Path(entry).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    targets = []
    exec_line = None
    in_desktop_entry = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            in_desktop_entry = line == "[Desktop Entry]"
            continue
        if not in_desktop_entry or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"')
        if key in {"X-Suite-Pythoine-PortableMain", "X-LinSpectacles-SourceMain"}:
            targets.append(value)
        elif key == "Exec":
            exec_line = value

    if exec_line:
        try:
            parts = shlex.split(exec_line)
        except ValueError:
            parts = []
        for part in parts:
            if part.startswith("%"):
                continue
            candidate = part.strip().strip('"')
            if candidate.endswith("main.py"):
                targets.append(candidate)
    return targets


def matching_source_launchers(program_root):
    target = (Path(program_root).resolve() / "main.py").resolve()
    directory = applications_dir()
    try:
        entries = list(directory.glob("*.desktop"))
    except OSError:
        return []

    matches = []
    for entry in entries:
        for candidate_text in _desktop_target(entry):
            try:
                if Path(candidate_text).expanduser().resolve() == target:
                    matches.append(entry)
                    break
            except (OSError, RuntimeError):
                continue
    return matches


def desktop_entry_targets_program(program_root):
    return bool(matching_source_launchers(program_root))



def _desktop_exec_quote(value):
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def source_launcher_path():
    return applications_dir() / "linspectacles-hub.desktop"


def install_source_launcher(program_root):
    """Create/replace LinSpectacles' own user desktop launcher for this source tree."""
    program_root = Path(program_root).resolve()
    main_path = program_root / "main.py"
    icon_path = program_root / "assets" / "linspectacles-icon.png"
    target = source_launcher_path()
    target.parent.mkdir(parents=True, exist_ok=True)

    python_exec = Path(sys.executable).resolve()
    desktop = "\n".join([
        "[Desktop Entry]",
        "Type=Application",
        "Name=LinSpectacles Hub",
        "GenericName=Linux Inspection Suite",
        "Comment=Inspect Linux system state with modular standalone utilities",
        f"Exec={_desktop_exec_quote(python_exec)} {_desktop_exec_quote(main_path)}",
        f"Icon={str(icon_path)}",
        "Terminal=false",
        "Categories=System;",
        "Keywords=Linux;System;Inspection;Diagnostics;",
        "StartupNotify=true",
        f"X-LinSpectacles-SourceMain={str(main_path)}",
        "",
    ])
    tmp = target.with_suffix(".desktop.tmp")
    tmp.write_text(desktop, encoding="utf-8")
    try:
        os.chmod(tmp, 0o644)
    except OSError:
        pass
    os.replace(tmp, target)
    return target


def remove_source_launchers(program_root):
    """Remove user desktop entries that explicitly launch this exact source tree.

    Returns [(path, previous_text)] so callers can restore them if a later
    migration step fails.
    """
    removed = []
    for entry in matching_source_launchers(program_root):
        try:
            text = entry.read_text(encoding="utf-8", errors="replace")
            entry.unlink()
            removed.append((entry, text))
        except OSError as exc:
            raise OSError(f"Could not remove desktop launcher {entry}: {exc}") from exc
    return removed


def restore_source_launchers(removed):
    for path, text in removed:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
