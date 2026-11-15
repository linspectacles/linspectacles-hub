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

from .common import DASHBOARD_ID, component_ownership_label

class DashboardHost:
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

        self.dashboard_coverage = QTableWidget(0, 5)
        self.dashboard_coverage.setHorizontalHeaderLabels(["Applet", "Version", "Source", "Availability", "Session"])
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

        manifests = sorted(
            self.registry.manifests.values(),
            key=lambda m: (m.name.casefold(), m.applet_id, 0 if m.origin == "manual" else 1, m.version),
        )
        enabled_only = bool(
            hasattr(self, "coverage_enabled_only") and self.coverage_enabled_only.isChecked()
        )
        loaded_only = bool(
            hasattr(self, "coverage_loaded_only") and self.coverage_loaded_only.isChecked()
        )
        visible_manifests = [
            manifest
            for manifest in manifests
            if (not enabled_only or self.config.applet_enabled(manifest.instance_id, manifest.applet_id))
            and (not loaded_only or manifest.instance_id in self.pages)
        ]
        coverage_columns = self._ordered_dashboard_contributions(self.module_coverage_columns)
        annotation_providers = self._ordered_dashboard_contributions(self.module_coverage_annotations)
        headers = ["Applet", "Version", "Source", "Availability", "Session"]
        headers.extend(label for _module_id, label, _provider in coverage_columns)
        if annotation_providers:
            # API v3 compatibility only.  New modules should contribute a named
            # column through API v4 rather than using a generic Summary cell.
            headers.append("Summary")
        self.dashboard_coverage.setColumnCount(len(headers))
        self.dashboard_coverage.setHorizontalHeaderLabels(headers)
        self.dashboard_coverage.setRowCount(len(visible_manifests))

        for row, manifest in enumerate(visible_manifests):
            enabled = self.config.applet_enabled(manifest.instance_id, manifest.applet_id)
            loaded = manifest.instance_id in self.pages
            record = {
                "id": manifest.applet_id,
                "instance_id": manifest.instance_id,
                "name": manifest.name,
                "version": manifest.version,
                "source": manifest.source,
                "origin": manifest.origin,
                "enabled": enabled,
                "loaded": loaded,
            }
            values = [
                manifest.name,
                manifest.version,
                component_ownership_label(manifest),
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
        enabled_count = sum(1 for m in manifests if self.config.applet_enabled(m.instance_id, m.applet_id))
        loaded_count = sum(1 for m in manifests if m.instance_id in self.pages)
        self.dashboard_installed_status.setText(f"Installed applets: {installed}")
        self.dashboard_enabled_status.setText(f"Enabled applets: {enabled_count}")
        self.dashboard_loaded_status.setText(f"Loaded this session: {loaded_count}")
        self.dashboard_lazy_status.setText(
            "Lazy loading: " + ("Enabled" if self.config.lazy_load_utilities else "Disabled")
        )
        module_manifests = self.module_registry.ordered(self.config.module_order)
        enabled_module_instances, _ambiguous_modules = self._resolved_module_enablement(module_manifests)
        module_enabled_count = len(enabled_module_instances)
        module_installed_count = len({m.module_id for m in module_manifests})
        self.dashboard_modules_status.setText(
            f"Hub modules: {module_enabled_count} enabled / {module_installed_count} installed"
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
        self._set_context_window_title("Dashboard")
        self.status_lbl.setText("Status: Active View: Dashboard")
        self.module_events.emit("selection.changed", applet_id=None, label="Dashboard")

