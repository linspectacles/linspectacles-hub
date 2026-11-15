#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2026 brunonlinespace
# GPL-3.0-or-later

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QVBoxLayout,
)

from ..migration import build_plan, migrate_source_runtime
from ..runtime import SOURCE_INTEGRATED, SOURCE_PORTABLE


class RuntimeMigrationDialog(QDialog):
    """Review and execute one Source Portable <-> Integrated migration."""

    def __init__(self, runtime_paths, config, parent=None):
        super().__init__(parent)
        if runtime_paths.packaged:
            raise ValueError("Packaged runtimes cannot migrate Portable/Integrated mode.")
        self.runtime_paths = runtime_paths
        self.config = config
        self.target_mode = SOURCE_INTEGRATED if runtime_paths.portable else SOURCE_PORTABLE
        self.plan = build_plan(runtime_paths, self.target_mode)
        self.result = None
        self.setWindowTitle("Change Hub Runtime — LinSpectacles")
        self.setMinimumWidth(690)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        target_name = "Integrated" if self.target_mode == SOURCE_INTEGRATED else "Portable"
        current_name = "Portable" if runtime_paths.portable else "Integrated"
        heading = QLabel(f"{current_name} → {target_name}")
        heading_font = heading.font()
        heading_font.setBold(True)
        heading.setFont(heading_font)
        root.addWidget(heading)

        intro = QLabel(
            "LinSpectacles will copy configuration to the target runtime location, update desktop integration, "
            "persist the new Source runtime mode, and restart. The existing runtime files are left in place."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        rows = (
            ("Configuration", self.plan.current.config_root, self.plan.target.config_root),
            ("User applets", self.plan.current.active_manual_applet_store, self.plan.target.active_manual_applet_store),
            ("User modules", self.plan.current.active_manual_module_store, self.plan.target.active_manual_module_store),
        )
        for label_text, current, target in rows:
            label = QLabel(f"<b>{label_text}</b><br>Current: {current}<br>Target: {target}")
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            label.setWordWrap(True)
            root.addWidget(label)

        self.copy_applets = QCheckBox("Copy current User applets to the target runtime")
        self.copy_modules = QCheckBox("Copy current User Hub Modules to the target runtime")
        self.copy_applets.setChecked(True)
        self.copy_modules.setChecked(True)
        root.addWidget(self.copy_applets)
        root.addWidget(self.copy_modules)

        note = QLabel(
            "Component migration is optional. Existing destination component folders are never overwritten; "
            "conflicts are reported and can only be skipped. Configuration conflicts are handled explicitly before migration."
        )
        note.setWordWrap(True)
        root.addWidget(note)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        migrate = QPushButton("Migrate and Restart")
        migrate.setDefault(True)
        migrate.clicked.connect(self._migrate)
        buttons.addButton(migrate, QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _configuration_policy(self):
        if not self.plan.config_conflict:
            return "replace"
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle("Existing Target Configuration")
        box.setText("The target runtime already contains a LinSpectacles configuration file.")
        box.setInformativeText(
            "Use Current copies your active configuration to the target and keeps a timestamped backup of the existing target file. "
            "Keep Target leaves the existing target configuration unchanged."
        )
        use_current = box.addButton("Use Current", QMessageBox.ButtonRole.AcceptRole)
        keep_target = box.addButton("Keep Target", QMessageBox.ButtonRole.DestructiveRole)
        cancel = box.addButton(QMessageBox.StandardButton.Cancel)
        box.exec()
        clicked = box.clickedButton()
        if clicked is use_current:
            return "replace"
        if clicked is keep_target:
            return "keep"
        return None

    def _confirm_component_conflicts(self):
        conflicts = []
        if self.copy_applets.isChecked() and self.plan.applet_conflicts:
            conflicts.append("Applets: " + ", ".join(self.plan.applet_conflicts))
        if self.copy_modules.isChecked() and self.plan.module_conflicts:
            conflicts.append("Modules: " + ", ".join(self.plan.module_conflicts))
        if not conflicts:
            return True
        answer = QMessageBox.question(
            self,
            "Existing Target Components",
            "The following target components already exist and will NOT be overwritten:\n\n"
            + "\n".join(conflicts)
            + "\n\nContinue and skip these conflicts?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _migrate(self):
        policy = self._configuration_policy()
        if policy is None:
            return
        if not self._confirm_component_conflicts():
            return
        # Flush the current in-memory settings before the config file is copied.
        if not self.config.save():
            QMessageBox.critical(self, "Runtime Migration", "Could not save the current LinSpectacles configuration.")
            return
        try:
            self.result = migrate_source_runtime(
                self.plan,
                copy_applets=self.copy_applets.isChecked(),
                copy_modules=self.copy_modules.isChecked(),
                config_policy=policy,
                skip_component_conflicts=True,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Runtime Migration", str(exc))
            return
        self.accept()
