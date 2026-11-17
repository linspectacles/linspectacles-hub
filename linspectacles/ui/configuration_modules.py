#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# LinSpectacles - Linux Inspection Suite
# Copyright (C) 2026 brunonlinespace
# GPL-3.0-or-later

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QFileDialog, QHeaderView, QMessageBox, QTableWidgetItem

from .common import (
    APPLET_LOGICAL_ROLE,
    MODULE_CATALOG,
    SortableTableWidgetItem,
    component_ownership_label,
    component_provider_label,
)


class ModulesConfigurationHost:
    """Logical Hub Module management with physical-copy provenance below it."""

    def _sort_module_table(self, column):
        if self._module_sort_column == column:
            self._module_sort_order = (
                Qt.SortOrder.DescendingOrder
                if self._module_sort_order == Qt.SortOrder.AscendingOrder
                else Qt.SortOrder.AscendingOrder
            )
        else:
            self._module_sort_column = int(column)
            self._module_sort_order = Qt.SortOrder.AscendingOrder
        self.module_table.sortItems(self._module_sort_column, self._module_sort_order)
        header = self.module_table.horizontalHeader()
        header.setSortIndicator(self._module_sort_column, self._module_sort_order)
        header.setSortIndicatorShown(True)

    def _clear_module_sort(self):
        self._module_sort_column = None
        self._module_sort_order = Qt.SortOrder.AscendingOrder
        self.module_table.horizontalHeader().setSortIndicatorShown(False)

    def _preferred_module_manifest(self, manifests):
        manifests = list(manifests or [])
        if not manifests:
            return None
        preferred = [
            manifest for manifest in manifests
            if manifest.origin == self.config.preferred_component_source
        ]
        pool = preferred or manifests
        return sorted(pool, key=lambda m: (0 if m.origin == "manual" else 1, m.source, m.version))[0]

    def refresh_modules(self):
        selected_logical = self.selected_module_logical_id()
        try:
            self.module_table.itemChanged.disconnect(self._module_setting_changed)
        except TypeError:
            pass

        self.module_registry.discover()
        ordered_installed = self.module_registry.ordered(self.config.module_order)
        groups = {}
        logical_order = []
        for manifest in ordered_installed:
            if manifest.module_id not in groups:
                groups[manifest.module_id] = []
                logical_order.append(manifest.module_id)
            groups[manifest.module_id].append(manifest)

        for module_id in MODULE_CATALOG:
            if module_id not in groups:
                logical_order.append(module_id)

        self.module_table.setRowCount(len(logical_order))
        for row, logical_id in enumerate(logical_order):
            candidates = groups.get(logical_id, [])
            catalog = MODULE_CATALOG.get(logical_id, {})
            runtime_manifest = self._preferred_module_manifest(candidates)
            name = (
                runtime_manifest.name
                if runtime_manifest is not None
                else str(catalog.get("name", logical_id))
            )

            name_item = SortableTableWidgetItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, logical_id)
            name_item.setData(APPLET_LOGICAL_ROLE, logical_id)
            self.module_table.setItem(row, 0, name_item)

            installed_item = SortableTableWidgetItem("Yes" if candidates else "No", bool(candidates))
            installed_item.setData(Qt.ItemDataRole.UserRole, logical_id)
            self.module_table.setItem(row, 1, installed_item)

            enabled_state = False
            enabled_item = SortableTableWidgetItem("", enabled_state)
            enabled_item.setData(Qt.ItemDataRole.UserRole, logical_id)
            enabled_item.setData(APPLET_LOGICAL_ROLE, logical_id)
            dashboard_state = False
            dashboard_item = SortableTableWidgetItem("", dashboard_state)
            dashboard_item.setData(Qt.ItemDataRole.UserRole, logical_id)
            dashboard_item.setData(APPLET_LOGICAL_ROLE, logical_id)

            if candidates:
                default_enabled = any(bool(m.enabled_by_default) for m in candidates)
                enabled_state = self.config.module_enabled(logical_id, default_enabled)
                enabled_item.set_sort_value(enabled_state)
                enabled_item.setFlags(enabled_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                enabled_item.setCheckState(
                    Qt.CheckState.Checked if enabled_state else Qt.CheckState.Unchecked
                )
                enabled_item.setToolTip(
                    "Enable or disable this logical Hub Module. The Preferred Component Source setting chooses which installed copy runs."
                )
                dashboard_state = self.config.module_dashboard_visible(logical_id, True)
                dashboard_item.set_sort_value(dashboard_state)
                dashboard_item.setFlags(dashboard_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                dashboard_item.setCheckState(
                    Qt.CheckState.Checked if dashboard_state else Qt.CheckState.Unchecked
                )
                dashboard_item.setToolTip(
                    "Show or hide this logical module's Dashboard contributions without disabling the module."
                )
            else:
                enabled_item.setFlags(enabled_item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                dashboard_item.setFlags(dashboard_item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                enabled_item.setToolTip("Catalogue entry — module is not installed.")
                dashboard_item.setToolTip("Catalogue entry — module is not installed.")

            self.module_table.setItem(row, 2, enabled_item)
            self.module_table.setItem(row, 3, dashboard_item)
            self.module_table.setItem(
                row, 4,
                SortableTableWidgetItem(
                    component_ownership_label(runtime_manifest)
                    if runtime_manifest is not None else "—"
                ),
            )
            self.module_table.setItem(
                row, 5,
                SortableTableWidgetItem(runtime_manifest.version if runtime_manifest is not None else "—"),
            )
            self.module_table.setItem(
                row, 6,
                SortableTableWidgetItem(runtime_manifest.editor if runtime_manifest is not None else "—"),
            )

        header = self.module_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, 7):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        if self._module_sort_column is not None:
            self.module_table.sortItems(self._module_sort_column, self._module_sort_order)
            header.setSortIndicator(self._module_sort_column, self._module_sort_order)
            header.setSortIndicatorShown(True)

        self.module_table.itemChanged.connect(self._module_setting_changed)
        try:
            self.module_table.itemSelectionChanged.disconnect(self._module_selection_changed)
        except TypeError:
            pass
        self.module_table.itemSelectionChanged.connect(self._module_selection_changed)
        try:
            self.module_copies_table.itemSelectionChanged.disconnect(self._update_module_remove_control)
        except TypeError:
            pass
        self.module_copies_table.itemSelectionChanged.connect(self._update_module_remove_control)

        if selected_logical:
            for row in range(self.module_table.rowCount()):
                item = self.module_table.item(row, 0)
                if item and item.data(Qt.ItemDataRole.UserRole) == selected_logical:
                    self.module_table.selectRow(row)
                    break
        if self.module_table.currentRow() < 0 and self.module_table.rowCount():
            self.module_table.selectRow(0)
        self._module_selection_changed()

    def _module_setting_changed(self, item):
        if item.column() not in (2, 3):
            return
        logical_id = item.data(APPLET_LOGICAL_ROLE) or item.data(Qt.ItemDataRole.UserRole)
        if not logical_id:
            return
        checked = item.checkState() == Qt.CheckState.Checked
        if isinstance(item, SortableTableWidgetItem):
            item.set_sort_value(checked)
        if item.column() == 2:
            self.config.set_module_enabled(logical_id, checked)
        else:
            self.config.set_module_dashboard_visible(logical_id, checked)
        self.changed = True
        self._update_module_reorder_controls()

    def selected_module_logical_id(self):
        row = self.module_table.currentRow()
        if row < 0:
            return None
        item = self.module_table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    # Compatibility for older internal callers.
    def selected_module_id(self):
        return self.selected_module_logical_id()

    def selected_module_copy_id(self):
        row = self.module_copies_table.currentRow()
        if row < 0:
            return None
        item = self.module_copies_table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _module_selection_changed(self):
        logical_id = self.selected_module_logical_id()
        candidates = (
            self.module_registry.manifests_for(logical_id)
            if logical_id else []
        )
        candidates = sorted(
            candidates,
            key=lambda m: (0 if m.origin == "manual" else 1, m.source, m.version),
        )
        self.module_copies_table.setRowCount(len(candidates))
        preferred = self._preferred_module_manifest(candidates)
        preferred_row = -1
        for row, manifest in enumerate(candidates):
            source_item = QTableWidgetItem(component_ownership_label(manifest))
            source_item.setData(Qt.ItemDataRole.UserRole, manifest.instance_id)
            source_item.setToolTip(
                "User-owned and removable by LinSpectacles."
                if manifest.origin == "manual"
                else "Package-managed; removal belongs to the package provider."
            )
            self.module_copies_table.setItem(row, 0, source_item)
            self.module_copies_table.setItem(row, 1, QTableWidgetItem(manifest.version))
            self.module_copies_table.setItem(
                row, 2,
                QTableWidgetItem(component_provider_label(manifest, self.runtime_paths)),
            )
            path_item = QTableWidgetItem(str(manifest.directory))
            path_item.setToolTip(str(manifest.directory))
            self.module_copies_table.setItem(row, 3, path_item)
            if preferred is not None and manifest.instance_id == preferred.instance_id:
                preferred_row = row
        if preferred_row >= 0:
            self.module_copies_table.selectRow(preferred_row)
        self._update_module_reorder_controls()
        self._update_module_remove_control()

    def _update_module_remove_control(self):
        if not hasattr(self, "remove_module_btn"):
            return
        instance_id = self.selected_module_copy_id()
        manifest = self.module_registry.manifests.get(instance_id) if instance_id else None
        removable = bool(manifest and manifest.removable)
        self.remove_module_btn.setEnabled(removable)
        if manifest is None:
            self.remove_module_btn.setToolTip("Select an installed User module copy to remove.")
        elif removable:
            self.remove_module_btn.setToolTip("Remove this User module copy from the active user module location.")
        else:
            self.remove_module_btn.setToolTip("Package-managed Hub Modules are owned by their package provider.")

    def _module_dashboard_reorderable(self, logical_id):
        if not logical_id:
            return False
        return bool(MODULE_CATALOG.get(str(logical_id), {}).get("dashboard_reorderable", True))

    def _update_module_reorder_controls(self):
        logical_id = self.selected_module_logical_id()
        can_reorder = bool(logical_id and self._module_dashboard_reorderable(logical_id))
        logical_ids = []
        for candidate in self.module_registry.ordered(self.config.module_order):
            if (
                candidate.module_id not in logical_ids
                and self._module_dashboard_reorderable(candidate.module_id)
            ):
                logical_ids.append(candidate.module_id)
        if not can_reorder or logical_id not in logical_ids:
            self.module_up_btn.setEnabled(False)
            self.module_down_btn.setEnabled(False)
            tip = "Dashboard order is fixed for this module." if logical_id else "Select a reorderable Dashboard module."
            self.module_up_btn.setToolTip(tip)
            self.module_down_btn.setToolTip(tip)
            return
        index = logical_ids.index(logical_id)
        self.module_up_btn.setEnabled(index > 0)
        self.module_down_btn.setEnabled(index < len(logical_ids) - 1)
        self.module_up_btn.setToolTip("Move this logical module's Dashboard contributions up.")
        self.module_down_btn.setToolTip("Move this logical module's Dashboard contributions down.")

    def move_selected_module(self, direction):
        logical_id = self.selected_module_logical_id()
        if logical_id is None or not self._module_dashboard_reorderable(logical_id):
            return
        ids = []
        for candidate in self.module_registry.ordered(self.config.module_order):
            if candidate.module_id not in ids:
                ids.append(candidate.module_id)
        movable = [mid for mid in ids if self._module_dashboard_reorderable(mid)]
        if logical_id not in movable:
            return
        index = movable.index(logical_id)
        new_index = index + int(direction)
        if not 0 <= new_index < len(movable):
            return
        other_id = movable[new_index]
        a, b = ids.index(logical_id), ids.index(other_id)
        ids[a], ids[b] = ids[b], ids[a]
        # Reordering is a Dashboard-order action, so return the table to its
        # natural module order rather than hiding the move behind a view sort.
        self._clear_module_sort()
        self.config.module_order = ids
        self.changed = True
        self.refresh_modules()
        for row in range(self.module_table.rowCount()):
            item = self.module_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == logical_id:
                self.module_table.selectRow(row)
                break

    def open_manual_module_folder(self):
        try:
            self.module_registry.store.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.critical(self, "Open User Modules Folder", str(exc))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.module_registry.store)))

    def add_module(self):
        if not self._ensure_manual_location_confirmed():
            return
        filename, _ = QFileDialog.getOpenFileName(
            None,
            "Add LinSpectacles Module",
            "",
            "LinSpectacles Module (*.zip);;ZIP Archives (*.zip)",
        )
        if not filename:
            return
        trust = QMessageBox.question(
            self,
            "Add Hub Module",
            "Hub Modules contain executable Python code that runs inside the LinSpectacles host when enabled. "
            "Only add a module you trust. A newly installed logical module starts disabled. If the same logical "
            "module is already enabled from another source, the Preferred Component Source setting determines "
            "which installed implementation runs.\n\nContinue with this archive?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if trust != QMessageBox.StandardButton.Yes:
            return
        try:
            existing_ids = {m.module_id for m in self.module_registry.manifests.values()}
            manifest = self.module_registry.install_zip(filename)
            if manifest.module_id not in existing_ids:
                self.config.set_module_enabled(manifest.module_id, False)
            order = self.config.module_order
            if manifest.module_id not in order:
                order.append(manifest.module_id)
                self.config.module_order = order
            self.changed = True
            self.refresh_modules()
            for row in range(self.module_table.rowCount()):
                item = self.module_table.item(row, 0)
                if item and item.data(Qt.ItemDataRole.UserRole) == manifest.module_id:
                    self.module_table.selectRow(row)
                    break
        except Exception as exc:
            QMessageBox.critical(self, "Add Hub Module", str(exc))

    def remove_module(self):
        instance_id = self.selected_module_copy_id()
        if not instance_id:
            return
        manifest = self.module_registry.manifests.get(instance_id)
        if not manifest:
            return
        if not manifest.removable:
            QMessageBox.information(
                self,
                "Remove Hub Module",
                f"'{manifest.name}' is Package-managed. LinSpectacles will not delete files owned by its package provider.",
            )
            return
        answer = QMessageBox.question(
            self,
            "Remove Hub Module",
            f"Remove the User copy of '{manifest.name}' from {component_provider_label(manifest, self.runtime_paths)}?\n\n"
            "Its module folder will be deleted. If another installed copy exists and the logical module remains enabled, "
            "that copy can become the runtime implementation when Configuration closes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        logical_id = manifest.module_id
        try:
            self.module_registry.remove(instance_id)
            if not self.module_registry.manifests_for(logical_id):
                self.config.forget_module_state(logical_id)
                self.config.forget_module_dashboard_visibility(logical_id)
                self.config.module_order = [item for item in self.config.module_order if item != logical_id]
            self.changed = True
            self.refresh_modules()
        except Exception as exc:
            QMessageBox.critical(self, "Remove Hub Module", str(exc))
