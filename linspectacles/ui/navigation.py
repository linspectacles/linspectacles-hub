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

from .common import (
    DASHBOARD_ID, NAV_META_ROLE, NAV_LOGICAL_ROLE, component_ownership_label,
    component_provider_label,
)

class AppletNavDelegate(QStyledItemDelegate):
    """Compact two-line applet identity without inflating sidebar rows."""

    def sizeHint(self, option, index):
        base = super().sizeHint(option, index)
        meta = str(index.data(NAV_META_ROLE) or "").strip()
        return QSize(base.width(), 40 if meta else 30)

    def paint(self, painter, option, index):
        title = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        meta = str(index.data(NAV_META_ROLE) or "").strip()

        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.text = ""
        style = opt.widget.style() if opt.widget is not None else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)

        painter.save()
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        heading = not bool(index.flags() & Qt.ItemFlag.ItemIsSelectable) and not meta
        title_color = QColor("#ffffff" if selected else ("#007acc" if heading else "#dcdcdc"))
        meta_color = QColor("#e7f3fb" if selected else "#9b9b9b")
        rect = option.rect.adjusted(9, 1, -7, -1)

        title_font = QFont(option.font)
        base_size = title_font.pointSizeF() if title_font.pointSizeF() > 0 else 10.0
        title_font.setPointSizeF(max(10.0, base_size + 0.5))
        title_font.setBold(True)

        if not meta:
            painter.setFont(title_font)
            painter.setPen(title_color)
            painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, title)
            painter.restore()
            return

        meta_font = QFont(title_font)
        meta_font.setBold(False)
        meta_font.setPointSizeF(max(8.0, title_font.pointSizeF() - 2.0))
        title_rect = rect.adjusted(0, 1, 0, -15)
        meta_rect = rect.adjusted(0, 19, 0, 0)
        painter.setFont(title_font)
        painter.setPen(title_color)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, title)
        painter.setFont(meta_font)
        painter.setPen(meta_color)
        painter.drawText(meta_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, meta)
        painter.restore()

class NavigationHost:
    def setup_sidebar(self):
        sidebar = QFrame()
        self.sidebar = sidebar
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
        self.applet_search.textChanged.connect(
            lambda _text: self.rebuild_sidebar(select_id=self.current_id(), rediscover=False)
        )
        layout.addWidget(self.applet_search)

        self.nav_list = QListWidget()
        self.nav_list.setItemDelegate(AppletNavDelegate(self.nav_list))
        self.nav_list.setStyleSheet(
            """
            QListWidget { background-color:#252526; border:none; color:#dcdcdc; font-size:10pt; }
            QListWidget::item { padding:2px 8px; border-radius:4px; margin-bottom:2px; }
            QListWidget::item:selected { background-color:#007acc; color:#fff; }
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

        self.contextual_action_container = QWidget()
        self.contextual_action_layout = QVBoxLayout(self.contextual_action_container)
        self.contextual_action_layout.setContentsMargins(0, 0, 0, 0)
        self.contextual_action_layout.setSpacing(4)
        self.contextual_action_container.setVisible(False)
        layout.addWidget(self.contextual_action_container)

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

    def rebuild_sidebar(self, select_id=None, rediscover=True):
        current = select_id or self.current_id() or DASHBOARD_ID
        if rediscover:
            self.registry.discover()
        enabled = self.enabled_manifests()
        presented = self.preferred_applet_manifests(enabled)
        self.manifest_by_id = {manifest.instance_id: manifest for manifest in presented}

        # If a preference change hides the currently selected physical copy,
        # stay on the same logical applet by selecting its newly preferred copy.
        if current != DASHBOARD_ID and current not in self.manifest_by_id:
            old_manifest = self.registry.manifests.get(str(current))
            if old_manifest is not None:
                replacement = next(
                    (m for m in presented if m.applet_id == old_manifest.applet_id),
                    None,
                )
                if replacement is not None:
                    current = replacement.instance_id

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

        query = self.applet_search.text().strip().casefold() if hasattr(self, "applet_search") else ""
        records = []
        for manifest in presented:
            # Organizer metadata remains keyed by logical applet identity and is
            # therefore shared by User/Package-managed copies of the same applet.
            entry = model.get(manifest.applet_id, {}) if isinstance(model, dict) else {}
            group = str(entry.get("group", "Unsorted") or "Unsorted")
            tags = [str(tag) for tag in entry.get("tags", [])] if isinstance(entry.get("tags", []), (list, tuple)) else []
            favorite = bool(entry.get("favorite", False))
            search_parts = [manifest.name, manifest.applet_id, manifest.version, manifest.source]
            if self.navigation_provider is not None:
                search_parts.extend([group, *tags])
            haystack = " ".join(search_parts).casefold()
            if query and query not in haystack:
                continue
            records.append({"manifest": manifest, "group": group, "favorite": favorite})

        self.nav_list.blockSignals(True)
        self.nav_list.clear()

        def add_manifest_item(manifest, prefix=""):
            item = QListWidgetItem(prefix + manifest.name)
            item.setData(Qt.ItemDataRole.UserRole, manifest.instance_id)
            item.setData(NAV_LOGICAL_ROLE, manifest.applet_id)
            item.setData(NAV_META_ROLE, f"{manifest.version} · {component_ownership_label(manifest)}")
            item.setToolTip(
                f"{manifest.name} {manifest.version}\n"
                f"{component_ownership_label(manifest)} · {component_provider_label(manifest, self.runtime_paths)}\n"
                f"{manifest.directory}"
            )
            self.nav_list.addItem(item)

        if self.navigation_provider is None:
            for record in sorted(
                records,
                key=lambda r: (
                    r["manifest"].name.casefold(),
                    r["manifest"].applet_id,
                    0 if r["manifest"].origin == "manual" else 1,
                    r["manifest"].version,
                ),
            ):
                add_manifest_item(record["manifest"])
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
                heading.setData(NAV_META_ROLE, "")
                heading_font = heading.font()
                heading_font.setBold(True)
                heading.setFont(heading_font)
                heading.setForeground(QColor("#007acc"))
                self.nav_list.addItem(heading)
                for record in sorted(
                    grouped[group],
                    key=lambda r: (
                        r["manifest"].name.casefold(),
                        0 if r["manifest"].origin == "manual" else 1,
                        r["manifest"].version,
                    ),
                ):
                    add_manifest_item(record["manifest"])

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
                self._set_context_window_title("Dashboard")
        elif selected:
            if hasattr(self, "dashboard_btn"):
                self.dashboard_btn.setChecked(False)
        elif not rediscover and current in self.manifest_by_id:
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
                self._set_context_window_title("Dashboard")

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

