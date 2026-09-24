#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# LinSpectacles - Linux Inspection Suite
# Copyright (C) 2026 brunonlinespace
# GPL-3.0-or-later

"""Generic Hub Module discovery, loading and host-service context.

Hub Modules are deliberately different from applets.  Applets are standalone
inspectors and must not depend on LinSpectacles.  Hub Modules enhance the host
itself and therefore use this small, versioned API.

Discovery is manifest-only: module Python code is imported only when a module
is enabled by the user/host configuration.
"""

import importlib.util
import json
import re
import shutil
import sys
import types
import zipfile
from dataclasses import dataclass
from pathlib import Path

MODULE_SCHEMA = 1
MODULE_API_VERSION = 5
SUPPORTED_MODULE_APIS = {1, 2, 3, 4, 5}
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


@dataclass(frozen=True)
class SuiteModuleManifest:
    module_id: str
    name: str
    version: str
    author: str
    editor: str
    directory: Path
    entrypoint: str
    factory: str
    description: str
    enabled_by_default: bool
    module_api: int
    source: str
    removable: bool


class EventBus:
    """Small in-process event bus exposed to enabled Hub Modules."""

    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_name, callback):
        if not isinstance(event_name, str) or not event_name:
            raise ValueError("event_name must be a non-empty string")
        if not callable(callback):
            raise TypeError("callback must be callable")
        token = (event_name, callback)
        self._subscribers.setdefault(event_name, []).append(callback)
        return token

    def unsubscribe(self, token):
        try:
            event_name, callback = token
        except Exception:
            return
        callbacks = self._subscribers.get(event_name, [])
        try:
            callbacks.remove(callback)
        except ValueError:
            return
        if not callbacks:
            self._subscribers.pop(event_name, None)

    def emit(self, event_name, **payload):
        for callback in tuple(self._subscribers.get(event_name, ())):
            try:
                callback(**payload)
            except Exception:
                # One optional module must never prevent the Suite from
                # notifying the remaining subscribers.
                continue


class ModuleContext:
    """Versioned, deliberately narrow host-services API for one Hub Module.

    The context never exposes the QMainWindow or its private widgets.  Modules
    may contribute actions/cards through generic services, inspect applet state,
    subscribe to Suite events, keep namespaced portable data and post status
    text.  Cleanup is automatic when the module is disabled or removed.
    """

    api_version = MODULE_API_VERSION

    def __init__(
        self,
        module_id,
        program_root,
        event_bus,
        add_menu_action,
        remove_menu_action,
        add_dashboard_widget,
        remove_dashboard_widget,
        applet_states,
        applet_metadata,
        current_applet_id,
        set_status,
        add_configuration_page=None,
        remove_configuration_page=None,
        open_configuration_page=None,
        add_suite_state_item=None,
        remove_suite_state_item=None,
        add_coverage_annotation=None,
        remove_coverage_annotation=None,
        add_coverage_column=None,
        remove_coverage_column=None,
        module_states=None,
        activate_applet=None,
        set_navigation_provider=None,
        remove_navigation_provider=None,
        refresh_navigation=None,
        storage_root=None,
    ):
        self.module_id = str(module_id)
        self.program_root = Path(program_root).resolve()
        self._storage_root = (
            Path(storage_root).expanduser()
            if storage_root is not None
            else self.program_root / "config" / "modules"
        )
        self._event_bus = event_bus
        self._add_menu_action_cb = add_menu_action
        self._remove_menu_action_cb = remove_menu_action
        self._add_dashboard_widget_cb = add_dashboard_widget
        self._remove_dashboard_widget_cb = remove_dashboard_widget
        self._applet_states_cb = applet_states
        self._applet_metadata_cb = applet_metadata
        self._current_applet_id_cb = current_applet_id
        self._set_status_cb = set_status
        self._add_configuration_page_cb = add_configuration_page
        self._remove_configuration_page_cb = remove_configuration_page
        self._open_configuration_page_cb = open_configuration_page
        self._add_suite_state_item_cb = add_suite_state_item
        self._remove_suite_state_item_cb = remove_suite_state_item
        self._add_coverage_annotation_cb = add_coverage_annotation
        self._remove_coverage_annotation_cb = remove_coverage_annotation
        self._add_coverage_column_cb = add_coverage_column
        self._remove_coverage_column_cb = remove_coverage_column
        self._module_states_cb = module_states
        self._activate_applet_cb = activate_applet
        self._set_navigation_provider_cb = set_navigation_provider
        self._remove_navigation_provider_cb = remove_navigation_provider
        self._refresh_navigation_cb = refresh_navigation
        self._navigation_handles = []
        self._menu_handles = []
        self._dashboard_handles = []
        self._configuration_handles = []
        self._suite_state_handles = []
        self._coverage_handles = []
        self._coverage_column_handles = []
        self._event_tokens = []

    @property
    def storage_dir(self):
        path = self._storage_root / self.module_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def add_menu_action(self, menu, text, callback, shortcut=None):
        """Add an action to a documented host menu section.

        ``menu`` is currently ``"help"`` or ``"tools"``.  The host owns
        placement and cleanup; the module owns only its label/callback.
        """
        if menu not in {"help", "tools"}:
            raise ValueError("menu must be 'help' or 'tools'")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("menu action text must be non-empty")
        if not callable(callback):
            raise TypeError("menu action callback must be callable")
        handle = self._add_menu_action_cb(
            self.module_id, menu, text.strip(), callback, shortcut
        )
        self._menu_handles.append(handle)
        return handle

    def add_dashboard_widget(self, widget, stretch=0):
        """Contribute a host-owned Dashboard widget/card."""
        handle = self._add_dashboard_widget_cb(
            self.module_id, widget, max(0, int(stretch or 0))
        )
        self._dashboard_handles.append(handle)
        return handle


    def add_configuration_page(self, page_id, label, factory):
        """Register a Configuration tab factory (Module API v3)."""
        if self._add_configuration_page_cb is None:
            raise RuntimeError("This LinSpectacles host does not support Configuration page contributions.")
        page_id = str(page_id or "").strip()
        label = str(label or "").strip()
        if not page_id or not label:
            raise ValueError("page_id and label must be non-empty")
        if not callable(factory):
            raise TypeError("factory must be callable")
        handle = self._add_configuration_page_cb(self.module_id, page_id, label, factory)
        self._configuration_handles.append(handle)
        return handle

    def open_configuration_page(self, page_id):
        """Open Configuration focused on a contributed page (Module API v3)."""
        if self._open_configuration_page_cb is None:
            raise RuntimeError("This LinSpectacles host does not support Configuration page navigation.")
        return self._open_configuration_page_cb(self.module_id, str(page_id))

    def add_suite_state_item(self, label, provider):
        """Contribute a compact Hub State line (Module API v3)."""
        if self._add_suite_state_item_cb is None:
            raise RuntimeError("This LinSpectacles host does not support Hub State contributions.")
        if not isinstance(label, str) or not label.strip():
            raise ValueError("label must be non-empty")
        if not callable(provider):
            raise TypeError("provider must be callable")
        handle = self._add_suite_state_item_cb(self.module_id, label.strip(), provider)
        self._suite_state_handles.append(handle)
        return handle

    def add_coverage_annotation(self, provider):
        """Contribute text to Inspection Coverage Summary cells (Module API v3)."""
        if self._add_coverage_annotation_cb is None:
            raise RuntimeError("This LinSpectacles host does not support coverage annotations.")
        if not callable(provider):
            raise TypeError("provider must be callable")
        handle = self._add_coverage_annotation_cb(self.module_id, provider)
        self._coverage_handles.append(handle)
        return handle

    def add_coverage_column(self, label, provider):
        """Contribute a named Inspection Coverage column (Module API v4).

        The provider receives the same host-known applet record used by
        ``add_coverage_annotation`` and returns the cell text.  The host owns
        the column and its ordering; modules never receive the table widget.
        """
        if self._add_coverage_column_cb is None:
            raise RuntimeError("This LinSpectacles host does not support coverage columns.")
        label = str(label or "").strip()
        if not label:
            raise ValueError("coverage column label must be non-empty")
        if not callable(provider):
            raise TypeError("provider must be callable")
        handle = self._add_coverage_column_cb(self.module_id, label, provider)
        self._coverage_column_handles.append(handle)
        return handle

    def get_applet_states(self):
        """Return host-known applet state without triggering applet scans."""
        return list(self._applet_states_cb())

    def get_applet_metadata(self):
        """Return manifest-derived applet metadata without importing applet code.

        Module API v2 adds this read-only capability so Hub Modules can
        inspect declarative applet capabilities (for example optional helper
        contracts) without crawling the applet store or triggering applet
        loading/scans. Each record includes ordinary identity/state fields,
        the resolved applet directory, and a JSON-compatible copy of the
        applet manifest.
        """
        return list(self._applet_metadata_cb())

    def current_applet_id(self):
        value = self._current_applet_id_cb()
        return None if value is None else str(value)

    def set_status(self, text):
        self._set_status_cb(str(text))

    def subscribe(self, event_name, callback):
        token = self._event_bus.subscribe(event_name, callback)
        self._event_tokens.append(token)
        return token

    def get_module_states(self):
        """Return installed Hub Module identity/state without importing disabled modules (API v5)."""
        if self._module_states_cb is None:
            raise RuntimeError("This LinSpectacles host does not expose Hub Module state.")
        return list(self._module_states_cb())

    def activate_applet(self, applet_id):
        """Request activation of an installed/enabled applet by ID (API v5)."""
        if self._activate_applet_cb is None:
            raise RuntimeError("This LinSpectacles host does not support applet activation.")
        return bool(self._activate_applet_cb(str(applet_id)))

    def set_navigation_provider(self, provider):
        """Register this module as the optional applet-navigation organizer (API v5)."""
        if self._set_navigation_provider_cb is None:
            raise RuntimeError("This LinSpectacles host does not support navigation organizers.")
        handle = self._set_navigation_provider_cb(self.module_id, provider)
        self._navigation_handles.append(handle)
        return handle

    def refresh_navigation(self):
        """Ask the host to rebuild its navigation from the active organizer model (API v5)."""
        if self._refresh_navigation_cb is not None:
            self._refresh_navigation_cb(self.module_id)

    def cleanup(self):
        """Remove every contribution registered through this context."""
        for handle in reversed(self._navigation_handles):
            try:
                if self._remove_navigation_provider_cb is not None:
                    self._remove_navigation_provider_cb(handle)
            except Exception:
                pass
        self._navigation_handles.clear()

        for token in reversed(self._event_tokens):
            self._event_bus.unsubscribe(token)
        self._event_tokens.clear()

        for handle in reversed(self._coverage_column_handles):
            try:
                if self._remove_coverage_column_cb is not None:
                    self._remove_coverage_column_cb(handle)
            except Exception:
                pass
        self._coverage_column_handles.clear()

        for handle in reversed(self._coverage_handles):
            try:
                if self._remove_coverage_annotation_cb is not None:
                    self._remove_coverage_annotation_cb(handle)
            except Exception:
                pass
        self._coverage_handles.clear()

        for handle in reversed(self._suite_state_handles):
            try:
                if self._remove_suite_state_item_cb is not None:
                    self._remove_suite_state_item_cb(handle)
            except Exception:
                pass
        self._suite_state_handles.clear()

        for handle in reversed(self._configuration_handles):
            try:
                if self._remove_configuration_page_cb is not None:
                    self._remove_configuration_page_cb(handle)
            except Exception:
                pass
        self._configuration_handles.clear()

        for handle in reversed(self._dashboard_handles):
            try:
                self._remove_dashboard_widget_cb(handle)
            except Exception:
                pass
        self._dashboard_handles.clear()

        for handle in reversed(self._menu_handles):
            try:
                self._remove_menu_action_cb(handle)
            except Exception:
                pass
        self._menu_handles.clear()


class ModuleRegistry:
    """Manifest-only discovery and isolated loading for Hub Modules."""

    def __init__(self, program_root, store=None, system_store=None):
        self.program_root = Path(program_root).resolve()
        self.store = (Path(store).expanduser() if store is not None else self.program_root / "modules")
        self.store.mkdir(parents=True, exist_ok=True)
        self.system_store = (
            Path(system_store).expanduser()
            if system_store is not None
            else None
        )
        self.manifests = {}
        self.instances = {}
        self._package_names = {}

    def _discovery_stores(self):
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

    @staticmethod
    def _relative_file(directory, value, default):
        text = str(value or default)
        rel = Path(text)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("unsafe relative path")
        path = directory / rel
        return text, path

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
                manifest_path = directory / "module.json"
                try:
                    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
                except (FileNotFoundError, json.JSONDecodeError, OSError):
                    continue
                try:
                    if raw.get("schema") != MODULE_SCHEMA:
                        continue
                    module_api = int(raw.get("module_api", 0))
                    if module_api not in SUPPORTED_MODULE_APIS:
                        continue
                    module_id = str(raw["id"])
                    if not SAFE_ID.match(module_id):
                        continue
                    entrypoint, entry_path = self._relative_file(
                        directory, raw.get("entrypoint"), "module.py"
                    )
                    if not entry_path.is_file() or not self._inside(directory, entry_path):
                        continue
                    factory = str(raw.get("factory", "create_module"))
                    if not factory or not factory.isidentifier():
                        continue
                    enabled_by_default = raw.get("enabled_by_default", False)
                    if not isinstance(enabled_by_default, bool):
                        continue
                    manifest = SuiteModuleManifest(
                        module_id=module_id,
                        name=str(raw["name"]),
                        version=str(raw.get("version", "0")),
                        author=str(raw.get("author", "")),
                        editor=str(raw.get("editor", raw.get("author", ""))),
                        directory=directory.resolve(),
                        entrypoint=entrypoint,
                        factory=factory,
                        description=str(raw.get("description", "")),
                        enabled_by_default=enabled_by_default,
                        module_api=module_api,
                        source=source,
                        removable=removable,
                    )
                except (KeyError, TypeError, ValueError):
                    continue
                if module_id not in found:
                    found[module_id] = manifest

        # Loaded instances are intentionally not discarded here. The host owns
        # lifecycle teardown so it can call deactivate() and clean registered
        # contributions before unloading Python modules. It also handles a
        # source change for the same ID (user override versus system package).
        self.manifests = found
        return found

    def ordered(self, order=None):
        manifests = list(self.manifests.values())
        if not order:
            return sorted(manifests, key=lambda m: m.name.lower())
        wanted = [str(item) for item in order]
        rank = {module_id: index for index, module_id in enumerate(wanted)}
        return sorted(
            manifests,
            key=lambda m: (rank.get(m.module_id, len(rank)), m.name.lower()),
        )

    def _load_entry_module(self, manifest):
        package_name = "linspectacles_suite_module_" + re.sub(
            r"[^a-zA-Z0-9_]", "_", manifest.module_id
        )
        self._package_names[manifest.module_id] = package_name

        # Create/load the package root so module entrypoints can use relative
        # imports without requiring the package __init__ to re-export factory.
        init_path = manifest.directory / "__init__.py"
        if init_path.is_file():
            spec = importlib.util.spec_from_file_location(
                package_name,
                init_path,
                submodule_search_locations=[str(manifest.directory)],
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not create package loader for {manifest.name}")
            package = importlib.util.module_from_spec(spec)
            sys.modules[package_name] = package
            try:
                spec.loader.exec_module(package)
            except Exception:
                self._purge_package(package_name)
                raise
        else:
            package = types.ModuleType(package_name)
            package.__path__ = [str(manifest.directory)]
            package.__package__ = package_name
            sys.modules[package_name] = package

        entry_path = manifest.directory / manifest.entrypoint
        entry_name = package_name + "._entrypoint"
        spec = importlib.util.spec_from_file_location(entry_name, entry_path)
        if spec is None or spec.loader is None:
            self._purge_package(package_name)
            raise ImportError(f"Could not create entrypoint loader for {manifest.name}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[entry_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            self._purge_package(package_name)
            raise
        return module

    @staticmethod
    def _purge_package(package_name):
        for name in list(sys.modules):
            if name == package_name or name.startswith(package_name + "."):
                sys.modules.pop(name, None)

    def load_instance(self, manifest, context):
        if manifest.module_api not in SUPPORTED_MODULE_APIS:
            supported = ", ".join(str(v) for v in sorted(SUPPORTED_MODULE_APIS))
            raise RuntimeError(
                f"{manifest.name} requires Module API {manifest.module_api}; "
                f"this LinSpectacles supports API {supported}."
            )
        if manifest.module_id in self.instances:
            return self.instances[manifest.module_id]

        module = self._load_entry_module(manifest)
        factory = getattr(module, manifest.factory, None)
        if not callable(factory):
            self.unload(manifest.module_id)
            raise AttributeError(
                f"Hub Module {manifest.name} does not export {manifest.factory}()"
            )
        instance = factory(context=context)
        if instance is None:
            self.unload(manifest.module_id)
            raise TypeError(f"Hub Module {manifest.name} factory returned None")
        self.instances[manifest.module_id] = instance
        return instance

    def unload(self, module_id):
        self.instances.pop(module_id, None)
        package_name = self._package_names.pop(module_id, None)
        if package_name:
            self._purge_package(package_name)

    def validate_zip(self, zip_path):
        zip_path = Path(zip_path)
        with zipfile.ZipFile(zip_path, "r") as archive:
            file_names = [name for name in archive.namelist() if name and not name.endswith("/")]
            paths = [Path(name) for name in file_names]
            if not paths:
                raise ValueError("Hub Module archive is empty.")
            roots = {p.parts[0] for p in paths if p.parts}
            if len(roots) != 1:
                raise ValueError("Hub Module archive must contain one top-level module folder.")
            root = next(iter(roots))
            for path in paths:
                if path.is_absolute() or ".." in path.parts:
                    raise ValueError("Hub Module archive contains an unsafe path.")

            manifest_name = f"{root}/module.json"
            if manifest_name not in file_names:
                raise ValueError("Hub Module archive has no module.json manifest.")
            try:
                raw = json.loads(archive.read(manifest_name).decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise ValueError(f"Hub Module manifest is invalid: {exc}") from exc

            module_id = str(raw.get("id", ""))
            if raw.get("schema") != MODULE_SCHEMA or not SAFE_ID.match(module_id):
                raise ValueError("Hub Module manifest is invalid or unsupported.")
            if int(raw.get("module_api", 0)) not in SUPPORTED_MODULE_APIS:
                raise ValueError(
                    f"Hub Module requires unsupported Module API {raw.get('module_api')!r}."
                )
            entrypoint = Path(str(raw.get("entrypoint", "module.py")))
            if entrypoint.is_absolute() or ".." in entrypoint.parts:
                raise ValueError("Hub Module entrypoint is unsafe.")
            entry_name = str(Path(root) / entrypoint)
            if entry_name not in file_names:
                raise ValueError("Hub Module archive does not contain its declared entrypoint.")
            factory = str(raw.get("factory", "create_module"))
            if not factory or not factory.isidentifier():
                raise ValueError("Hub Module factory name is invalid.")
            if not isinstance(raw.get("enabled_by_default", False), bool):
                raise ValueError("enabled_by_default must be true or false.")
            return root, module_id

    def install_zip(self, zip_path):
        root, module_id = self.validate_zip(zip_path)
        destination = self.store / root
        if destination.exists():
            raise FileExistsError(f"Hub Module folder already exists: {destination.name}")
        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(self.store)
        self.discover()
        if module_id not in self.manifests:
            shutil.rmtree(destination, ignore_errors=True)
            raise ValueError("Installed files did not produce a valid Hub Module.")
        return self.manifests[module_id]

    def remove(self, module_id):
        manifest = self.manifests.get(module_id)
        if manifest is None:
            return False
        if not manifest.removable:
            raise ValueError(
                "System-installed Hub Modules are managed by the package manager and cannot be removed from LinSpectacles."
            )
        if not self._inside(self.store, manifest.directory):
            raise ValueError("Refusing to remove a Hub Module outside the writable module store.")
        shutil.rmtree(manifest.directory)
        self.discover()
        return True
