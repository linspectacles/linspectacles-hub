#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# LinSpectacles - Linux Inspection Suite
# Copyright (C) 2026 brunonlinespace
# GPL-3.0-or-later

import json
import sys
from pathlib import Path

from PyQt6.QtCore import QProcess, Qt, QUrl
from PyQt6.QtGui import QAction, QColor, QDesktopServices, QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFontDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QScrollArea,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from . import (
    APP_NAME, ORGANIZATION_ID, ORGANIZATION_URL, REPOSITORY, VERSION,
)
from .applets import AppletRegistry
from .config import PortableConfig
from .modules import EventBus, ModuleContext, ModuleRegistry
from .paths import RuntimePaths
from .styles import DARK_STYLESHEET

DASHBOARD_ID = "__dashboard__"

# Permissive offline module catalogue. This enriches Configuration only; it is
# never a whitelist and never performs network/store/install operations.
MODULE_CATALOG = {
    "applet-organizer": {"name": "Applet Organizer", "dashboard_reorderable": True},
    "boot-environment": {"name": "Boot Environment", "dashboard_reorderable": True},
    "encyclopedia": {"name": "Encyclopedia & What's This?", "dashboard_reorderable": True},
    "privileged-helpers": {"name": "Privileged Helpers", "dashboard_reorderable": False},
    "system-identity": {"name": "System Identity", "dashboard_reorderable": True},
    "system-pulse": {"name": "System Pulse", "dashboard_reorderable": True},
}


class ConfigurationDialog(QDialog):
    """Applet, appearance, startup and Hub Module configuration."""

    def __init__(
        self, registry, module_registry, config, parent=None,
        module_pages=None, initial_page_id=None,
    ):
        super().__init__(parent)
        self.registry = registry
        self.module_registry = module_registry
        self.config = config
        self.module_pages = list(module_pages or [])
        self.initial_page_id = initial_page_id
        self.dynamic_pages = []
        self.changed = False
        self.setWindowTitle("Configuration — LinSpectacles")
        self.resize(820, 650)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        tabs = QTabWidget()
        self.tabs = tabs
        root.addWidget(tabs, 1)

        # Module API v3 Configuration pages are host-owned. The Applet
        # Organizer is the one contributed page with a fixed Suite position:
        # when present it precedes Applets; other module pages remain after
        # Startup and before Modules.
        self.dynamic_page_indexes = {}

        def add_module_configuration_page(contribution):
            try:
                module_id, page_id, label, factory = contribution
                page = factory(tabs)
                if page is None or not isinstance(page, QWidget):
                    raise TypeError("Configuration page factory did not return QWidget")
            except Exception as exc:
                module_id = contribution[0] if len(contribution) > 0 else ""
                page_id = contribution[1] if len(contribution) > 1 else ""
                label = contribution[2] if len(contribution) > 2 else "Hub Module"
                page = QWidget()
                error_layout = QVBoxLayout(page)
                error_layout.setContentsMargins(12, 12, 12, 12)
                error = QLabel(f"Could not create this Hub Module configuration page:\n{exc}")
                error.setWordWrap(True)
                error_layout.addWidget(error)
                error_layout.addStretch(1)
            index = tabs.addTab(page, str(label))
            self.dynamic_pages.append(page)
            self.dynamic_page_indexes[(str(module_id), str(page_id))] = index
            self.dynamic_page_indexes[str(page_id)] = index

        organizer_pages = [
            contribution for contribution in self.module_pages
            if str(contribution[0]) == "applet-organizer"
        ]
        other_module_pages = [
            contribution for contribution in self.module_pages
            if str(contribution[0]) != "applet-organizer"
        ]
        for contribution in organizer_pages:
            add_module_configuration_page(contribution)

        # ------------------------------------------------------------------
        # Applets. The sidebar continues to discover only applets; Suite
        # Modules are configured separately on the dedicated Modules tab.
        # ------------------------------------------------------------------
        applets_page = QWidget()
        applets_layout = QVBoxLayout(applets_page)
        applets_layout.setContentsMargins(12, 12, 12, 12)
        applets_layout.setSpacing(10)

        applets_note = QLabel(
            "Applets are discovered from the active user/portable store and, in RPM installs, "
            "the system applet store. A user copy takes precedence over a system copy with the "
            "same applet ID. Disable hides an applet without deleting it; Remove applies only "
            "to user/portable applets. System-installed applets are managed by DNF."
        )
        applets_note.setWordWrap(True)
        applets_layout.addWidget(applets_note)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Enabled", "Applet", "Source", "Version", "Editor"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        applet_header = self.table.horizontalHeader()
        applet_header.setStretchLastSection(False)
        applet_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        applet_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        applet_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        applet_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        applet_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        applets_layout.addWidget(self.table, 2)

        controls = QHBoxLayout()
        add_btn = QPushButton("Add Applet...")
        self.remove_applet_btn = QPushButton("Remove")
        refresh_btn = QPushButton("Refresh")
        open_btn = QPushButton("Open Applets Folder")
        add_btn.clicked.connect(self.add_applet)
        self.remove_applet_btn.clicked.connect(self.remove_applet)
        refresh_btn.clicked.connect(self.refresh_applets)
        open_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.registry.store)))
        )
        for button in (add_btn, self.remove_applet_btn, refresh_btn, open_btn):
            controls.addWidget(button)
        self.table.itemSelectionChanged.connect(self._update_applet_remove_control)
        controls.addStretch(1)
        applets_layout.addLayout(controls)

        tabs.addTab(applets_page, "Applets")

        # ------------------------------------------------------------------
        # Appearance
        # ------------------------------------------------------------------
        appearance_page = QWidget()
        appearance_layout = QVBoxLayout(appearance_page)
        appearance_layout.setContentsMargins(12, 12, 12, 12)
        appearance_layout.setSpacing(10)

        appearance_heading = QLabel("Metadata display")
        appearance_heading_font = appearance_heading.font()
        appearance_heading_font.setBold(True)
        appearance_heading.setFont(appearance_heading_font)
        appearance_layout.addWidget(appearance_heading)

        appearance_note = QLabel(
            "Choose the font used by metadata/details panes in inspector applets. "
            "The setting is applied to loaded applets immediately after Configuration closes."
        )
        appearance_note.setWordWrap(True)
        appearance_layout.addWidget(appearance_note)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Metadata font:"))
        self.metadata_font_value = config.metadata_font
        self.metadata_font_label = QLabel()
        self.metadata_font_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        font_row.addWidget(self.metadata_font_label, 1)
        choose_font_btn = QPushButton("Choose...")
        choose_font_btn.clicked.connect(self.choose_metadata_font)
        font_row.addWidget(choose_font_btn)
        reset_font_btn = QPushButton("Reset")
        reset_font_btn.clicked.connect(self.reset_metadata_font)
        font_row.addWidget(reset_font_btn)
        appearance_layout.addLayout(font_row)
        appearance_layout.addStretch(1)
        tabs.addTab(appearance_page, "Appearance")
        self._update_metadata_font_label()

        # ------------------------------------------------------------------
        # Startup
        # ------------------------------------------------------------------
        startup_page = QWidget()
        startup_layout = QVBoxLayout(startup_page)
        startup_layout.setContentsMargins(12, 12, 12, 12)
        startup_layout.setSpacing(10)

        heading = QLabel("Startup")
        font = heading.font()
        font.setBold(True)
        heading.setFont(font)
        startup_layout.addWidget(heading)

        self.lazy_checkbox = QCheckBox("Lazy-load utilities")
        self.lazy_checkbox.setChecked(bool(config.lazy_load_utilities))
        startup_layout.addWidget(self.lazy_checkbox)

        note = QLabel(
            "When enabled, applets are imported only when first opened. "
            "When disabled, enabled applets are initialized during LinSpectacles startup. "
            "Live applets activate only while selected. Boot and package inventories remain Scan-only. "
            "Enabled Hub Modules activate at Hub startup because they contribute host features rather than sidebar views."
        )
        note.setWordWrap(True)
        startup_layout.addWidget(note)
        startup_layout.addStretch(1)
        tabs.addTab(startup_page, "Startup")

        # ------------------------------------------------------------------
        # Hub Modules
        # ------------------------------------------------------------------
        modules_page = QWidget()
        modules_layout = QVBoxLayout(modules_page)
        modules_layout.setContentsMargins(12, 12, 12, 12)
        modules_layout.setSpacing(10)

        modules_heading = QLabel("Hub Modules")
        modules_heading_font = modules_heading.font()
        modules_heading_font.setBold(True)
        modules_heading.setFont(modules_heading_font)
        modules_layout.addWidget(modules_heading)

        modules_note = QLabel(
            "This is an offline catalogue and manager for LinSpectacles Hub Modules. Installed modules can be "
            "enabled/disabled and their Dashboard visibility controlled here; known but uninstalled modules are "
            "shown for discovery only. In RPM installs, user modules take precedence over system-installed modules "
            "with the same ID. Remove applies only to user/portable modules; system-installed modules are managed "
            "by DNF. Unknown installed modules remain visible as Uncatalogued. For installed Dashboard modules, "
            "the row position is the Dashboard order: select a reorderable module and use Up/Down to move the row. "
            "Fixed modules do not offer Dashboard reordering."
        )
        modules_note.setWordWrap(True)
        modules_note.setStyleSheet("color:#b8b8b8;")
        modules_layout.addWidget(modules_note)

        self.module_table = QTableWidget(0, 7)
        self.module_table.setHorizontalHeaderLabels(
            ["Installed", "Enabled", "Dashboard", "Hub Module", "Source", "Version", "Editor"]
        )
        self.module_table.verticalHeader().setVisible(False)
        self.module_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.module_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.module_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        module_header = self.module_table.horizontalHeader()
        module_header.setStretchLastSection(False)
        module_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        module_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        module_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        module_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        module_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        module_header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        module_header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.module_table.setMinimumHeight(120)
        modules_layout.addWidget(self.module_table, 1)

        module_controls = QHBoxLayout()
        add_module_btn = QPushButton("Add Module...")
        self.remove_module_btn = QPushButton("Remove")
        self.module_up_btn = QPushButton("Up")
        self.module_down_btn = QPushButton("Down")
        refresh_module_btn = QPushButton("Refresh")
        open_modules_btn = QPushButton("Open Modules Folder")
        add_module_btn.clicked.connect(self.add_module)
        self.remove_module_btn.clicked.connect(self.remove_module)
        self.module_up_btn.clicked.connect(lambda: self.move_selected_module(-1))
        self.module_down_btn.clicked.connect(lambda: self.move_selected_module(1))
        refresh_module_btn.clicked.connect(self.refresh_modules)
        open_modules_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.module_registry.store)))
        )
        for button in (
            add_module_btn,
            self.remove_module_btn,
            self.module_up_btn,
            self.module_down_btn,
            refresh_module_btn,
            open_modules_btn,
        ):
            module_controls.addWidget(button)
        module_controls.addStretch(1)
        modules_layout.addLayout(module_controls)
        # Other enabled module-owned Configuration pages follow Startup.
        for contribution in other_module_pages:
            add_module_configuration_page(contribution)

        # Keep Modules after every enabled module-owned Configuration page.
        self.modules_tab_index = tabs.addTab(modules_page, "Modules")

        # ------------------------------------------------------------------
        # About — final Configuration page, following the current inspector
        # About-page convention used by Scheduler/Interrupts Inspector.
        # ------------------------------------------------------------------
        about = QWidget()
        about_layout = QVBoxLayout(about)
        about_layout.setContentsMargins(24, 20, 24, 18)
        about_layout.setSpacing(8)

        program_root = Path(getattr(parent, "program_root", Path(__file__).resolve().parents[1])).resolve()
        runtime_paths = getattr(parent, "runtime_paths", RuntimePaths.for_program(program_root))

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(112, 112)
        logo_path = program_root / "assets" / "linspectacles-logo.png"
        if logo_path.is_file():
            pix = QPixmap(str(logo_path))
            if not pix.isNull():
                icon_label.setPixmap(
                    pix.scaled(
                        112, 112,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        about_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        name = QLabel("<h2 style='margin:0'>LinSpectacles Hub</h2>")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(name)

        subtitle = QLabel("<b>Linux Inspection Suite</b>")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(subtitle)

        version = QLabel(f"Version {VERSION}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(version)

        slogan = QLabel("<b>Expose. Explore. Explain.</b>")
        slogan.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(slogan)

        desc = QLabel(
            "A modular, portable collection of Linux inspection utilities for examining system "
            "resources and optional diagnostics without changing the system."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(desc)

        details = QLabel(
            f"<b>Build:</b> {runtime_paths.build_label}<br>"
            "<b>Organisation ID:</b> "
            f"<a href='{ORGANIZATION_URL}'>{ORGANIZATION_ID}</a>"
        )
        details.setWordWrap(True)
        details.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
            | Qt.TextInteractionFlag.TextSelectableByMouse
        )
        details.setOpenExternalLinks(True)
        details.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(details)

        copyright_label = QLabel(
            "Copyright © 2026 "
            "<a href='https://github.com/brunonlinespace'>brunonlinespace</a>"
        )
        copyright_label.setOpenExternalLinks(True)
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(copyright_label)

        license_label = QLabel("Licensed under GNU GPLv3 or later.")
        license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(license_label)

        license_url = QUrl.fromLocalFile(str(program_root / "LICENSE")).toString()
        links = QLabel(
            f"<a href='{REPOSITORY}'>GitHub Repository</a> "
            "&nbsp;·&nbsp; "
            f"<a href='{license_url}'>License</a>"
        )
        links.setOpenExternalLinks(True)
        links.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(links)
        about_layout.addStretch(1)
        tabs.addTab(about, "About")

        if self.initial_page_id is not None:
            index = self.dynamic_page_indexes.get(self.initial_page_id)
            if index is None and isinstance(self.initial_page_id, tuple):
                index = self.dynamic_page_indexes.get(tuple(map(str, self.initial_page_id)))
            if index is not None:
                tabs.setCurrentIndex(index)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_button = buttons.button(QDialogButtonBox.StandardButton.Close)
        if close_button is not None:
            close_button.clicked.connect(self._finish)
        root.addWidget(buttons)

        self.refresh_applets()
        self.refresh_modules()

    def _save_startup(self):
        value = self.lazy_checkbox.isChecked()
        if value != self.config.lazy_load_utilities:
            self.config.lazy_load_utilities = value
            self.changed = True

    def _default_metadata_font(self):
        font = QFont("Monospace")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPointSize(10)
        return font

    def _current_metadata_font(self):
        if self.metadata_font_value:
            font = QFont()
            try:
                if font.fromString(self.metadata_font_value):
                    return font
            except Exception:
                pass
        return self._default_metadata_font()

    def _update_metadata_font_label(self):
        font = self._current_metadata_font()
        size = font.pointSizeF()
        size_text = f"{size:g} pt" if size > 0 else "default size"
        self.metadata_font_label.setText(f"{font.family()} — {size_text}")
        self.metadata_font_label.setFont(font)

    def choose_metadata_font(self):
        font, ok = QFontDialog.getFont(
            self._current_metadata_font(), self, "Choose Metadata Font"
        )
        if not ok:
            return
        self.metadata_font_value = font.toString()
        self._update_metadata_font_label()

    def reset_metadata_font(self):
        self.metadata_font_value = ""
        self._update_metadata_font_label()

    def _save_appearance(self):
        if self.metadata_font_value != self.config.metadata_font:
            self.config.metadata_font = self.metadata_font_value
            self.changed = True

    def _can_close_dynamic_pages(self):
        for page in self.dynamic_pages:
            checker = getattr(page, "can_close_configuration", None)
            if not callable(checker):
                continue
            try:
                result = checker()
            except Exception as exc:
                return False, str(exc)
            if isinstance(result, tuple):
                allowed, message = bool(result[0]), str(result[1] if len(result) > 1 else "")
            else:
                allowed, message = bool(result), ""
            if not allowed:
                return False, message
        return True, ""

    def _finish(self):
        allowed, message = self._can_close_dynamic_pages()
        if not allowed:
            QMessageBox.information(self, "Configuration", message or "Wait for the current module operation to finish before closing Configuration.")
            return
        self._save_startup()
        self._save_appearance()
        self.accept()

    def closeEvent(self, event):
        allowed, message = self._can_close_dynamic_pages()
        if not allowed:
            QMessageBox.information(self, "Configuration", message or "Wait for the current module operation to finish before closing Configuration.")
            event.ignore()
            return
        self._save_startup()
        self._save_appearance()
        super().closeEvent(event)

    # ----- Applets -------------------------------------------------------
    def refresh_applets(self):
        try:
            self.table.itemChanged.disconnect(self._enabled_changed)
        except TypeError:
            pass

        self.registry.discover()
        manifests = sorted(self.registry.manifests.values(), key=lambda m: (m.name.casefold(), m.applet_id))
        disabled = self.config.disabled_applets
        self.table.setRowCount(len(manifests))

        for row, manifest in enumerate(manifests):
            enabled_item = QTableWidgetItem("")
            enabled_item.setFlags(
                enabled_item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            enabled_item.setCheckState(
                Qt.CheckState.Unchecked
                if manifest.applet_id in disabled
                else Qt.CheckState.Checked
            )
            enabled_item.setData(Qt.ItemDataRole.UserRole, manifest.applet_id)
            self.table.setItem(row, 0, enabled_item)
            self.table.setItem(row, 1, QTableWidgetItem(manifest.name))
            source_item = QTableWidgetItem(manifest.source)
            source_item.setToolTip(str(manifest.directory))
            self.table.setItem(row, 2, source_item)
            self.table.setItem(row, 3, QTableWidgetItem(manifest.version))
            self.table.setItem(row, 4, QTableWidgetItem(manifest.editor))

        applet_header = self.table.horizontalHeader()
        applet_header.setStretchLastSection(False)
        applet_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        applet_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        applet_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        applet_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        applet_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemChanged.connect(self._enabled_changed)
        self._update_applet_remove_control()

    def _enabled_changed(self, item):
        if item.column() != 0:
            return
        applet_id = item.data(Qt.ItemDataRole.UserRole)
        if not applet_id:
            return
        self.config.set_applet_enabled(
            applet_id, item.checkState() == Qt.CheckState.Checked
        )
        self.changed = True

    def selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _update_applet_remove_control(self):
        if not hasattr(self, "remove_applet_btn"):
            return
        applet_id = self.selected_id()
        manifest = self.registry.manifests.get(applet_id) if applet_id else None
        removable = bool(manifest and manifest.removable)
        self.remove_applet_btn.setEnabled(removable)
        if manifest is None:
            self.remove_applet_btn.setToolTip("Select a user/portable applet to remove.")
        elif removable:
            self.remove_applet_btn.setToolTip("Remove this applet from the writable applet store.")
        else:
            self.remove_applet_btn.setToolTip("System-installed applets are managed by DNF.")

    def add_applet(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Add LinSpectacles Applet",
            "",
            "LinSpectacles Applet (*.zip);;ZIP Archives (*.zip)",
        )
        if not filename:
            return
        trust = QMessageBox.question(
            self,
            "Add Applet",
            "LinSpectacles applets contain executable Python code. Only add an applet you trust.\n\nContinue with this archive?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if trust != QMessageBox.StandardButton.Yes:
            return
        try:
            manifest = self.registry.install_zip(filename)
            self.config.set_applet_enabled(manifest.applet_id, True)
            self.changed = True
            self.refresh_applets()
        except Exception as exc:
            QMessageBox.critical(self, "Add Applet", str(exc))

    def remove_applet(self):
        applet_id = self.selected_id()
        if not applet_id:
            return
        manifest = self.registry.manifests.get(applet_id)
        if not manifest:
            return
        if not manifest.removable:
            QMessageBox.information(
                self,
                "Remove Applet",
                f"'{manifest.name}' is system-installed and is managed by DNF. "
                "LinSpectacles will not delete RPM-owned applet files.",
            )
            return
        location = "portable" if manifest.source == "Portable" else "user"
        answer = QMessageBox.question(
            self,
            "Remove Applet",
            f"Remove '{manifest.name}' from the {location} LinSpectacles applet store?\n\n"
            "Its applet folder will be deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.registry.remove(applet_id)
            self.config.set_applet_enabled(applet_id, True)
            self.changed = True
            self.refresh_applets()
        except Exception as exc:
            QMessageBox.critical(self, "Remove Applet", str(exc))

    # ----- Hub Modules -------------------------------------------------
    def refresh_modules(self):
        try:
            self.module_table.itemChanged.disconnect(self._module_setting_changed)
        except TypeError:
            pass

        self.module_registry.discover()
        installed = dict(self.module_registry.manifests)

        # Installed rows visually express Dashboard/module order. Catalogue-only
        # discovery rows follow afterwards alphabetically and never participate
        # in reordering. There is deliberately no module category taxonomy.
        ordered_installed = self.module_registry.ordered(self.config.module_order)
        rows = [(m.module_id, m, MODULE_CATALOG.get(m.module_id, {})) for m in ordered_installed]
        catalogue_only = []
        for module_id, catalog in MODULE_CATALOG.items():
            if module_id in installed:
                continue
            catalogue_only.append((module_id, None, catalog))
        catalogue_only.sort(key=lambda item: str(item[2].get("name", item[0])).casefold())
        rows.extend(catalogue_only)
        self.module_table.setRowCount(len(rows))

        for row, (module_id, manifest, catalog) in enumerate(rows):
            installed_item = QTableWidgetItem("Yes" if manifest else "No")
            installed_item.setData(Qt.ItemDataRole.UserRole, module_id)
            self.module_table.setItem(row, 0, installed_item)

            enabled_item = QTableWidgetItem("")
            enabled_item.setData(Qt.ItemDataRole.UserRole, module_id)
            dashboard_item = QTableWidgetItem("")
            dashboard_item.setData(Qt.ItemDataRole.UserRole, module_id)
            if manifest is not None:
                enabled_item.setFlags(enabled_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                enabled = self.config.module_enabled(module_id, manifest.enabled_by_default)
                enabled_item.setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)
                dashboard_item.setFlags(dashboard_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                dashboard_item.setCheckState(
                    Qt.CheckState.Checked if self.config.module_dashboard_visible(module_id, True)
                    else Qt.CheckState.Unchecked
                )
                dashboard_item.setToolTip(
                    "Show or hide this module's Dashboard contributions without enabling or disabling the module."
                )
            else:
                enabled_item.setFlags(enabled_item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                dashboard_item.setFlags(dashboard_item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                enabled_item.setToolTip("Catalogue entry — module is not installed in the active module store.")
                dashboard_item.setToolTip("Catalogue entry — module is not installed in the active module store.")
            self.module_table.setItem(row, 1, enabled_item)
            self.module_table.setItem(row, 2, dashboard_item)
            self.module_table.setItem(row, 3, QTableWidgetItem(manifest.name if manifest else str(catalog.get("name", module_id))))
            source_item = QTableWidgetItem(manifest.source if manifest else "Catalogue")
            source_item.setToolTip(str(manifest.directory) if manifest else "Offline catalogue entry")
            self.module_table.setItem(row, 4, source_item)
            self.module_table.setItem(row, 5, QTableWidgetItem(manifest.version if manifest else "—"))
            self.module_table.setItem(row, 6, QTableWidgetItem(manifest.editor if manifest else "—"))

        module_header = self.module_table.horizontalHeader()
        module_header.setStretchLastSection(False)
        module_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        module_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        module_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        module_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        module_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        module_header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        module_header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.module_table.itemChanged.connect(self._module_setting_changed)
        try:
            self.module_table.itemSelectionChanged.disconnect(self._update_module_reorder_controls)
        except TypeError:
            pass
        try:
            self.module_table.itemSelectionChanged.disconnect(self._update_module_remove_control)
        except TypeError:
            pass
        self.module_table.itemSelectionChanged.connect(self._update_module_reorder_controls)
        self.module_table.itemSelectionChanged.connect(self._update_module_remove_control)
        self._update_module_reorder_controls()
        self._update_module_remove_control()

    def _module_setting_changed(self, item):
        if item.column() not in (1, 2):
            return
        module_id = item.data(Qt.ItemDataRole.UserRole)
        if not module_id or module_id not in self.module_registry.manifests:
            return
        checked = item.checkState() == Qt.CheckState.Checked
        if item.column() == 1:
            self.config.set_module_enabled(module_id, checked)
        else:
            self.config.set_module_dashboard_visible(module_id, checked)
        self.changed = True
        self._update_module_reorder_controls()

    def selected_module_id(self):
        row = self.module_table.currentRow()
        if row < 0:
            return None
        item = self.module_table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _update_module_remove_control(self):
        if not hasattr(self, "remove_module_btn"):
            return
        module_id = self.selected_module_id()
        manifest = self.module_registry.manifests.get(module_id) if module_id else None
        removable = bool(manifest and manifest.removable)
        self.remove_module_btn.setEnabled(removable)
        if manifest is None:
            self.remove_module_btn.setToolTip("Select a user/portable Hub Module to remove.")
        elif removable:
            self.remove_module_btn.setToolTip("Remove this module from the writable module store.")
        else:
            self.remove_module_btn.setToolTip("System-installed Hub Modules are managed by DNF.")

    def _module_dashboard_reorderable(self, module_id):
        if module_id not in self.module_registry.manifests:
            return False
        return bool(MODULE_CATALOG.get(str(module_id), {}).get("dashboard_reorderable", True))

    def _update_module_reorder_controls(self):
        module_id = self.selected_module_id()
        can_reorder = bool(module_id and self._module_dashboard_reorderable(module_id))
        manifests = self.module_registry.ordered(self.config.module_order)
        ids = [manifest.module_id for manifest in manifests if self._module_dashboard_reorderable(manifest.module_id)]
        if not can_reorder or module_id not in ids:
            self.module_up_btn.setEnabled(False)
            self.module_down_btn.setEnabled(False)
            tip = "Dashboard order is fixed for this module." if module_id else "Select a reorderable Dashboard module."
            self.module_up_btn.setToolTip(tip)
            self.module_down_btn.setToolTip(tip)
            return
        index = ids.index(module_id)
        self.module_up_btn.setEnabled(index > 0)
        self.module_down_btn.setEnabled(index < len(ids) - 1)
        self.module_up_btn.setToolTip("Move this module's reorderable Dashboard contributions up.")
        self.module_down_btn.setToolTip("Move this module's reorderable Dashboard contributions down.")

    def move_selected_module(self, direction):
        module_id = self.selected_module_id()
        if not module_id or not self._module_dashboard_reorderable(module_id):
            return
        manifests = self.module_registry.ordered(self.config.module_order)
        ids = [manifest.module_id for manifest in manifests]
        movable = [mid for mid in ids if self._module_dashboard_reorderable(mid)]
        if module_id not in movable:
            return
        index = movable.index(module_id)
        new_index = index + int(direction)
        if not 0 <= new_index < len(movable):
            return
        other_id = movable[new_index]
        a, b = ids.index(module_id), ids.index(other_id)
        ids[a], ids[b] = ids[b], ids[a]
        self.config.module_order = ids
        self.changed = True
        self.refresh_modules()
        for row in range(self.module_table.rowCount()):
            item = self.module_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == module_id:
                self.module_table.selectRow(row)
                break

    def add_module(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
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
            "Only add a module you trust. Newly added modules remain disabled until you explicitly enable them.\n\n"
            "Continue with this archive?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if trust != QMessageBox.StandardButton.Yes:
            return
        try:
            manifest = self.module_registry.install_zip(filename)
            # User-installed code never activates merely because its manifest
            # requests enabled_by_default; installation and activation are two
            # separate explicit choices.
            self.config.set_module_enabled(manifest.module_id, False)
            order = self.config.module_order
            if manifest.module_id not in order:
                order.append(manifest.module_id)
                self.config.module_order = order
            self.changed = True
            self.refresh_modules()
        except Exception as exc:
            QMessageBox.critical(self, "Add Hub Module", str(exc))

    def remove_module(self):
        module_id = self.selected_module_id()
        if not module_id:
            return
        manifest = self.module_registry.manifests.get(module_id)
        if not manifest:
            return
        if not manifest.removable:
            QMessageBox.information(
                self,
                "Remove Hub Module",
                f"'{manifest.name}' is system-installed and is managed by DNF. "
                "LinSpectacles will not delete RPM-owned module files.",
            )
            return
        location = "portable" if manifest.source == "Portable" else "user"
        answer = QMessageBox.question(
            self,
            "Remove Hub Module",
            f"Remove '{manifest.name}' from the {location} LinSpectacles module store?\n\n"
            "Its module folder will be deleted. Any active contribution is removed when Configuration closes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.module_registry.remove(module_id)
            self.config.forget_module_state(module_id)
            self.config.forget_module_dashboard_visibility(module_id)
            self.config.module_order = [item for item in self.config.module_order if item != module_id]
            self.changed = True
            self.refresh_modules()
        except Exception as exc:
            QMessageBox.critical(self, "Remove Hub Module", str(exc))


class AboutDialog(QDialog):
    """Pad-family style retained, modeless About dialog."""

    def __init__(self, program_root, parent=None, runtime_paths=None):
        super().__init__(parent)
        self.program_root = Path(program_root).resolve()
        self.runtime_paths = runtime_paths or RuntimePaths.for_program(self.program_root)
        self.setWindowTitle("About — LinSpectacles Hub")
        self.setMinimumSize(540, 590)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 24, 30, 22)
        root.setSpacing(10)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setFixedSize(112, 112)
        logo_path = self.program_root / "assets" / "linspectacles-logo.png"
        if logo_path.is_file():
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                logo_label.setPixmap(
                    pixmap.scaled(
                        112,
                        112,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        root.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        name = QLabel("<h2 style='margin:0'>LinSpectacles Hub</h2>")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(name)

        subtitle = QLabel("<b>Linux Inspection Suite</b>")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(subtitle)

        version = QLabel(f"Version {VERSION}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(version)

        slogan = QLabel("<b>Expose. Explore. Explain.</b>")
        slogan.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(slogan)

        description = QLabel(
            "A modular, portable collection of Linux inspection utilities for examining system "
            "resources and optional diagnostics without changing the system."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(description)

        details = QLabel(
            f"<b>Build:</b> {self.runtime_paths.build_label}<br>"
            "<b>Organisation ID:</b> "
            f"<a href='{ORGANIZATION_URL}'>{ORGANIZATION_ID}</a><br>"
            "<b>Configuration:</b><br>"
            f"{self.runtime_paths.config_file}"
        )
        details.setWordWrap(True)
        details.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
            | Qt.TextInteractionFlag.TextSelectableByMouse
        )
        details.setOpenExternalLinks(True)
        details.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(details)

        copyright_label = QLabel("Copyright © 2026 brunonlinespace")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(copyright_label)

        license_label = QLabel("Licensed under GNU GPLv3 or later.")
        license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(license_label)

        readme_url = QUrl.fromLocalFile(str(self.program_root / "README.md")).toString()
        license_url = QUrl.fromLocalFile(str(self.program_root / "LICENSE")).toString()
        links = QLabel(
            f"<a href='{REPOSITORY}'>GitHub Repository</a> &nbsp;·&nbsp; "
            f"<a href='{readme_url}'>README</a> &nbsp;·&nbsp; "
            f"<a href='{license_url}'>License</a>"
        )
        links.setOpenExternalLinks(True)
        links.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(links)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)


class Linspectacles(QMainWindow):
    def __init__(self, program_root):
        super().__init__()
        self.program_root = Path(program_root).resolve()
        self.runtime_paths = RuntimePaths.for_program(self.program_root)
        self.runtime_paths.ensure_mutable_dirs()
        self.setWindowTitle(APP_NAME)
        self.resize(1350, 900)
        self._about_dialog = None

        icon_path = self.program_root / "assets" / "linspectacles-icon.png"
        if icon_path.is_file():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.config = PortableConfig(self.program_root, self.runtime_paths.config_file)
        self.registry = AppletRegistry(
            self.program_root,
            self.runtime_paths.applet_store,
            self.runtime_paths.system_applet_store,
        )
        self.registry.discover()
        self.module_registry = ModuleRegistry(
            self.program_root,
            self.runtime_paths.module_store,
            self.runtime_paths.system_module_store,
        )
        self.module_registry.discover()
        self.module_events = EventBus()
        self.module_contexts = {}
        self.active_modules = {}
        self.active_module_directories = {}
        self.module_configuration_pages = []
        self.module_suite_state_items = []
        self.module_coverage_annotations = []
        self.module_coverage_columns = []
        # Module API v5 navigation state must exist before setup_sidebar() and
        # the first rebuild_sidebar() call.  An organizer module may replace
        # these defaults later during sync_suite_modules().
        self.navigation_provider = None
        self.navigation_provider_module_id = None
        self.pages = {}
        self.loaded_applet_directories = {}
        self.manifest_by_id = {}

        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QHBoxLayout(central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(DARK_STYLESHEET)

        self.setup_menu()
        self.setup_sidebar()
        self.setup_content_area()
        self.rebuild_sidebar(select_id=DASHBOARD_ID)
        self.sync_suite_modules(show_errors=False)

        if not self.config.lazy_load_utilities:
            self.initialize_enabled_applets()

    def setup_menu(self):
        # Hub-level applet cycling deliberately skips Dashboard.  The comma
        # and period bindings are laptop-friendly and follow the visible
        # sidebar order, wrapping at either end.
        self.previous_applet_action = QAction("Previous Applet", self)
        self.previous_applet_action.setShortcut("Ctrl+,")
        self.previous_applet_action.triggered.connect(
            lambda: self.navigate_applet(-1)
        )
        self.addAction(self.previous_applet_action)

        self.next_applet_action = QAction("Next Applet", self)
        self.next_applet_action.setShortcut("Ctrl+.")
        self.next_applet_action.triggered.connect(
            lambda: self.navigate_applet(1)
        )
        self.addAction(self.next_applet_action)

        self.dashboard_action = QAction("Dashboard", self)
        self.dashboard_action.setShortcut("F5")
        self.dashboard_action.triggered.connect(self.show_dashboard)
        self.addAction(self.dashboard_action)

        self.help_menu = self.menuBar().addMenu("Help")

        documentation_action = QAction("Documentation", self)
        documentation_action.setShortcut("F1")
        documentation_action.triggered.connect(self.open_documentation)
        self.help_menu.addAction(documentation_action)

        # Enabled Hub Modules may add actions to this reserved Help section.
        # The following separator remains the stable boundary before repository
        # and issue-reporting links.
        self.help_links_separator = self.help_menu.addSeparator()

        repository_action = QAction("GitHub Repository", self)
        repository_action.triggered.connect(
            lambda: QDesktopServices.openUrl(
                QUrl(REPOSITORY)
            )
        )
        self.help_menu.addAction(repository_action)

        issue_action = QAction("Raise an Issue", self)
        issue_action.triggered.connect(
            lambda: QDesktopServices.openUrl(
                QUrl(REPOSITORY.rstrip("/") + "/issues")
            )
        )
        self.help_menu.addAction(issue_action)

        self.help_menu.addSeparator()

        about_action = QAction("About LinSpectacles Hub", self)
        about_action.triggered.connect(self.open_about)
        self.help_menu.addAction(about_action)

        # Tools is an extension point, not a permanent empty menu.  It becomes
        # visible only while at least one enabled Hub Module contributes an
        # action.  It is inserted before Help for conventional menu ordering.
        self.tools_menu = QMenu("Tools", self)
        self.menuBar().insertMenu(self.help_menu.menuAction(), self.tools_menu)
        self.tools_menu.menuAction().setVisible(False)

    def open_documentation(self):
        readme = self.program_root / "README.md"
        if readme.is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(readme)))
            return
        QDesktopServices.openUrl(
            QUrl(REPOSITORY)
        )

    def open_about(self):
        if self._about_dialog is not None:
            self._about_dialog.show()
            self._about_dialog.raise_()
            self._about_dialog.activateWindow()
            return

        dialog = AboutDialog(self.program_root, self, self.runtime_paths)
        self._about_dialog = dialog
        dialog.destroyed.connect(lambda *_: setattr(self, "_about_dialog", None))
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def setup_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("background-color: #252526; color: #ffffff;")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 12, 10, 20)

        self.dashboard_btn = QPushButton("Dashboard")
        self.dashboard_btn.setCheckable(True)
        self.dashboard_btn.setStyleSheet(
            "QPushButton { text-align:left; padding:10px; border:none; border-radius:4px; color:#dcdcdc; font-size:11pt; }"
            "QPushButton:hover { background:#3e3e42; }"
            "QPushButton:checked { background:#007acc; color:#ffffff; font-weight:bold; }"
        )
        self.dashboard_btn.clicked.connect(self.show_dashboard)
        layout.addWidget(self.dashboard_btn)

        self.applet_search = QLineEdit()
        self.applet_search.setPlaceholderText("Search applets...")
        self.applet_search.setClearButtonEnabled(True)
        self.applet_search.setVisible(False)
        self.applet_search.textChanged.connect(
            lambda _text: self.rebuild_sidebar(select_id=self.current_id(), rediscover=False)
        )
        layout.addWidget(self.applet_search)

        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet(
            """
            QListWidget { background-color:#252526; border:none; color:#dcdcdc; font-size:11pt; }
            QListWidget::item { padding:10px; border-radius:4px; margin-bottom:4px; }
            QListWidget::item:selected { background-color:#007acc; color:#fff; font-weight:bold; }
            QListWidget::item:hover:!selected { background-color:#3e3e42; }
            """
        )
        self.nav_list.currentItemChanged.connect(self.switch_view)
        self.nav_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.nav_list.customContextMenuRequested.connect(self._show_applet_context_menu)
        # The navigation list owns the expandable vertical area.  Keep the
        # management controls pinned beneath it instead of letting a spacer
        # consume the sidebar and force the list down to its size hint.
        layout.addWidget(self.nav_list, 1)

        self.launch_standalone_btn = QPushButton("Launch Standalone...")
        self.launch_standalone_btn.setVisible(False)
        self.launch_standalone_btn.clicked.connect(self.launch_current_applet_standalone)
        layout.addWidget(self.launch_standalone_btn)

        config = QPushButton("Configuration...")
        config.clicked.connect(lambda: self.open_configuration())
        layout.addWidget(config)

        self.status_lbl = QLabel("Status: Ready")
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet("color:#9cdcfe; font-size:9pt;")
        layout.addWidget(self.status_lbl)

        self.main_layout.addWidget(sidebar)

    def _dashboard_card(self):
        frame = QFrame()
        frame.setObjectName("dashboardCard")
        frame.setStyleSheet(
            "QFrame#dashboardCard { background:#252526; border:1px solid #3f3f46; "
            "border-radius:8px; }"
        )
        return frame

    def setup_content_area(self):
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        dashboard_scroll = QScrollArea()
        dashboard_scroll.setWidgetResizable(True)
        dashboard_scroll.setFrameShape(QFrame.Shape.NoFrame)
        dashboard_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Branding header.  This establishes identity without becoming another
        # launcher; navigation remains exclusively in the sidebar.
        header = QHBoxLayout()
        header.setSpacing(18)

        logo = QLabel()
        logo.setFixedSize(112, 112)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = self.program_root / "assets" / "linspectacles-logo.png"
        if logo_path.is_file():
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                logo.setPixmap(
                    pixmap.scaled(
                        108, 108,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        header.addWidget(logo)

        brand = QVBoxLayout()
        brand.setSpacing(3)
        title = QLabel("LinSpectacles")
        title_font = title.font()
        title_font.setBold(True)
        title_font.setPointSize(max(title_font.pointSize(), 22))
        title.setFont(title_font)
        brand.addWidget(title)

        subtitle = QLabel("Linux Inspection Suite")
        subtitle_font = subtitle.font()
        subtitle_font.setBold(True)
        subtitle_font.setPointSize(max(subtitle_font.pointSize(), 12))
        subtitle.setFont(subtitle_font)
        brand.addWidget(subtitle)

        motto = QLabel("Expose. Explore. Explain.")
        motto_font = motto.font()
        motto_font.setItalic(True)
        motto.setFont(motto_font)
        motto.setStyleSheet("color:#9cdcfe;")
        brand.addWidget(motto)

        description = QLabel(
            "A portable, modular environment for read-only Linux inspection. "
            "The Dashboard reports Suite and session context without running applet scans."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color:#c8c8c8;")
        brand.addWidget(description)
        brand.addStretch(1)
        header.addLayout(brand, 1)
        layout.addLayout(header)

        # Quiet extension point for enabled Hub Modules. Dashboard visibility
        # is a host preference independent of module activation. The container
        # remains invisible when no visible module contributes a widget.
        self.dashboard_module_container = QWidget()
        self.dashboard_module_layout = QVBoxLayout(self.dashboard_module_container)
        self.dashboard_module_layout.setContentsMargins(0, 0, 0, 0)
        self.dashboard_module_layout.setSpacing(12)
        self.dashboard_module_container.setVisible(False)
        layout.addWidget(self.dashboard_module_container)

        lower = QHBoxLayout()
        lower.setSpacing(16)

        # Inspection coverage is intentionally informational.  It never loads
        # or invokes an applet merely to populate the Dashboard.
        coverage_card = self._dashboard_card()
        coverage_layout = QVBoxLayout(coverage_card)
        coverage_layout.setContentsMargins(16, 14, 16, 14)
        coverage_layout.setSpacing(10)
        coverage_heading = QLabel("Inspection Coverage")
        coverage_heading_font = coverage_heading.font()
        coverage_heading_font.setBold(True)
        coverage_heading.setFont(coverage_heading_font)
        coverage_layout.addWidget(coverage_heading)

        coverage_note = QLabel(
            "Applet availability and this session's load state. This table is not navigation and does not trigger scans."
        )
        coverage_note.setWordWrap(True)
        coverage_note.setStyleSheet("color:#b8b8b8;")
        coverage_layout.addWidget(coverage_note)

        coverage_filters = QHBoxLayout()
        coverage_filters.setSpacing(14)
        self.coverage_enabled_only = QCheckBox("Enabled Only")
        self.coverage_loaded_only = QCheckBox("Loaded Only")
        self.coverage_enabled_only.toggled.connect(self.update_dashboard)
        self.coverage_loaded_only.toggled.connect(self.update_dashboard)
        coverage_filters.addWidget(self.coverage_enabled_only)
        coverage_filters.addWidget(self.coverage_loaded_only)
        coverage_filters.addStretch(1)
        coverage_layout.addLayout(coverage_filters)

        self.dashboard_coverage = QTableWidget(0, 4)
        self.dashboard_coverage.setHorizontalHeaderLabels(["Applet", "Version", "Availability", "Session"])
        self.dashboard_coverage.verticalHeader().setVisible(False)
        self.dashboard_coverage.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.dashboard_coverage.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.dashboard_coverage.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.dashboard_coverage.setAlternatingRowColors(True)
        header_view = self.dashboard_coverage.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        coverage_layout.addWidget(self.dashboard_coverage, 1)
        lower.addWidget(coverage_card, 2)

        state_card = self._dashboard_card()
        state_layout = QVBoxLayout(state_card)
        state_layout.setContentsMargins(16, 14, 16, 14)
        state_layout.setSpacing(9)
        state_heading = QLabel("Hub State")
        state_heading_font = state_heading.font()
        state_heading_font.setBold(True)
        state_heading.setFont(state_heading_font)
        state_layout.addWidget(state_heading)

        self.dashboard_installed_status = QLabel()
        self.dashboard_enabled_status = QLabel()
        self.dashboard_loaded_status = QLabel()
        self.dashboard_lazy_status = QLabel()
        self.dashboard_modules_status = QLabel()
        for label in (
            self.dashboard_installed_status,
            self.dashboard_enabled_status,
            self.dashboard_loaded_status,
            self.dashboard_lazy_status,
            self.dashboard_modules_status,
        ):
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            state_layout.addWidget(label)

        self.dashboard_module_state_layout = QVBoxLayout()
        self.dashboard_module_state_layout.setContentsMargins(0, 0, 0, 0)
        self.dashboard_module_state_layout.setSpacing(5)
        state_layout.addLayout(self.dashboard_module_state_layout)

        state_layout.addSpacing(8)
        principle = QLabel(
            "Dashboard policy\n"
            "• No applet is opened here.\n"
            "• Scan-only applets remain user-controlled.\n"
            "• Disabled applets stay visible here only as coverage information."
        )
        principle.setWordWrap(True)
        principle.setStyleSheet("color:#b8b8b8;")
        state_layout.addWidget(principle)
        state_layout.addStretch(1)
        lower.addWidget(state_card, 1)

        layout.addLayout(lower, 1)

        dashboard_scroll.setWidget(page)
        self.stack.addWidget(dashboard_scroll)
        self.pages[DASHBOARD_ID] = dashboard_scroll
        self.dashboard_page = dashboard_scroll
        self.dashboard_content_page = page
        self.update_dashboard()

    def update_dashboard(self):
        if not hasattr(self, "dashboard_coverage"):
            return

        manifests = sorted(self.registry.manifests.values(), key=lambda m: (m.name.casefold(), m.applet_id))
        disabled = set(self.config.disabled_applets)
        enabled_only = bool(
            hasattr(self, "coverage_enabled_only") and self.coverage_enabled_only.isChecked()
        )
        loaded_only = bool(
            hasattr(self, "coverage_loaded_only") and self.coverage_loaded_only.isChecked()
        )
        visible_manifests = [
            manifest
            for manifest in manifests
            if (not enabled_only or manifest.applet_id not in disabled)
            and (not loaded_only or manifest.applet_id in self.pages)
        ]
        coverage_columns = self._ordered_dashboard_contributions(self.module_coverage_columns)
        annotation_providers = self._ordered_dashboard_contributions(self.module_coverage_annotations)
        headers = ["Applet", "Version", "Availability", "Session"]
        headers.extend(label for _module_id, label, _provider in coverage_columns)
        if annotation_providers:
            # API v3 compatibility only.  New modules should contribute a named
            # column through API v4 rather than using a generic Summary cell.
            headers.append("Summary")
        self.dashboard_coverage.setColumnCount(len(headers))
        self.dashboard_coverage.setHorizontalHeaderLabels(headers)
        self.dashboard_coverage.setRowCount(len(visible_manifests))

        for row, manifest in enumerate(visible_manifests):
            enabled = manifest.applet_id not in disabled
            loaded = manifest.applet_id in self.pages
            record = {
                "id": manifest.applet_id,
                "name": manifest.name,
                "version": manifest.version,
                "enabled": enabled,
                "loaded": loaded,
            }
            values = [
                manifest.name,
                manifest.version,
                "Enabled" if enabled else "Disabled",
                "Loaded" if loaded else "Not loaded",
            ]
            for _module_id, _label, provider in coverage_columns:
                try:
                    value = provider(dict(record))
                except Exception:
                    value = None
                text = str(value).strip() if value is not None else ""
                values.append(text or "—")

            if annotation_providers:
                summary_bits = []
                for _module_id, provider in annotation_providers:
                    try:
                        value = provider(dict(record))
                    except Exception:
                        value = None
                    if value:
                        text = str(value).strip()
                        if text and text not in summary_bits:
                            summary_bits.append(text)
                values.append(" · ".join(summary_bits) if summary_bits else "—")

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.dashboard_coverage.setItem(row, column, item)

        self.dashboard_coverage.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        installed = len(manifests)
        enabled_count = sum(1 for m in manifests if m.applet_id not in disabled)
        loaded_count = sum(1 for m in manifests if m.applet_id in self.pages)
        self.dashboard_installed_status.setText(f"Installed applets: {installed}")
        self.dashboard_enabled_status.setText(f"Enabled applets: {enabled_count}")
        self.dashboard_loaded_status.setText(f"Loaded this session: {loaded_count}")
        self.dashboard_lazy_status.setText(
            "Lazy loading: " + ("Enabled" if self.config.lazy_load_utilities else "Disabled")
        )
        module_manifests = self.module_registry.ordered(self.config.module_order)
        module_enabled_count = sum(
            1
            for manifest in module_manifests
            if self.config.module_enabled(manifest.module_id, manifest.enabled_by_default)
        )
        self.dashboard_modules_status.setText(
            f"Hub modules: {module_enabled_count} enabled / {len(module_manifests)} installed"
        )

        while self.dashboard_module_state_layout.count():
            item = self.dashboard_module_state_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for _module_id, label, provider in self._ordered_dashboard_contributions(self.module_suite_state_items):
            try:
                value = str(provider()).strip()
            except Exception:
                value = "Unavailable"
            if not value:
                continue
            line = QLabel(f"{label}: {value}")
            line.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.dashboard_module_state_layout.addWidget(line)

    # ------------------------------------------------------------------
    # Hub Module API host services
    # ------------------------------------------------------------------
    def _add_module_menu_action(self, module_id, menu_id, text, callback, shortcut=None):
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(str(shortcut))
        action.triggered.connect(lambda _checked=False, cb=callback: cb())
        action.setProperty("linspectaclesModuleId", str(module_id))

        if menu_id == "help":
            self.help_menu.insertAction(self.help_links_separator, action)
        elif menu_id == "tools":
            self.tools_menu.addAction(action)
            self.tools_menu.menuAction().setVisible(True)
        else:
            action.deleteLater()
            raise ValueError("Unsupported Hub Module menu")
        return action

    def _remove_module_menu_action(self, action):
        if action is None:
            return
        self.help_menu.removeAction(action)
        self.tools_menu.removeAction(action)
        action.deleteLater()
        if not self.tools_menu.actions():
            self.tools_menu.menuAction().setVisible(False)

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
        disabled = set(self.config.disabled_applets)
        return [
            {
                "id": manifest.applet_id,
                "name": manifest.name,
                "version": manifest.version,
                "enabled": manifest.applet_id not in disabled,
                "loaded": manifest.applet_id in self.pages,
                "source": manifest.source,
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
        disabled = set(self.config.disabled_applets)
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
                    "name": manifest.name,
                    "version": manifest.version,
                    "author": manifest.author,
                    "editor": manifest.editor,
                    "description": manifest.description,
                    "enabled": manifest.applet_id not in disabled,
                    "loaded": manifest.applet_id in self.pages,
                    "directory": str(manifest.directory),
                    "source": manifest.source,
                    "removable": manifest.removable,
                    "manifest": raw,
                }
            )
        return records

    def _module_current_applet_id(self):
        applet_id = self.current_id()
        return None if applet_id in (None, DASHBOARD_ID) else applet_id

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
            remove_dashboard_widget=self._remove_module_dashboard_widget,
            applet_states=self._module_applet_states,
            applet_metadata=self._module_applet_metadata,
            current_applet_id=self._module_current_applet_id,
            set_status=self._module_set_status,
            add_configuration_page=self._add_module_configuration_page,
            remove_configuration_page=self._remove_module_configuration_page,
            open_configuration_page=self._open_module_configuration_page,
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
        records = []
        for manifest in self.module_registry.ordered(self.config.module_order):
            records.append({
                "id": manifest.module_id,
                "name": manifest.name,
                "version": manifest.version,
                "enabled": self.config.module_enabled(manifest.module_id, manifest.enabled_by_default),
                "dashboard_visible": self.config.module_dashboard_visible(manifest.module_id, True),
                "source": manifest.source,
                "removable": manifest.removable,
            })
        return records

    def _module_activate_applet(self, applet_id):
        applet_id = str(applet_id)
        for row in range(self.nav_list.count()):
            item = self.nav_list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == applet_id:
                self.nav_list.setCurrentRow(row)
                return True
        # A navigation filter must never make an otherwise enabled applet
        # impossible for a module to activate. Clear only the organizer query.
        if hasattr(self, "applet_search") and self.applet_search.text():
            self.applet_search.clear()
            for row in range(self.nav_list.count()):
                item = self.nav_list.item(row)
                if item.data(Qt.ItemDataRole.UserRole) == applet_id:
                    self.nav_list.setCurrentRow(row)
                    return True
        return False

    def _set_navigation_provider(self, module_id, provider):
        if self.navigation_provider is not None and self.navigation_provider_module_id != str(module_id):
            raise RuntimeError("Only one Hub Module may organize applet navigation at a time.")
        if not callable(provider):
            raise TypeError("navigation provider must be callable")
        self.navigation_provider_module_id = str(module_id)
        self.navigation_provider = provider
        if hasattr(self, "applet_search"):
            self.applet_search.setVisible(True)
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
            if hasattr(self, "applet_search"):
                self.applet_search.clear()
                self.applet_search.setVisible(False)
            self.rebuild_sidebar(select_id=self.current_id(), rediscover=False)

    def _refresh_navigation(self, module_id):
        if self.navigation_provider_module_id == str(module_id):
            self.rebuild_sidebar(select_id=self.current_id(), rediscover=False)

    def show_dashboard(self):
        if not hasattr(self, "nav_list") or DASHBOARD_ID not in self.pages:
            return
        current = self.current_id()
        if current not in (None, DASHBOARD_ID):
            self._set_applet_active(self.pages.get(current), False)
        self.nav_list.blockSignals(True)
        self.nav_list.setCurrentRow(-1)
        self.nav_list.blockSignals(False)
        self.dashboard_btn.setChecked(True)
        self._update_launch_standalone_control(None)
        self.update_dashboard()
        self.stack.setCurrentWidget(self.pages[DASHBOARD_ID])
        self.status_lbl.setText("Status: Active View: Dashboard")
        self.module_events.emit("selection.changed", applet_id=None, label="Dashboard")

    def _update_launch_standalone_control(self, applet_id=None):
        if not hasattr(self, "launch_standalone_btn"):
            return
        visible = bool(applet_id and applet_id in self.manifest_by_id)
        self.launch_standalone_btn.setVisible(visible)
        self.launch_standalone_btn.setEnabled(visible)

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

    def _deactivate_suite_module(self, module_id):
        instance = self.active_modules.pop(module_id, None)
        context = self.module_contexts.pop(module_id, None)
        if instance is not None:
            handler = getattr(instance, "deactivate", None)
            if callable(handler):
                try:
                    handler()
                except Exception as exc:
                    self.status_lbl.setText(
                        f"Status: Hub Module cleanup warning ({module_id}): {exc}"
                    )
        if context is not None:
            context.cleanup()
        self.module_registry.unload(module_id)
        self.active_module_directories.pop(module_id, None)
        self.module_events.emit("module.deactivated", module_id=module_id)

    def sync_suite_modules(self, show_errors=True):
        """Activate/deactivate modules to match manifest discovery + config.

        Discovery itself never executes module code. Enabled modules are the
        only ones imported, and every host contribution is registered through a
        versioned ModuleContext so it can be removed cleanly again.
        """
        self.module_registry.discover()
        manifest_list = self.module_registry.ordered(self.config.module_order)
        manifests = {m.module_id: m for m in manifest_list}
        desired = {
            module_id
            for module_id, manifest in manifests.items()
            if self.config.module_enabled(module_id, manifest.enabled_by_default)
        }

        for module_id in list(self.active_modules):
            manifest = manifests.get(module_id)
            active_directory = self.active_module_directories.get(module_id)
            if (
                module_id not in desired
                or manifest is None
                or (active_directory is not None and active_directory != manifest.directory)
            ):
                self._deactivate_suite_module(module_id)

        failures = []
        for manifest in manifest_list:
            module_id = manifest.module_id
            if module_id not in desired or module_id in self.active_modules:
                continue
            context = self._create_module_context(module_id)
            try:
                instance = self.module_registry.load_instance(manifest, context)
                handler = getattr(instance, "activate", None)
                if callable(handler):
                    handler()
            except Exception as exc:
                context.cleanup()
                self.module_registry.unload(module_id)
                failures.append(f"{manifest.name}: {exc}")
                continue
            self.module_contexts[module_id] = context
            self.active_modules[module_id] = instance
            self.active_module_directories[module_id] = manifest.directory
            self.module_events.emit(
                "module.activated", module_id=module_id, name=manifest.name
            )

        self._reorder_module_dashboard_widgets()
        self.update_dashboard()
        self.module_events.emit(
            "modules.changed",
            modules=[
                {
                    "id": manifest.module_id,
                    "name": manifest.name,
                    "version": manifest.version,
                    "enabled": manifest.module_id in desired,
                    "active": manifest.module_id in self.active_modules,
                }
                for manifest in manifests.values()
            ],
        )

        if failures:
            message = "Could not activate one or more Hub Modules:\n\n" + "\n".join(failures)
            self.status_lbl.setText("Status: One or more Hub Modules failed to activate.")
            if show_errors:
                QMessageBox.warning(self, "Hub Module", message)

    def closeEvent(self, event):
        for module_id in list(self.active_modules):
            self._deactivate_suite_module(module_id)
        super().closeEvent(event)

    def enabled_manifests(self):
        disabled = self.config.disabled_applets
        return [
            manifest
            for manifest in self.registry.ordered()
            if manifest.applet_id not in disabled
        ]

    def rebuild_sidebar(self, select_id=None, rediscover=True):
        current = select_id or self.current_id() or DASHBOARD_ID
        if rediscover:
            self.registry.discover()
        enabled = self.enabled_manifests()
        self.manifest_by_id = {manifest.applet_id: manifest for manifest in enabled}

        model = {}
        group_order = []
        if self.navigation_provider is not None:
            try:
                provided = self.navigation_provider() or {}
                if isinstance(provided, dict):
                    model = provided.get("items", {}) if isinstance(provided.get("items", {}), dict) else {}
                    group_order = [str(v) for v in provided.get("group_order", []) if str(v)]
            except Exception as exc:
                self.status_lbl.setText(f"Status: Organizer navigation warning: {exc}")
                model = {}
                group_order = []

        query = self.applet_search.text().strip().casefold() if self.navigation_provider is not None and hasattr(self, "applet_search") else ""
        records = []
        for manifest in enabled:
            entry = model.get(manifest.applet_id, {}) if isinstance(model, dict) else {}
            group = str(entry.get("group", "Unsorted") or "Unsorted")
            tags = [str(tag) for tag in entry.get("tags", [])] if isinstance(entry.get("tags", []), (list, tuple)) else []
            favorite = bool(entry.get("favorite", False))
            haystack = " ".join([manifest.name, manifest.applet_id, group, *tags]).casefold()
            if query and query not in haystack:
                continue
            records.append({"manifest": manifest, "group": group, "favorite": favorite})

        self.nav_list.blockSignals(True)
        self.nav_list.clear()

        if self.navigation_provider is None:
            for record in sorted(records, key=lambda r: r["manifest"].name.casefold()):
                manifest = record["manifest"]
                item = QListWidgetItem(manifest.name)
                item.setData(Qt.ItemDataRole.UserRole, manifest.applet_id)
                self.nav_list.addItem(item)
        else:
            grouped = {}
            for record in records:
                group = "Favorites" if record["favorite"] else record["group"]
                grouped.setdefault(group, []).append(record)
            rank = {name: i for i, name in enumerate(group_order)}
            group_names = sorted(
                grouped,
                key=lambda name: (0 if name == "Favorites" else 1, rank.get(name, 10**6), name.casefold()),
            )
            for group in group_names:
                heading = QListWidgetItem(group)
                heading.setFlags(Qt.ItemFlag.NoItemFlags)
                heading.setData(Qt.ItemDataRole.UserRole, None)
                heading_font = heading.font()
                heading_font.setBold(True)
                heading.setFont(heading_font)
                heading.setForeground(QColor("#007acc"))
                self.nav_list.addItem(heading)
                for record in sorted(grouped[group], key=lambda r: r["manifest"].name.casefold()):
                    manifest = record["manifest"]
                    item = QListWidgetItem("  " + manifest.name)
                    item.setData(Qt.ItemDataRole.UserRole, manifest.applet_id)
                    self.nav_list.addItem(item)

        self.nav_list.blockSignals(False)
        selected = False
        if current != DASHBOARD_ID:
            for row in range(self.nav_list.count()):
                if self.nav_list.item(row).data(Qt.ItemDataRole.UserRole) == current:
                    self.nav_list.setCurrentRow(row)
                    selected = True
                    break
        if current == DASHBOARD_ID:
            self.nav_list.setCurrentRow(-1)
            if hasattr(self, "dashboard_btn"):
                self.dashboard_btn.setChecked(True)
            if self.pages.get(DASHBOARD_ID) is not None:
                self.stack.setCurrentWidget(self.pages[DASHBOARD_ID])
        elif selected:
            if hasattr(self, "dashboard_btn"):
                self.dashboard_btn.setChecked(False)
        elif not rediscover and current in self.manifest_by_id:
            # A text filter may temporarily hide the active applet. Keep its
            # view active rather than bouncing the user to Dashboard while
            # they type; clearing/changing the query can reveal it again.
            self.nav_list.setCurrentRow(-1)
            if hasattr(self, "dashboard_btn"):
                self.dashboard_btn.setChecked(False)
        else:
            self._set_applet_active(self.pages.get(current), False)
            self.nav_list.setCurrentRow(-1)
            if hasattr(self, "dashboard_btn"):
                self.dashboard_btn.setChecked(True)
            if self.pages.get(DASHBOARD_ID) is not None:
                self.stack.setCurrentWidget(self.pages[DASHBOARD_ID])

        self._update_launch_standalone_control(self._active_applet_id())

        if rediscover:
            self._unload_disabled_or_removed()
            self.update_dashboard()

    def navigate_applet(self, direction):
        """Cycle through visible applet rows, skipping Dashboard and organizer headings."""
        if not hasattr(self, "nav_list") or self.nav_list.count() <= 1:
            return
        applet_rows = [
            row for row in range(self.nav_list.count())
            if self.nav_list.item(row).data(Qt.ItemDataRole.UserRole) not in (None, DASHBOARD_ID)
        ]
        if not applet_rows:
            return
        current_row = self.nav_list.currentRow()
        step = 1 if int(direction) >= 0 else -1
        if current_row not in applet_rows:
            target_row = applet_rows[0] if step > 0 else applet_rows[-1]
        else:
            index = applet_rows.index(current_row)
            target_row = applet_rows[(index + step) % len(applet_rows)]
        self.nav_list.setCurrentRow(target_row)

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

            # A newly installed user copy may shadow an RPM applet with the
            # same ID. If that applet was active, replace the embedded widget
            # immediately after Configuration closes rather than requiring a
            # Hub restart.
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

    def _apply_applet_preferences(self, applet_id, widget):
        if widget is None:
            return
        handler = getattr(widget, "apply_host_settings", None)
        if not callable(handler):
            return
        try:
            handler(
                {
                    "metadata_font": self.config.metadata_font,
                    "hidden_columns": self.config.hidden_columns_for(applet_id),
                },
                lambda hidden, target_id=applet_id: self.config.set_hidden_columns(target_id, hidden),
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
            applet_id=applet_id,
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

        applet_id = current.data(Qt.ItemDataRole.UserRole)
        if applet_id is None:
            return
        if applet_id == DASHBOARD_ID:
            self.show_dashboard()
            return
        widget = self.ensure_applet(applet_id)
        if widget is None:
            return

        if hasattr(self, "dashboard_btn"):
            self.dashboard_btn.setChecked(False)
        self.stack.setCurrentWidget(widget)
        self._set_applet_active(widget, True)
        self._update_launch_standalone_control(applet_id)
        self.status_lbl.setText(f"Status: Active View: {current.text()}")
        self.module_events.emit(
            "selection.changed",
            applet_id=None if applet_id == DASHBOARD_ID else applet_id,
            label=current.text(),
        )

    def initialize_enabled_applets(self):
        current = self.current_id()
        self.status_lbl.setText("Status: Initializing enabled applets...")
        QApplication.processEvents()
        for manifest in self.enabled_manifests():
            self.ensure_applet(manifest.applet_id)
            QApplication.processEvents()
        if current:
            for row in range(self.nav_list.count()):
                if self.nav_list.item(row).data(Qt.ItemDataRole.UserRole) == current:
                    self.nav_list.setCurrentRow(row)
                    break
        self.status_lbl.setText(
            "Status: Enabled applets initialized. Scan-only applets remain user-controlled."
        )

    def open_configuration(self, initial_page_id=None):
        previous_lazy = self.config.lazy_load_utilities
        current = self.current_id()
        module_pages = sorted(
            list(self.module_configuration_pages),
            key=lambda item: (self._module_rank(item[0]), str(item[2]).casefold()),
        )
        dialog = ConfigurationDialog(
            self.registry, self.module_registry, self.config, self,
            module_pages=module_pages, initial_page_id=initial_page_id,
        )
        dialog.exec()

        # Hub Modules are synchronized before applet-change events are sent,
        # so disabled/removed modules cannot receive a stale notification and
        # newly enabled modules immediately see the current host state.
        self.sync_suite_modules(show_errors=True)
        self.rebuild_sidebar(select_id=current)
        self._apply_preferences_to_loaded_applets()
        enabled = self.config.lazy_load_utilities
        if not enabled:
            self.initialize_enabled_applets()
        elif not previous_lazy and enabled:
            self.status_lbl.setText(
                "Status: Lazy loading enabled; already loaded applets remain cached."
            )
        self.update_dashboard()
        self.module_events.emit("applets.changed", applets=self._module_applet_states())
        self.module_events.emit(
            "configuration.changed",
            applets=self._module_applet_states(),
            lazy_load=self.config.lazy_load_utilities,
        )


def run(program_root):
    app = QApplication(sys.argv)
    app.setApplicationName("LinSpectacles")
    app.setOrganizationName(ORGANIZATION_ID)
    icon_path = Path(program_root).resolve() / "assets" / "linspectacles-icon.png"
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))
    suite = Linspectacles(program_root)
    suite.show()
    return app.exec()
