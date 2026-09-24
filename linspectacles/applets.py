#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2026 brunonlinespace
# GPL-3.0-or-later

import importlib.util
import json
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

APPLET_SCHEMA = 1
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
APPLET_ID_PREFIX = "linspectacles-"
REJECTED_APPLET_ID_PREFIXES = ("linspector-",)


def normalize_applet_id(value):
    """Return the stable logical applet ID for supported manifest ID forms.

    New applets may declare ``linspectacles-<applet-id>`` while legacy applets
    continue to declare ``<applet-id>``.  The mistaken r3 ``linspector-`` prefix
    is explicitly rejected.  The host deliberately normalizes
    both forms to the legacy logical ID so existing configuration, Module API
    consumers and navigation/catalogue state keep referring to one applet.
    """
    declared_id = str(value).strip()
    if not SAFE_ID.fullmatch(declared_id):
        raise ValueError("Applet ID is invalid or unsupported.")
    if declared_id.startswith(REJECTED_APPLET_ID_PREFIXES):
        raise ValueError("Applet ID uses the unsupported linspector- prefix; use linspectacles- or the legacy unprefixed ID.")
    if declared_id.startswith(APPLET_ID_PREFIX):
        logical_id = declared_id[len(APPLET_ID_PREFIX):]
        if not logical_id or not SAFE_ID.fullmatch(logical_id):
            raise ValueError("Prefixed applet ID has no valid applet identifier.")
        return logical_id
    return declared_id


@dataclass(frozen=True)
class AppletManifest:
    applet_id: str
    name: str
    version: str
    author: str
    editor: str
    order: int
    directory: Path
    entrypoint: str
    factory: str
    standalone: str
    description: str
    source: str
    removable: bool


class AppletRegistry:
    def __init__(self, program_root, store=None, system_store=None):
        self.program_root = Path(program_root).resolve()
        self.store = (Path(store).expanduser() if store is not None else self.program_root / "applets")
        self.store.mkdir(parents=True, exist_ok=True)
        self.system_store = (
            Path(system_store).expanduser()
            if system_store is not None
            else None
        )
        self.manifests = {}
        self.modules = {}

    def _discovery_stores(self):
        # The mutable user/portable store always has precedence. In packaged
        # mode an immutable system store is consulted only for IDs not already
        # supplied by the user store.
        primary_source = "User" if self.system_store is not None else "Portable"
        stores = [(self.store, primary_source, True)]
        if self.system_store is not None:
            try:
                same_store = self.system_store.resolve() == self.store.resolve()
            except OSError:
                same_store = False
            if not same_store:
                stores.append((self.system_store, "System (RPM)", False))
        return stores

    @staticmethod
    def _inside(base, candidate):
        try:
            candidate.resolve().relative_to(base.resolve())
            return True
        except ValueError:
            return False

    def discover(self):
        found = {}
        for store, source, removable in self._discovery_stores():
            if not store.is_dir():
                continue
            try:
                directories = sorted(store.iterdir(), key=lambda p: p.name.lower())
            except OSError:
                continue
            for directory in directories:
                if not directory.is_dir() or directory.is_symlink() or directory.name.startswith("_"):
                    continue
                manifest_path = directory / "applet.json"
                try:
                    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
                except (FileNotFoundError, json.JSONDecodeError, OSError):
                    continue
                try:
                    if raw.get("schema") != APPLET_SCHEMA:
                        continue
                    applet_id = normalize_applet_id(raw["id"])
                    entrypoint = str(raw.get("entrypoint", "applet.py"))
                    standalone = str(raw.get("standalone", "standalone.py"))
                    entry = directory / entrypoint
                    if not entry.is_file() or not self._inside(directory, entry):
                        continue
                    manifest = AppletManifest(
                        applet_id=applet_id,
                        name=str(raw["name"]),
                        version=str(raw.get("version", "0")),
                        author=str(raw.get("author", "")),
                        editor=str(raw.get("editor", raw.get("author", ""))),
                        order=int(raw.get("order", 1000)),
                        directory=directory.resolve(),
                        entrypoint=entrypoint,
                        factory=str(raw.get("factory", "create_applet")),
                        standalone=standalone,
                        description=str(raw.get("description", "")),
                        source=source,
                        removable=removable,
                    )
                except (KeyError, TypeError, ValueError):
                    continue
                if applet_id not in found:
                    found[applet_id] = manifest

        # If an applet ID changes source (for example a new user override
        # shadows a system RPM copy), do not retain the old imported package.
        previous = self.manifests
        for applet_id in list(self.modules):
            old = previous.get(applet_id)
            new = found.get(applet_id)
            if new is None or old is None or old.directory != new.directory:
                self.modules.pop(applet_id, None)
        self.manifests = found
        return found

    def ordered(self, preferred_order=None):
        preferred_order = preferred_order or []
        rank = {applet_id: index for index, applet_id in enumerate(preferred_order)}
        return sorted(
            self.manifests.values(),
            key=lambda m: (rank.get(m.applet_id, 100000 + m.order), m.order, m.name.lower()),
        )

    def load_widget(self, manifest, parent=None):
        module = self.modules.get(manifest.applet_id)
        if module is None:
            package_name = "linspectacles_applet_" + re.sub(r"[^a-zA-Z0-9_]", "_", manifest.applet_id)
            init_path = manifest.directory / "__init__.py"
            load_path = init_path if init_path.is_file() else manifest.directory / manifest.entrypoint
            spec = importlib.util.spec_from_file_location(
                package_name,
                load_path,
                submodule_search_locations=[str(manifest.directory)] if init_path.is_file() else None,
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not create loader for {manifest.name}")
            module = importlib.util.module_from_spec(spec)
            sys.modules[package_name] = module
            try:
                spec.loader.exec_module(module)
            except Exception:
                sys.modules.pop(package_name, None)
                raise
            self.modules[manifest.applet_id] = module
        factory = getattr(module, manifest.factory, None)
        if factory is None:
            raise AttributeError(f"Applet {manifest.name} does not export {manifest.factory}()")
        return factory(parent=parent)

    def validate_zip(self, zip_path):
        zip_path = Path(zip_path)
        with zipfile.ZipFile(zip_path, "r") as archive:
            names = [Path(name) for name in archive.namelist() if name and not name.endswith("/")]
            if not names:
                raise ValueError("Applet archive is empty.")
            roots = {p.parts[0] for p in names if p.parts}
            if len(roots) != 1:
                raise ValueError("Applet archive must contain one top-level applet folder.")
            root = next(iter(roots))
            for p in names:
                if p.is_absolute() or ".." in p.parts:
                    raise ValueError("Applet archive contains an unsafe path.")
            manifest_name = f"{root}/applet.json"
            if manifest_name not in archive.namelist():
                raise ValueError("Applet archive has no applet.json manifest.")
            raw = json.loads(archive.read(manifest_name).decode("utf-8"))
            if raw.get("schema") != APPLET_SCHEMA:
                raise ValueError("Applet manifest is invalid or unsupported.")
            try:
                applet_id = normalize_applet_id(raw.get("id", ""))
            except ValueError as exc:
                raise ValueError("Applet manifest is invalid or unsupported.") from exc
            return root, applet_id

    def install_zip(self, zip_path):
        root, applet_id = self.validate_zip(zip_path)
        destination = self.store / root
        if destination.exists():
            raise FileExistsError(f"Applet folder already exists: {destination.name}")
        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(self.store)
        self.discover()
        if applet_id not in self.manifests:
            shutil.rmtree(destination, ignore_errors=True)
            raise ValueError("Installed files did not produce a valid applet.")
        return self.manifests[applet_id]

    def remove(self, applet_id):
        manifest = self.manifests.get(applet_id)
        if manifest is None:
            return False
        if not manifest.removable:
            raise ValueError(
                "System-installed applets are managed by the package manager and cannot be removed from LinSpectacles."
            )
        if not self._inside(self.store, manifest.directory):
            raise ValueError("Refusing to remove an applet outside the writable applet store.")
        shutil.rmtree(manifest.directory)
        self.modules.pop(applet_id, None)
        self.discover()
        return True
