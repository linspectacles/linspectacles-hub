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

from .. import APP_NAME, ORGANIZATION_ID, ORGANIZATION_URL, REPOSITORY, VERSION
from ..paths import RuntimePaths

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
        issues_url = REPOSITORY.rstrip("/") + "/issues"
        links = QLabel(
            f"<a href='{readme_url}'>README</a> &nbsp;·&nbsp; "
            f"<a href='{license_url}'>License</a> &nbsp;·&nbsp; "
            f"<a href='{REPOSITORY}'>Repository</a> &nbsp;·&nbsp; "
            f"<a href='{issues_url}'>Issues</a>"
        )
        links.setOpenExternalLinks(True)
        links.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(links)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)
