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

from .ui.common import DASHBOARD_ID

class AppletHost:
    def _update_launch_standalone_control(self, applet_id=None):
        if not hasattr(self, "launch_standalone_btn"):
            return
        visible = bool(applet_id and applet_id in self.manifest_by_id)
        self.launch_standalone_btn.setVisible(visible)
        self.launch_standalone_btn.setEnabled(visible)
        action = getattr(self, "launch_standalone_action", None)
        if action is not None:
            action.setEnabled(visible)
        updater = getattr(self, "_update_contextual_action_controls", None)
        if callable(updater):
            updater(applet_id if visible else None)

    def _active_applet_id(self):
        if not hasattr(self, "stack"):
            return None
        current_widget = self.stack.currentWidget()
        for applet_id, widget in self.pages.items():
            if applet_id != DASHBOARD_ID and widget is current_widget:
                return applet_id
        return None

    def launch_current_applet_standalone(self):
        applet_id = self._active_applet_id()
        if applet_id:
            self.launch_applet_standalone(applet_id)

    def launch_applet_standalone(self, applet_id):
        manifest = self.registry.manifests.get(str(applet_id))
        if manifest is None:
            QMessageBox.warning(self, "Launch Standalone", "This applet is no longer installed.")
            return
        launcher = (manifest.directory / manifest.standalone).resolve()
        try:
            launcher.relative_to(manifest.directory.resolve())
        except ValueError:
            QMessageBox.critical(self, "Launch Standalone", "The applet standalone launcher path is invalid.")
            return
        if not launcher.is_file():
            QMessageBox.critical(
                self,
                "Launch Standalone",
                f"Could not find the standalone launcher for {manifest.name}:\n{launcher}",
            )
            return
        try:
            started, _pid = QProcess.startDetached(
                sys.executable, [str(launcher)], str(manifest.directory)
            )
        except Exception as exc:
            QMessageBox.critical(
                self, "Launch Standalone", f"Could not launch {manifest.name}:\n{exc}"
            )
            return
        if not started:
            QMessageBox.critical(
                self, "Launch Standalone", f"Could not launch {manifest.name}."
            )
            return
        self.status_lbl.setText(f"Status: Launched standalone: {manifest.name}")

    def _show_applet_context_menu(self, position):
        item = self.nav_list.itemAt(position)
        if item is None:
            return
        applet_id = item.data(Qt.ItemDataRole.UserRole)
        if not applet_id or applet_id not in self.manifest_by_id:
            return
        menu = QMenu(self.nav_list)
        launch_action = menu.addAction("Launch Standalone...")
        chosen = menu.exec(self.nav_list.viewport().mapToGlobal(position))
        if chosen is launch_action:
            self.launch_applet_standalone(applet_id)

    def enabled_manifests(self):
        return [
            manifest
            for manifest in self.registry.ordered()
            if self.config.applet_enabled(manifest.instance_id, manifest.applet_id)
        ]

    def preferred_applet_manifests(self, manifests=None):
        manifests = list(self.enabled_manifests() if manifests is None else manifests)
        return self.config.resolve_applet_presentation(manifests)

    def _set_applet_active(self, widget, active):
        if widget is None:
            return
        handler = getattr(widget, "set_applet_active", None)
        if callable(handler):
            try:
                handler(bool(active))
            except Exception as exc:
                self.status_lbl.setText(f"Status: Applet lifecycle warning: {exc}")

    def _unload_disabled_or_removed(self):
        keep = set(self.manifest_by_id) | {DASHBOARD_ID}
        for applet_id in list(self.pages):
            manifest = self.manifest_by_id.get(applet_id)
            source_changed = bool(
                applet_id != DASHBOARD_ID
                and manifest is not None
                and self.loaded_applet_directories.get(applet_id) != manifest.directory
            )
            if applet_id in keep and not source_changed:
                continue
            widget = self.pages.pop(applet_id)
            was_current = self.stack.currentWidget() is widget
            self._set_applet_active(widget, False)
            self.stack.removeWidget(widget)
            widget.deleteLater()
            self.loaded_applet_directories.pop(applet_id, None)

            # If the runtime-owned Manual source changes underneath a loaded Manual
            # instance, reload that same explicit instance from its new path.
            if source_changed and was_current:
                replacement = self.ensure_applet(applet_id)
                if replacement is not None:
                    self.stack.setCurrentWidget(replacement)
                    self._set_applet_active(replacement, True)

    def current_id(self):
        if hasattr(self, "stack") and self.pages.get(DASHBOARD_ID) is not None:
            if self.stack.currentWidget() is self.pages[DASHBOARD_ID]:
                return DASHBOARD_ID
        item = self.nav_list.currentItem() if hasattr(self, "nav_list") else None
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _apply_applet_preferences(self, instance_id, widget):
        if widget is None:
            return
        handler = getattr(widget, "apply_host_settings", None)
        if not callable(handler):
            return
        manifest = self.manifest_by_id.get(instance_id) or self.registry.manifests.get(instance_id)
        logical_id = manifest.applet_id if manifest is not None else str(instance_id)
        try:
            handler(
                {
                    "metadata_font": self.config.metadata_font,
                    "hidden_columns": self.config.hidden_columns_for(logical_id),
                },
                lambda hidden, target_id=logical_id: self.config.set_hidden_columns(target_id, hidden),
            )
        except Exception as exc:
            self.status_lbl.setText(f"Status: Applet settings warning: {exc}")

    def _apply_preferences_to_loaded_applets(self):
        for applet_id, widget in self.pages.items():
            if applet_id == DASHBOARD_ID:
                continue
            self._apply_applet_preferences(applet_id, widget)

    def ensure_applet(self, applet_id):
        if applet_id in self.pages:
            return self.pages[applet_id]
        manifest = self.manifest_by_id.get(applet_id)
        if manifest is None:
            return None
        try:
            widget = self.registry.load_widget(manifest, parent=self.stack)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Applet Error",
                f"Could not load {manifest.name}:\n{exc}",
            )
            self.status_lbl.setText(f"Status: Failed to load {manifest.name}.")
            return None
        self.stack.addWidget(widget)
        self.pages[applet_id] = widget
        self.loaded_applet_directories[applet_id] = manifest.directory
        self._apply_applet_preferences(applet_id, widget)
        self._set_applet_active(widget, False)
        self.module_events.emit(
            "applet.loaded",
            applet_id=manifest.applet_id,
            instance_id=manifest.instance_id,
            source=manifest.source,
            name=manifest.name,
            version=manifest.version,
        )
        return widget

    def switch_view(self, current, previous=None):
        if current is None:
            return

        if previous is not None:
            previous_id = previous.data(Qt.ItemDataRole.UserRole)
            if previous_id != DASHBOARD_ID:
                self._set_applet_active(self.pages.get(previous_id), False)

        instance_id = current.data(Qt.ItemDataRole.UserRole)
        if instance_id is None:
            return
        if instance_id == DASHBOARD_ID:
            self.show_dashboard()
            return
        widget = self.ensure_applet(instance_id)
        if widget is None:
            return

        if hasattr(self, "dashboard_btn"):
            self.dashboard_btn.setChecked(False)
        self.stack.setCurrentWidget(widget)
        self._set_applet_active(widget, True)
        self._update_launch_standalone_control(instance_id)
        manifest = self.manifest_by_id.get(instance_id)
        if manifest is not None:
            self._set_context_window_title(manifest.name)
            self.status_lbl.setText(
                f"Status: Active View: {manifest.name} {manifest.version} · {manifest.source}"
            )
            self.module_events.emit(
                "selection.changed",
                applet_id=manifest.applet_id,
                instance_id=manifest.instance_id,
                source=manifest.source,
                label=manifest.name,
            )

    def initialize_enabled_applets(self):
        current = self.current_id()
        self.status_lbl.setText("Status: Initializing enabled applets...")
        QApplication.processEvents()
        for manifest in self.preferred_applet_manifests():
            self.ensure_applet(manifest.instance_id)
            QApplication.processEvents()
        if current:
            for row in range(self.nav_list.count()):
                if self.nav_list.item(row).data(Qt.ItemDataRole.UserRole) == current:
                    self.nav_list.setCurrentRow(row)
                    break
        self.status_lbl.setText(
            "Status: Enabled applets initialized. Scan-only applets remain user-controlled."
        )

