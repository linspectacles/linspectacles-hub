#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# LinSpectacles - Linux Inspection Suite
# Copyright (C) 2026 brunonlinespace
# GPL-3.0-or-later

import json
import sys
from pathlib import Path

from PyQt6.QtCore import QEvent, QProcess, QSize, Qt, QUrl
from PyQt6.QtGui import QAction, QColor, QDesktopServices, QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QDialog, QDialogButtonBox,
    QFileDialog, QFontDialog, QFrame, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMenu, QScrollArea,
    QStyle, QStyledItemDelegate, QStyleOptionViewItem, QMessageBox, QPushButton,
    QRadioButton, QStackedWidget, QTableWidget, QTableWidgetItem, QTabWidget,
    QVBoxLayout, QWidget,
)

from .modules import ModuleContext
from .ui.common import DASHBOARD_ID, NAV_LOGICAL_ROLE

class ModuleHost:
    def _add_module_contextual_action(self, module_id, action_id, text, callback, shortcut=None):
        if not callable(callback):
            raise TypeError("contextual action callback must be callable")
        action = QAction(str(text), self)
        if shortcut:
            action.setShortcut(str(shortcut))
        action.triggered.connect(lambda _checked=False, cb=callback: cb())
        action.setProperty("linspectaclesModuleId", str(module_id))
        action.setProperty("linspectaclesContextActionId", str(action_id))
        self.addAction(action)

        button = QPushButton(str(text))
        button.setProperty("linspectaclesModuleId", str(module_id))
        button.setProperty("linspectaclesContextActionId", str(action_id))
        button.clicked.connect(action.trigger)
        button.setVisible(False)
        self.contextual_action_layout.addWidget(button)

        handle = (action, button)
        self.module_contextual_actions.append(handle)
        self._update_contextual_action_controls(self._active_applet_id())
        return handle

    def _remove_module_contextual_action(self, handle):
        try:
            action, button = handle
        except Exception:
            return
        if handle in self.module_contextual_actions:
            self.module_contextual_actions.remove(handle)
        try:
            self.removeAction(action)
        except Exception:
            pass
        try:
            self.contextual_action_layout.removeWidget(button)
            button.setParent(None)
            button.deleteLater()
        except Exception:
            pass
        try:
            action.deleteLater()
        except Exception:
            pass
        self._update_contextual_action_controls(self._active_applet_id())

    def _update_contextual_action_controls(self, applet_id=None):
        visible = bool(applet_id and applet_id in self.manifest_by_id)
        any_visible = False
        for _action, button in list(self.module_contextual_actions):
            button.setVisible(visible)
            any_visible = any_visible or visible
        if hasattr(self, "contextual_action_container"):
            self.contextual_action_container.setVisible(any_visible)

    def _add_module_menu_action(self, module_id, menu_id, text, callback, shortcut=None):
        """Compatibility bridge for pre-0.2.0 menu contributions.

        Visible Help/Tools menus were removed in 0.2.0.  The historical
        Encyclopedia ``What's This?`` contribution is promoted to the new
        contextual sidebar surface so current modules continue to work.
        Other legacy menu actions remain shortcut-capable but have no visible
        menu placement.
        """
        menu_id = str(menu_id or "").strip().lower()
        text = str(text or "").strip()
        if menu_id == "help" and (text.casefold().startswith("what's this") or str(shortcut or "").casefold() == "shift+f1"):
            return self._add_module_contextual_action(
                module_id, "legacy-whats-this", "What's This?", callback, shortcut or "Shift+F1"
            )
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(str(shortcut))
            self.addAction(action)
        action.triggered.connect(lambda _checked=False, cb=callback: cb())
        action.setProperty("linspectaclesModuleId", str(module_id))
        action.setProperty("linspectaclesLegacyMenu", menu_id)
        return action

    def _remove_module_menu_action(self, handle):
        if handle is None:
            return
        if isinstance(handle, tuple):
            self._remove_module_contextual_action(handle)
            return
        try:
            self.removeAction(handle)
        except Exception:
            pass
        handle.deleteLater()

    def _resolved_module_enablement(self, manifests=None):
        manifests = list(
            manifests if manifests is not None
            else self.module_registry.ordered(self.config.module_order)
        )
        return self.config.resolve_module_enablement(manifests)

    def _module_rank(self, module_id):
        order = self.config.module_order
        try:
            return order.index(str(module_id))
        except ValueError:
            return len(order)

    def _ordered_module_contributions(self, contributions):
        return sorted(
            list(contributions),
            key=lambda item: self._module_rank(item[0] if isinstance(item, tuple) else ""),
        )

    def _module_dashboard_visible(self, module_id):
        return self.config.module_dashboard_visible(str(module_id), True)

    def _ordered_dashboard_contributions(self, contributions):
        return [
            item
            for item in self._ordered_module_contributions(contributions)
            if isinstance(item, tuple)
            and item
            and self._module_dashboard_visible(item[0])
        ]

    def _reorder_module_dashboard_widgets(self):
        widgets = []
        for index in range(self.dashboard_module_layout.count()):
            widget = self.dashboard_module_layout.itemAt(index).widget()
            if widget is not None:
                widgets.append(widget)
        widgets.sort(key=lambda w: self._module_rank(w.property("linspectaclesModuleId") or ""))
        visible_widgets = 0
        for widget in widgets:
            self.dashboard_module_layout.removeWidget(widget)
        for widget in widgets:
            module_id = str(widget.property("linspectaclesModuleId") or "")
            visible = self._module_dashboard_visible(module_id)
            widget.setVisible(visible)
            if visible:
                visible_widgets += 1
            self.dashboard_module_layout.addWidget(
                widget, int(widget.property("linspectaclesModuleStretch") or 0)
            )
        self.dashboard_module_container.setVisible(bool(visible_widgets))

    def _add_module_dashboard_widget(self, module_id, widget, stretch=0):
        if widget is None:
            raise ValueError("Dashboard contribution cannot be None")
        widget.setProperty("linspectaclesModuleId", str(module_id))
        widget.setProperty("linspectaclesModuleStretch", int(stretch))
        self.dashboard_module_layout.addWidget(widget, int(stretch))
        self._reorder_module_dashboard_widgets()
        return widget

    def _remove_module_dashboard_widget(self, widget):
        if widget is None:
            return
        self.dashboard_module_layout.removeWidget(widget)
        widget.setParent(None)
        widget.deleteLater()
        self._reorder_module_dashboard_widgets()

    def _add_module_configuration_page(self, module_id, page_id, label, factory):
        handle = (str(module_id), str(page_id), str(label), factory)
        self.module_configuration_pages.append(handle)
        return handle

    def _remove_module_configuration_page(self, handle):
        try:
            self.module_configuration_pages.remove(handle)
        except ValueError:
            pass

    def _open_module_configuration_page(self, module_id, page_id):
        self.open_configuration((str(module_id), str(page_id)))

    def _add_module_applets_extension(self, module_id, extension_id, label, factory):
        handle = (str(module_id), str(extension_id), str(label), factory)
        self.module_applets_extensions.append(handle)
        return handle

    def _remove_module_applets_extension(self, handle):
        try:
            self.module_applets_extensions.remove(handle)
        except ValueError:
            pass

    def _add_module_applets_column(
        self, module_id, column_id, label, kind, value_provider,
        changed_callback, editable,
    ):
        handle = (
            str(module_id), str(column_id), str(label), str(kind), value_provider,
            changed_callback, editable,
        )
        self.module_applets_columns.append(handle)
        return handle

    def _remove_module_applets_column(self, handle):
        try:
            self.module_applets_columns.remove(handle)
        except ValueError:
            pass

    def _add_module_applets_action(self, module_id, action_id, label, callback):
        handle = (str(module_id), str(action_id), str(label), callback)
        self.module_applets_actions.append(handle)
        return handle

    def _remove_module_applets_action(self, handle):
        try:
            self.module_applets_actions.remove(handle)
        except ValueError:
            pass

    def _add_module_suite_state_item(self, module_id, label, provider):
        handle = (str(module_id), str(label), provider)
        self.module_suite_state_items.append(handle)
        self.update_dashboard()
        return handle

    def _remove_module_suite_state_item(self, handle):
        try:
            self.module_suite_state_items.remove(handle)
        except ValueError:
            pass
        self.update_dashboard()

    def _add_module_coverage_annotation(self, module_id, provider):
        handle = (str(module_id), provider)
        self.module_coverage_annotations.append(handle)
        self.update_dashboard()
        return handle

    def _remove_module_coverage_annotation(self, handle):
        try:
            self.module_coverage_annotations.remove(handle)
        except ValueError:
            pass
        self.update_dashboard()

    def _add_module_coverage_column(self, module_id, label, provider):
        handle = (str(module_id), str(label), provider)
        self.module_coverage_columns.append(handle)
        self.update_dashboard()
        return handle

    def _remove_module_coverage_column(self, handle):
        try:
            self.module_coverage_columns.remove(handle)
        except ValueError:
            pass
        self.update_dashboard()

    def _module_applet_states(self):
        return [
            {
                "id": manifest.applet_id,
                "instance_id": manifest.instance_id,
                "name": manifest.name,
                "version": manifest.version,
                "enabled": self.config.applet_enabled(manifest.instance_id, manifest.applet_id),
                "loaded": manifest.instance_id in self.pages,
                "source": manifest.source,
                "origin": manifest.origin,
                "removable": manifest.removable,
            }
            for manifest in self.registry.ordered()
        ]

    def _module_applet_metadata(self):
        """Return declarative applet metadata without importing applet code.

        This is the generic Module API v2 bridge for modules that need to
        reason about applet-declared capabilities. Reading applet.json is
        intentionally side-effect free and does not load or scan an applet.
        """
        records = []
        for manifest in self.registry.ordered():
            raw = {}
            try:
                manifest_path = manifest.directory / "applet.json"
                loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    raw = loaded
            except (OSError, ValueError, TypeError):
                raw = {}
            records.append(
                {
                    "id": manifest.applet_id,
                    "instance_id": manifest.instance_id,
                    "name": manifest.name,
                    "version": manifest.version,
                    "author": manifest.author,
                    "editor": manifest.editor,
                    "description": manifest.description,
                    "enabled": self.config.applet_enabled(manifest.instance_id, manifest.applet_id),
                    "loaded": manifest.instance_id in self.pages,
                    "directory": str(manifest.directory),
                    "source": manifest.source,
                    "removable": manifest.removable,
                    "manifest": raw,
                }
            )
        return records

    def _module_current_applet_id(self):
        instance_id = self.current_id()
        if instance_id in (None, DASHBOARD_ID):
            return None
        manifest = self.manifest_by_id.get(instance_id)
        return manifest.applet_id if manifest is not None else None

    def _module_set_status(self, text):
        self.status_lbl.setText(f"Status: {text}")

    def _create_module_context(self, module_id):
        return ModuleContext(
            module_id=module_id,
            program_root=self.program_root,
            event_bus=self.module_events,
            add_menu_action=self._add_module_menu_action,
            remove_menu_action=self._remove_module_menu_action,
            add_dashboard_widget=self._add_module_dashboard_widget,
            add_contextual_action=self._add_module_contextual_action,
            remove_contextual_action=self._remove_module_contextual_action,
            remove_dashboard_widget=self._remove_module_dashboard_widget,
            applet_states=self._module_applet_states,
            applet_metadata=self._module_applet_metadata,
            current_applet_id=self._module_current_applet_id,
            set_status=self._module_set_status,
            add_configuration_page=self._add_module_configuration_page,
            remove_configuration_page=self._remove_module_configuration_page,
            open_configuration_page=self._open_module_configuration_page,
            add_applets_extension=self._add_module_applets_extension,
            remove_applets_extension=self._remove_module_applets_extension,
            add_applets_column=self._add_module_applets_column,
            remove_applets_column=self._remove_module_applets_column,
            add_applets_action=self._add_module_applets_action,
            remove_applets_action=self._remove_module_applets_action,
            add_suite_state_item=self._add_module_suite_state_item,
            remove_suite_state_item=self._remove_module_suite_state_item,
            add_coverage_annotation=self._add_module_coverage_annotation,
            remove_coverage_annotation=self._remove_module_coverage_annotation,
            add_coverage_column=self._add_module_coverage_column,
            remove_coverage_column=self._remove_module_coverage_column,
            module_states=self._module_module_states,
            activate_applet=self._module_activate_applet,
            set_navigation_provider=self._set_navigation_provider,
            remove_navigation_provider=self._remove_navigation_provider,
            refresh_navigation=self._refresh_navigation,
            storage_root=self.runtime_paths.module_storage_root,
        )

    def _module_module_states(self):
        self.module_registry.discover()
        manifests = self.module_registry.ordered(self.config.module_order)
        enabled_instances, _ambiguous = self._resolved_module_enablement(manifests)
        records = []
        for manifest in manifests:
            records.append({
                "id": manifest.module_id,
                "instance_id": manifest.instance_id,
                "name": manifest.name,
                "version": manifest.version,
                "enabled": manifest.instance_id in enabled_instances,
                "dashboard_visible": self.config.module_dashboard_visible(manifest.module_id, True),
                "source": manifest.source,
                "removable": manifest.removable,
            })
        return records

    def _module_activate_applet(self, applet_id):
        requested = str(applet_id)

        def matching_rows():
            rows = []
            for row in range(self.nav_list.count()):
                item = self.nav_list.item(row)
                instance_id = item.data(Qt.ItemDataRole.UserRole)
                logical_id = item.data(NAV_LOGICAL_ROLE)
                if instance_id == requested or logical_id == requested:
                    rows.append(row)
            return rows

        rows = matching_rows()
        if not rows and hasattr(self, "applet_search") and self.applet_search.text():
            self.applet_search.clear()
            rows = matching_rows()
        if len(rows) == 1:
            self.nav_list.setCurrentRow(rows[0])
            return True
        if len(rows) > 1:
            self.status_lbl.setText(
                "Status: Multiple copies of that applet are available; choose the User or Package-managed copy explicitly in the sidebar."
            )
        return False

    def _set_navigation_provider(self, module_id, provider):
        if self.navigation_provider is not None and self.navigation_provider_module_id != str(module_id):
            raise RuntimeError("Only one Hub Module may organize applet navigation at a time.")
        if not callable(provider):
            raise TypeError("navigation provider must be callable")
        self.navigation_provider_module_id = str(module_id)
        self.navigation_provider = provider
        self.rebuild_sidebar(select_id=self.current_id(), rediscover=False)
        return (str(module_id), provider)

    def _remove_navigation_provider(self, handle):
        try:
            module_id, provider = handle
        except Exception:
            return
        if self.navigation_provider_module_id == str(module_id) and self.navigation_provider is provider:
            self.navigation_provider = None
            self.navigation_provider_module_id = None
            self.rebuild_sidebar(select_id=self.current_id(), rediscover=False)

    def _refresh_navigation(self, module_id):
        if self.navigation_provider_module_id == str(module_id):
            self.rebuild_sidebar(select_id=self.current_id(), rediscover=False)

    def _deactivate_suite_module(self, instance_id):
        instance = self.active_modules.pop(instance_id, None)
        context = self.module_contexts.pop(instance_id, None)
        manifest = self.module_registry.manifests.get(instance_id)
        logical_id = manifest.module_id if manifest is not None else str(instance_id).split(":", 1)[-1]
        if instance is not None:
            handler = getattr(instance, "deactivate", None)
            if callable(handler):
                try:
                    handler()
                except Exception as exc:
                    self.status_lbl.setText(
                        f"Status: Hub Module cleanup warning ({logical_id}): {exc}"
                    )
        if context is not None:
            context.cleanup()
        self.module_registry.unload(instance_id)
        self.active_module_directories.pop(instance_id, None)
        self.module_events.emit(
            "module.deactivated", module_id=logical_id, instance_id=instance_id
        )

    def sync_suite_modules(self, show_errors=True):
        """Activate/deactivate the preferred implementation of each enabled logical module."""
        self.module_registry.discover()
        manifest_list = self.module_registry.ordered(self.config.module_order)
        manifests = {m.instance_id: m for m in manifest_list}
        desired, _ambiguous_modules = self._resolved_module_enablement(manifest_list)

        for instance_id in list(self.active_modules):
            manifest = manifests.get(instance_id)
            active_directory = self.active_module_directories.get(instance_id)
            if (
                instance_id not in desired
                or manifest is None
                or (active_directory is not None and active_directory != manifest.directory)
            ):
                self._deactivate_suite_module(instance_id)

        failures = []
        for manifest in manifest_list:
            instance_id = manifest.instance_id
            if instance_id not in desired or instance_id in self.active_modules:
                continue
            context = self._create_module_context(manifest.module_id)
            try:
                instance = self.module_registry.load_instance(manifest, context)
                handler = getattr(instance, "activate", None)
                if callable(handler):
                    handler()
            except Exception as exc:
                context.cleanup()
                self.module_registry.unload(instance_id)
                failures.append(f"{manifest.name} ({manifest.source}): {exc}")
                continue
            self.module_contexts[instance_id] = context
            self.active_modules[instance_id] = instance
            self.active_module_directories[instance_id] = manifest.directory
            self.module_events.emit(
                "module.activated",
                module_id=manifest.module_id,
                instance_id=instance_id,
                source=manifest.source,
                name=manifest.name,
            )

        self._reorder_module_dashboard_widgets()
        self.update_dashboard()
        self.module_events.emit(
            "modules.changed",
            modules=[
                {
                    "id": manifest.module_id,
                    "instance_id": manifest.instance_id,
                    "name": manifest.name,
                    "version": manifest.version,
                    "source": manifest.source,
                    "enabled": manifest.instance_id in desired,
                    "active": manifest.instance_id in self.active_modules,
                }
                for manifest in manifest_list
            ],
        )

        if failures:
            message = "Could not activate one or more Hub Modules:\n\n" + "\n".join(failures)
            self.status_lbl.setText("Status: One or more Hub Modules failed to activate.")
            if show_errors:
                QMessageBox.warning(self, "Hub Module", message)

