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
from .common import APPLET_LOGICAL_ROLE, MODULE_CATALOG
from .component_location import ManualComponentLocationDialog
from .runtime_migration import RuntimeMigrationDialog

from .configuration_applets import AppletsConfigurationHost
from .configuration_modules import ModulesConfigurationHost

class ConfigurationDialog(AppletsConfigurationHost, ModulesConfigurationHost, QDialog):
    def __init__(
        self, registry, module_registry, config, parent=None,
        module_pages=None, applet_extensions=None, applet_columns=None,
        applet_actions=None, initial_page_id=None,
    ):
        super().__init__(parent)
        self.registry = registry
        self.module_registry = module_registry
        self.config = config
        self.runtime_paths = getattr(parent, "runtime_paths", RuntimePaths.for_program(Path(__file__).resolve().parents[2]))
        self.module_pages = list(module_pages or [])
        self.applet_extensions = list(applet_extensions or [])
        self.applet_columns = list(applet_columns or [])
        self.applet_actions = list(applet_actions or [])
        self.initial_page_id = initial_page_id
        self.dynamic_pages = []
        self.changed = False
        self.runtime_migration_completed = False
        self.setWindowTitle("Configuration")
        self.resize(820, 650)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        tabs = QTabWidget()
        self.tabs = tabs
        root.addWidget(tabs, 1)

        # Module-owned Configuration pages remain separate host-owned tabs.
        # Applet-page enhancements prefer API v7 table columns/actions; the legacy
        # API v6 widget extension remains available for compatibility.
        self.dynamic_page_indexes = {}
        self.dynamic_page_widgets = {}

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
            self.dynamic_page_widgets[(str(module_id), str(page_id))] = page
            self.dynamic_page_widgets[str(page_id)] = page

        other_module_pages = list(self.module_pages)

        # ------------------------------------------------------------------
        # Applets. The sidebar continues to discover only applets; Suite
        # Modules are configured separately on the dedicated Modules tab.
        # ------------------------------------------------------------------
        applets_page = QWidget()
        applets_layout = QVBoxLayout(applets_page)
        applets_layout.setContentsMargins(12, 12, 12, 12)
        applets_layout.setSpacing(10)

        applets_note = QLabel(
            "Applets are discovered from the runtime-owned User location plus the known Package-managed location. "
            "Portable Source uses this Hub's internal applets folder; Integrated Source and Packaged use XDG user data. "
            "User and Package-managed copies with the same logical ID are both shown. Package-managed copies remain owned by their package provider."
        )
        applets_note.setWordWrap(True)
        applets_layout.addWidget(applets_note)

        self.applet_filter = QLineEdit()
        self.applet_filter.setPlaceholderText("Search applets...")
        self.applet_filter.setClearButtonEnabled(True)
        self.applet_filter.textChanged.connect(
            lambda _text: self.refresh_applets(rediscover=False)
        )
        applets_layout.addWidget(self.applet_filter)

        self._base_applet_columns = 6
        dynamic_columns = list(self.applet_columns)
        # Keep module-contributed columns stable, but place Organizer's Layer
        # then Favourite at the far right of the canonical Applets table.
        tail_order = {"layer": 0, "favourite": 1, "favorite": 1}
        ordinary_dynamic = [
            contribution for contribution in dynamic_columns
            if str(contribution[2]).strip().casefold() not in tail_order
        ]
        organizer_dynamic = sorted(
            [
                contribution for contribution in dynamic_columns
                if str(contribution[2]).strip().casefold() in tail_order
            ],
            key=lambda contribution: tail_order[str(contribution[2]).strip().casefold()],
        )
        self._dynamic_applet_columns = ordinary_dynamic + organizer_dynamic
        headers = ["Applet", "Enabled", "Source", "Owner", "Version", "Editor"] + [
            str(contribution[2]) for contribution in self._dynamic_applet_columns
        ]
        self.table = QTableWidget(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.table.itemChanged.connect(self._applet_item_changed)
        applet_header = self.table.horizontalHeader()
        applet_header.setStretchLastSection(False)
        applet_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, len(headers)):
            applet_header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        applet_header.setSectionsClickable(True)
        applet_header.setSortIndicatorShown(False)
        self._applet_sort_column = None
        self._applet_sort_order = Qt.SortOrder.AscendingOrder
        applet_header.sectionClicked.connect(self._sort_applet_table)
        applets_layout.addWidget(self.table, 2)

        controls = QHBoxLayout()
        add_btn = QPushButton("Add Applet...")
        self.remove_applet_btn = QPushButton("Remove")
        refresh_btn = QPushButton("Refresh")
        self.open_applet_folder_btn = QPushButton("Open User Applets Folder")
        add_btn.clicked.connect(self.add_applet)
        self.remove_applet_btn.clicked.connect(self.remove_applet)
        refresh_btn.clicked.connect(self.refresh_applets)
        self.open_applet_folder_btn.clicked.connect(self.open_manual_applet_folder)
        for button in (add_btn, self.remove_applet_btn, refresh_btn, self.open_applet_folder_btn):
            controls.addWidget(button)
        for contribution in self.applet_actions:
            try:
                _module_id, _action_id, label, callback = contribution
                if not callable(callback):
                    raise TypeError("Applets action callback is not callable")
                button = QPushButton(str(label))
                button.clicked.connect(
                    lambda _checked=False, cb=callback: self._run_applet_action(cb)
                )
                controls.addWidget(button)
            except Exception:
                continue
        self.table.itemSelectionChanged.connect(self._update_applet_remove_control)
        controls.addStretch(1)
        applets_layout.addLayout(controls)

        for contribution in self.applet_extensions:
            try:
                module_id, extension_id, label, factory = contribution
                extension = factory(applets_page)
                if extension is None or not isinstance(extension, QWidget):
                    raise TypeError("Applets extension factory did not return QWidget")
            except Exception as exc:
                module_id = contribution[0] if len(contribution) > 0 else ""
                extension_id = contribution[1] if len(contribution) > 1 else ""
                label = contribution[2] if len(contribution) > 2 else "Applet enhancement"
                extension = QWidget(applets_page)
                error_layout = QVBoxLayout(extension)
                error_layout.setContentsMargins(0, 0, 0, 0)
                error = QLabel(f"Could not create this Hub Module Applets enhancement:\n{exc}")
                error.setWordWrap(True)
                error_layout.addWidget(error)
            heading = QLabel(str(label))
            heading_font = heading.font()
            heading_font.setBold(True)
            heading.setFont(heading_font)
            applets_layout.addWidget(heading)
            applets_layout.addWidget(extension, 1)
            self.dynamic_pages.append(extension)

        self.applets_tab_index = tabs.addTab(applets_page, "Applets")
        self.setAcceptDrops(True)
        find_applets_action = QAction("Find Applet", self)
        find_applets_action.setShortcut("Ctrl+F")
        find_applets_action.triggered.connect(self._focus_applet_filter)
        self.addAction(find_applets_action)

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
        # Source runtimes may migrate safely between Portable and Integrated.
        # Packaged runtimes remain package-manager controlled and cannot switch.
        # ------------------------------------------------------------------
        runtime_page = QWidget()
        runtime_layout = QVBoxLayout(runtime_page)
        runtime_layout.setContentsMargins(12, 12, 12, 12)
        runtime_layout.setSpacing(10)

        runtime_heading = QLabel("Hub Runtime")
        runtime_heading_font = runtime_heading.font()
        runtime_heading_font.setBold(True)
        runtime_heading.setFont(runtime_heading_font)
        runtime_layout.addWidget(runtime_heading)

        runtime_note = QLabel(
            "Runtime mode determines where Hub-owned configuration and User components live. "
            "Source builds can migrate safely between Portable and Integrated; packaged builds remain integrated."
        )
        runtime_note.setWordWrap(True)
        runtime_layout.addWidget(runtime_note)

        runtime_rows = (
            ("Runtime:", self.runtime_paths.build_label),
            ("Configuration:", str(self.runtime_paths.config_root)),
            ("Hub data:", str(self.runtime_paths.data_root)),
            ("Desktop integration:", "Expected" if self.runtime_paths.desktop_integration_expected else "Not expected"),
        )
        for label_text, value_text in runtime_rows:
            row = QHBoxLayout()
            label = QLabel(label_text)
            label_font = label.font()
            label_font.setBold(True)
            label.setFont(label_font)
            value = QLabel(value_text)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value.setWordWrap(True)
            row.addWidget(label)
            row.addWidget(value, 1)
            runtime_layout.addLayout(row)

        if not self.runtime_paths.packaged:
            target_label = "Integrated" if self.runtime_paths.portable else "Portable"
            switch_runtime_btn = QPushButton(f"Switch to {target_label}...")
            switch_runtime_btn.clicked.connect(self._switch_source_runtime)
            runtime_layout.addWidget(switch_runtime_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        else:
            packaged_note = QLabel("Packaged Hub runtimes are integrated by the package provider and cannot switch to Portable mode.")
            packaged_note.setWordWrap(True)
            runtime_layout.addWidget(packaged_note)

        runtime_layout.addSpacing(10)
        startup_heading = QLabel("Startup")
        startup_heading_font = startup_heading.font()
        startup_heading_font.setBold(True)
        startup_heading.setFont(startup_heading_font)
        runtime_layout.addWidget(startup_heading)

        self.lazy_checkbox = QCheckBox("Lazy-load utilities")
        self.lazy_checkbox.setChecked(bool(config.lazy_load_utilities))
        runtime_layout.addWidget(self.lazy_checkbox)

        startup_note = QLabel(
            "When enabled, applets are imported only when first opened. "
            "When disabled, enabled applets are initialized during LinSpectacles startup. "
            "Live applets activate only while selected. Boot and package inventories remain Scan-only. "
            "Enabled Hub Modules activate at Hub startup because they contribute host features rather than sidebar views."
        )
        startup_note.setWordWrap(True)
        runtime_layout.addWidget(startup_note)

        runtime_layout.addSpacing(10)
        source_heading = QLabel("Preferred Component Source")
        source_heading_font = source_heading.font()
        source_heading_font.setBold(True)
        source_heading.setFont(source_heading_font)
        runtime_layout.addWidget(source_heading)

        source_note = QLabel(
            "When both User and Package-managed copies of the same applet or Hub Module are available, "
            "this preference chooses the copy used for normal Hub presentation and module runtime selection. "
            "Configuration continues to show both installed copies. Versions are reported but are never used "
            "to choose a winner."
        )
        source_note.setWordWrap(True)
        runtime_layout.addWidget(source_note)

        self.prefer_manual_components = QRadioButton("Prefer User")
        self.prefer_managed_components = QRadioButton("Prefer Package-managed")
        if self.config.preferred_component_source == "managed":
            self.prefer_managed_components.setChecked(True)
        else:
            self.prefer_manual_components.setChecked(True)
        runtime_layout.addWidget(self.prefer_manual_components)
        runtime_layout.addWidget(self.prefer_managed_components)

        runtime_layout.addStretch(1)
        tabs.addTab(runtime_page, "Runtime")

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
            "Hub Module enablement belongs to the logical module, not to individual installed copies. "
            "When both User and Package-managed implementations exist, the Preferred Component Source setting chooses "
            "which implementation runs. Installed copies remain visible below for provenance and User-copy management. "
            "Dashboard visibility and ordering are shared by logical module identity."
        )
        modules_note.setWordWrap(True)
        modules_note.setStyleSheet("color:#b8b8b8;")
        modules_layout.addWidget(modules_note)

        self.module_table = QTableWidget(0, 7)
        self.module_table.setHorizontalHeaderLabels(
            ["Hub Module", "Installed", "Enabled", "Dashboard", "Runtime Source", "Version", "Editor"]
        )
        self.module_table.verticalHeader().setVisible(False)
        self.module_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.module_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.module_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        module_header = self.module_table.horizontalHeader()
        module_header.setStretchLastSection(False)
        module_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, 7):
            module_header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        module_header.setSectionsClickable(True)
        module_header.setSortIndicatorShown(False)
        self._module_sort_column = None
        self._module_sort_order = Qt.SortOrder.AscendingOrder
        module_header.sectionClicked.connect(self._sort_module_table)
        self.module_table.setMinimumHeight(120)
        modules_layout.addWidget(self.module_table, 1)

        copies_heading = QLabel("Installed Copies")
        copies_heading_font = copies_heading.font()
        copies_heading_font.setBold(True)
        copies_heading.setFont(copies_heading_font)
        modules_layout.addWidget(copies_heading)

        self.module_copies_table = QTableWidget(0, 4)
        self.module_copies_table.setHorizontalHeaderLabels(
            ["Owner", "Version", "Source", "Path"]
        )
        self.module_copies_table.verticalHeader().setVisible(False)
        self.module_copies_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.module_copies_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.module_copies_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        copies_header = self.module_copies_table.horizontalHeader()
        copies_header.setStretchLastSection(True)
        copies_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        copies_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        copies_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        copies_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.module_copies_table.setMaximumHeight(130)
        modules_layout.addWidget(self.module_copies_table)

        module_controls = QHBoxLayout()
        add_module_btn = QPushButton("Add Module...")
        self.remove_module_btn = QPushButton("Remove")
        self.module_up_btn = QPushButton("Up")
        self.module_down_btn = QPushButton("Down")
        refresh_module_btn = QPushButton("Refresh")
        open_modules_btn = QPushButton("Open User Modules Folder")
        add_module_btn.clicked.connect(self.add_module)
        self.remove_module_btn.clicked.connect(self.remove_module)
        self.module_up_btn.clicked.connect(lambda: self.move_selected_module(-1))
        self.module_down_btn.clicked.connect(lambda: self.move_selected_module(1))
        refresh_module_btn.clicked.connect(self.refresh_modules)
        open_modules_btn.clicked.connect(self.open_manual_module_folder)
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
        # Enabled module-owned Configuration pages are reordered immediately
        # after the canonical Modules page below.
        for contribution in other_module_pages:
            add_module_configuration_page(contribution)

        # Canonical Modules page; final tab ordering is normalized below.
        self.modules_tab_index = tabs.addTab(modules_page, "Modules")

        # ------------------------------------------------------------------
        # About — final Configuration page, following the current inspector
        # About-page convention used by Scheduler/Interrupts Inspector.
        # ------------------------------------------------------------------
        about = QWidget()
        about_layout = QVBoxLayout(about)
        about_layout.setContentsMargins(24, 20, 24, 18)
        about_layout.setSpacing(8)

        program_root = Path(getattr(parent, "program_root", Path(__file__).resolve().parents[2])).resolve()
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
            f"<a href='{ORGANIZATION_URL}'>{ORGANIZATION_ID}</a><br>"
            "<b>Configuration:</b><br>"
            f"{runtime_paths.config_file}"
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

        readme_url = QUrl.fromLocalFile(str(program_root / "README.md")).toString()
        license_url = QUrl.fromLocalFile(str(program_root / "LICENSE")).toString()
        issues_url = REPOSITORY.rstrip("/") + "/issues"
        links = QLabel(
            f"<a href='{readme_url}'>README</a> "
            "&nbsp;·&nbsp; "
            f"<a href='{license_url}'>License</a> "
            "&nbsp;·&nbsp; "
            f"<a href='{REPOSITORY}'>Repository</a> "
            "&nbsp;·&nbsp; "
            f"<a href='{issues_url}'>Issues</a>"
        )
        links.setOpenExternalLinks(True)
        links.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(links)
        about_layout.addStretch(1)
        tabs.addTab(about, "About")

        # Canonical Configuration order: Applets, Modules, optional module-owned
        # pages (for example Helpers), Runtime, Appearance, About.
        desired_pages = [applets_page, modules_page]
        seen_dynamic = set()
        for page in self.dynamic_page_widgets.values():
            page_key = id(page)
            if page_key not in seen_dynamic:
                desired_pages.append(page)
                seen_dynamic.add(page_key)
        desired_pages.extend([runtime_page, appearance_page, about])
        for target_index, page in enumerate(desired_pages):
            current_index = tabs.indexOf(page)
            if current_index >= 0 and current_index != target_index:
                tabs.tabBar().moveTab(current_index, target_index)

        self.applets_tab_index = tabs.indexOf(applets_page)
        self.modules_tab_index = tabs.indexOf(modules_page)
        self.dynamic_page_indexes = {"applets": self.applets_tab_index}
        for key, page in self.dynamic_page_widgets.items():
            self.dynamic_page_indexes[key] = tabs.indexOf(page)
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

    def choose_manual_component_location(self):
        # Compatibility surface retained for older callers. Manual component
        # storage is runtime-owned from 0.1.6 onward.
        QMessageBox.information(
            self,
            "User Component Location",
            "User component storage follows the Hub runtime: Portable uses the Hub folder; Integrated/Packaged use XDG user data.",
        )
        return False

    def _ensure_manual_location_confirmed(self):
        # Runtime mode now defines the single Manual component location.
        return True

    def _switch_source_runtime(self):
        if self.runtime_paths.packaged:
            return
        try:
            dialog = RuntimeMigrationDialog(self.runtime_paths, self.config, self)
        except Exception as exc:
            QMessageBox.critical(self, "Runtime Migration", str(exc))
            return
        if dialog.exec() != QDialog.DialogCode.Accepted or dialog.result is None:
            return

        self.runtime_migration_completed = True
        target_name = "Integrated" if dialog.result.target_mode == "integrated" else "Portable"
        main_path = self.runtime_paths.program_root / "main.py"
        result = QProcess.startDetached(sys.executable, [str(main_path)])
        started = bool(result[0]) if isinstance(result, tuple) else bool(result)
        if not started:
            QMessageBox.warning(
                self,
                "Runtime Migration",
                f"Migration to {target_name} completed, but LinSpectacles could not restart automatically. Please launch it again manually.",
            )
        self.accept()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _save_startup(self):
        value = self.lazy_checkbox.isChecked()
        if value != self.config.lazy_load_utilities:
            self.config.lazy_load_utilities = value
            self.changed = True

    def _save_component_source_preference(self):
        value = "managed" if self.prefer_managed_components.isChecked() else "manual"
        if value != self.config.preferred_component_source:
            self.config.preferred_component_source = value
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
        self._save_component_source_preference()
        self.accept()

    def closeEvent(self, event):
        allowed, message = self._can_close_dynamic_pages()
        if not allowed:
            QMessageBox.information(self, "Configuration", message or "Wait for the current module operation to finish before closing Configuration.")
            event.ignore()
            return
        self._save_startup()
        self._save_appearance()
        self._save_component_source_preference()
        super().closeEvent(event)

