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
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..paths import RuntimePaths

class ManualComponentLocationDialog(QDialog):
    """Choose the single manual component source used by this Hub."""

    def __init__(self, runtime_paths, config, parent=None, first_time=False):
        super().__init__(parent)
        self.runtime_paths = runtime_paths
        self.config = config
        self.setWindowTitle("User Component Location — LinSpectacles")
        self.setMinimumWidth(620)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        intro = QLabel(
            ("Choose where LinSpectacles should read and manage manually installed applets and Hub Modules. "
             "Only this manual location and the known managed/system location are discovered. ")
            + ("This choice is required before the first manual installation." if first_time else "You can change this at any time.")
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        self.shared_radio = QRadioButton("XDG user location")
        self.shared_path = QLabel(str(runtime_paths.shared_root))
        self.shared_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(self.shared_radio)
        root.addWidget(self.shared_path)

        self.portable_radio = QRadioButton("This Hub's portable folder")
        self.portable_radio.setEnabled(not runtime_paths.packaged)
        self.portable_path = QLabel(
            str(runtime_paths.portable_root) if not runtime_paths.packaged
            else "Unavailable for a packaged Hub"
        )
        self.portable_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(self.portable_radio)
        root.addWidget(self.portable_path)

        self.custom_radio = QRadioButton("Custom location")
        root.addWidget(self.custom_radio)
        custom_row = QHBoxLayout()
        self.custom_edit = QLineEdit(config.manual_component_custom_root)
        self.custom_edit.setPlaceholderText("Choose an absolute directory...")
        browse = QPushButton("Browse...")
        browse.clicked.connect(self._browse_custom)
        custom_row.addWidget(self.custom_edit, 1)
        custom_row.addWidget(browse)
        root.addLayout(custom_row)

        note = QLabel(
            "Add/Remove/Open Folder operate only on the selected manual location. "
            "Package-managed components are discovered separately and remain owned by their package provider. "
            "Changing this setting does not move or delete existing component folders."
        )
        note.setWordWrap(True)
        root.addWidget(note)

        current = config.manual_component_location
        if current == "portable" and not runtime_paths.packaged:
            self.portable_radio.setChecked(True)
        elif current == "custom":
            self.custom_radio.setChecked(True)
        else:
            self.shared_radio.setChecked(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_checked)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _browse_custom(self):
        start = self.custom_edit.text().strip() or str(Path.home())
        directory = QFileDialog.getExistingDirectory(None, "Choose User Component Location", start)
        if directory:
            self.custom_edit.setText(directory)
            self.custom_radio.setChecked(True)

    def selected_values(self):
        if self.portable_radio.isChecked():
            return "portable", ""
        if self.custom_radio.isChecked():
            return "custom", self.custom_edit.text().strip()
        return "shared", ""

    def _accept_checked(self):
        location, custom_root = self.selected_values()
        if location == "custom":
            try:
                self.runtime_paths.manual_root(location, custom_root)
            except Exception as exc:
                QMessageBox.warning(self, "User Component Location", str(exc))
                return
        self.accept()
