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

from .. import ORGANIZATION_ID, ORGANIZATION_URL, REPOSITORY, VERSION
from ..paths import RuntimePaths
from .common import (
    APPLET_LOGICAL_ROLE, MODULE_CATALOG, SortableTableWidgetItem,
    component_ownership_label, component_provider_label,
)
from .component_location import ManualComponentLocationDialog

class AppletsConfigurationHost:
    def _focus_applet_filter(self):
        self.tabs.setCurrentIndex(self.applets_tab_index)
        self.applet_filter.setFocus()
        self.applet_filter.selectAll()

    def _sort_applet_table(self, column):
        if self._applet_sort_column == column:
            self._applet_sort_order = (
                Qt.SortOrder.DescendingOrder
                if self._applet_sort_order == Qt.SortOrder.AscendingOrder
                else Qt.SortOrder.AscendingOrder
            )
        else:
            self._applet_sort_column = int(column)
            self._applet_sort_order = Qt.SortOrder.AscendingOrder
        self.table.sortItems(self._applet_sort_column, self._applet_sort_order)
        header = self.table.horizontalHeader()
        header.setSortIndicator(self._applet_sort_column, self._applet_sort_order)
        header.setSortIndicatorShown(True)

    def _run_applet_action(self, callback):
        try:
            callback(self)
        except TypeError:
            callback()
        except Exception as exc:
            QMessageBox.warning(self, "Applet enhancement", str(exc))
        self.refresh_applets(rediscover=False)

    def _dynamic_applet_column_index(self, table_column):
        dynamic_index = int(table_column) - self._base_applet_columns
        if 0 <= dynamic_index < len(self._dynamic_applet_columns):
            return dynamic_index
        return None

    def refresh_applets(self, rediscover=True):
        self.table.blockSignals(True)
        try:
            if rediscover:
                self.registry.discover()
            manifests = sorted(
                self.registry.manifests.values(),
                key=lambda m: (m.name.casefold(), m.applet_id, 0 if m.origin == "manual" else 1, m.version),
            )
            query = self.applet_filter.text().strip().casefold() if hasattr(self, "applet_filter") else ""
            if query:
                manifests = [
                    manifest for manifest in manifests
                    if query in " ".join(
                        [manifest.name, manifest.applet_id, manifest.source, manifest.version, manifest.editor]
                    ).casefold()
                ]
            self.table.setRowCount(len(manifests))

            source_column = 2
            management_column = 3
            version_column = 4
            editor_column = 5

            for row, manifest in enumerate(manifests):
                name_item = SortableTableWidgetItem(manifest.name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                name_item.setData(Qt.ItemDataRole.UserRole, manifest.instance_id)
                name_item.setData(APPLET_LOGICAL_ROLE, manifest.applet_id)
                self.table.setItem(row, 0, name_item)

                enabled = self.config.applet_enabled(manifest.instance_id, manifest.applet_id)
                enabled_item = SortableTableWidgetItem("", enabled)
                enabled_item.setFlags(
                    (
                        enabled_item.flags()
                        | Qt.ItemFlag.ItemIsUserCheckable
                        | Qt.ItemFlag.ItemIsEnabled
                        | Qt.ItemFlag.ItemIsSelectable
                    )
                    & ~Qt.ItemFlag.ItemIsEditable
                )
                enabled_item.setCheckState(
                    Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked
                )
                enabled_item.setData(Qt.ItemDataRole.UserRole, manifest.instance_id)
                enabled_item.setData(APPLET_LOGICAL_ROLE, manifest.applet_id)
                self.table.setItem(row, 1, enabled_item)

                for offset, contribution in enumerate(self._dynamic_applet_columns):
                    (
                        _module_id, _column_id, _label, kind, value_provider,
                        changed_callback, editable,
                    ) = contribution
                    column = self._base_applet_columns + offset
                    try:
                        value = value_provider(manifest.applet_id)
                    except Exception:
                        value = False if kind == "check" else "—"
                    item = SortableTableWidgetItem("", bool(value) if kind == "check" else value)
                    item.setData(Qt.ItemDataRole.UserRole, manifest.instance_id)
                    item.setData(Qt.ItemDataRole.UserRole + 1, offset)
                    item.setData(APPLET_LOGICAL_ROLE, manifest.applet_id)
                    can_edit = editable(manifest.applet_id) if callable(editable) else bool(editable)
                    if kind == "check":
                        item.setFlags(
                            (item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                            | Qt.ItemFlag.ItemIsUserCheckable
                        )
                        if changed_callback is None or not can_edit:
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                        item.setCheckState(
                            Qt.CheckState.Checked if bool(value) else Qt.CheckState.Unchecked
                        )
                    else:
                        item.setText(str(value if value is not None else ""))
                        if changed_callback is None or not can_edit:
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(row, column, item)

                source_item = SortableTableWidgetItem(component_provider_label(manifest, self.runtime_paths))
                source_item.setFlags(source_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                source_item.setToolTip(str(manifest.directory))
                self.table.setItem(row, source_column, source_item)
                management_item = SortableTableWidgetItem(component_ownership_label(manifest))
                management_item.setFlags(management_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                management_item.setToolTip(
                    "User-owned component managed by LinSpectacles in the active runtime-owned user store."
                    if manifest.origin == "manual"
                    else "Package-managed component; LinSpectacles will not remove its files."
                )
                self.table.setItem(row, management_column, management_item)
                version_item = SortableTableWidgetItem(manifest.version)
                version_item.setFlags(version_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, version_column, version_item)
                editor_item = SortableTableWidgetItem(manifest.editor)
                editor_item.setFlags(editor_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, editor_column, editor_item)

            applet_header = self.table.horizontalHeader()
            applet_header.setStretchLastSection(False)
            applet_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            for column in range(1, self.table.columnCount()):
                applet_header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
            if self._applet_sort_column is not None:
                self.table.sortItems(self._applet_sort_column, self._applet_sort_order)
                applet_header.setSortIndicator(self._applet_sort_column, self._applet_sort_order)
                applet_header.setSortIndicatorShown(True)
        finally:
            self.table.blockSignals(False)
        self._update_applet_remove_control()

    def _applet_item_changed(self, item):
        instance_id = item.data(Qt.ItemDataRole.UserRole)
        applet_id = item.data(APPLET_LOGICAL_ROLE)
        if not instance_id:
            return
        if item.column() == 1:
            checked = item.checkState() == Qt.CheckState.Checked
            if isinstance(item, SortableTableWidgetItem):
                item.set_sort_value(checked)
            self.config.set_applet_enabled(instance_id, checked, applet_id)
            self.changed = True
            return

        dynamic_index = self._dynamic_applet_column_index(item.column())
        if dynamic_index is None:
            return
        try:
            contribution = self._dynamic_applet_columns[dynamic_index]
            kind = contribution[3]
            changed_callback = contribution[5]
            editable = contribution[6]
            can_edit = editable(applet_id) if callable(editable) else bool(editable)
            if changed_callback is None or not can_edit:
                return
            value = (item.checkState() == Qt.CheckState.Checked) if kind == "check" else item.text().strip()
            if isinstance(item, SortableTableWidgetItem):
                item.set_sort_value(value)
            normalized = changed_callback(applet_id, value)
            if kind == "text" and normalized is not None and str(normalized) != item.text():
                self.table.blockSignals(True)
                item.setText(str(normalized))
                if isinstance(item, SortableTableWidgetItem):
                    item.set_sort_value(normalized)
                self.table.blockSignals(False)
            self.changed = True
        except Exception as exc:
            QMessageBox.warning(self, "Applet enhancement", str(exc))
            self.refresh_applets(rediscover=False)

    def selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _update_applet_remove_control(self):
        if not hasattr(self, "remove_applet_btn"):
            return
        instance_id = self.selected_id()
        manifest = self.registry.manifests.get(instance_id) if instance_id else None
        removable = bool(manifest and manifest.removable)
        self.remove_applet_btn.setEnabled(removable)
        if manifest is None:
            self.remove_applet_btn.setToolTip("Select a User applet to remove.")
        elif removable:
            self.remove_applet_btn.setToolTip("Remove this User applet from the active user applet location.")
        else:
            self.remove_applet_btn.setToolTip("Package-managed applets are owned by their package provider.")

        if hasattr(self, "open_applet_folder_btn"):
            self.open_applet_folder_btn.setEnabled(True)
            self.open_applet_folder_btn.setToolTip(str(self.registry.store))

    def open_manual_applet_folder(self):
        try:
            self.registry.store.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.critical(self, "Open User Applets Folder", str(exc))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.registry.store)))

    def _install_applet_archive(self, filename):
        filename = str(filename or "")
        if not filename:
            return False
        if not self._ensure_manual_location_confirmed():
            return False
        trust = QMessageBox.question(
            self,
            "Add Applet",
            "LinSpectacles applets contain executable Python code. Only add an applet you trust.\n\nContinue with this archive?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if trust != QMessageBox.StandardButton.Yes:
            return False
        try:
            manifest = self.registry.install_zip(filename)
            self.config.set_applet_enabled(manifest.instance_id, True, manifest.applet_id)
            self.changed = True
            self.refresh_applets()
            return True
        except Exception as exc:
            QMessageBox.critical(self, "Add Applet", str(exc))
            return False

    def dragEnterEvent(self, event):
        if self.tabs.currentIndex() != self.applets_tab_index:
            super().dragEnterEvent(event)
            return
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if len(paths) == 1 and paths[0].lower().endswith(".zip"):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        if self.tabs.currentIndex() == self.applets_tab_index and event.mimeData().hasUrls():
            paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
            if len(paths) == 1 and paths[0].lower().endswith(".zip"):
                if self._install_applet_archive(paths[0]):
                    event.acceptProposedAction()
                    return
        super().dropEvent(event)

    def add_applet(self):
        if not self._ensure_manual_location_confirmed():
            return
        filename, _ = QFileDialog.getOpenFileName(
            None,
            "Add LinSpectacles Applet",
            "",
            "LinSpectacles Applet (*.zip);;ZIP Archives (*.zip)",
        )
        if not filename:
            return
        self._install_applet_archive(filename)

    def remove_applet(self):
        instance_id = self.selected_id()
        if not instance_id:
            return
        manifest = self.registry.manifests.get(instance_id)
        if not manifest:
            return
        if not manifest.removable:
            QMessageBox.information(
                self,
                "Remove Applet",
                f"'{manifest.name}' is package-managed and is managed by its package provider. "
                "LinSpectacles will not delete package-managed applet files.",
            )
            return
        answer = QMessageBox.question(
            self,
            "Remove Applet",
            f"Remove the User copy of '{manifest.name}' from {component_provider_label(manifest, self.runtime_paths)}?\n\n"
            "Its applet folder will be deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.registry.remove(instance_id)
            self.config.set_applet_enabled(instance_id, True, manifest.applet_id)
            self.changed = True
            self.refresh_applets()
        except Exception as exc:
            QMessageBox.critical(self, "Remove Applet", str(exc))

