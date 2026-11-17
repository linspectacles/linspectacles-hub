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

from . import (APP_NAME, ORGANIZATION_ID, ORGANIZATION_URL, REPOSITORY, VERSION)
from .applets import AppletRegistry
from .config import PortableConfig
from .modules import EventBus, ModuleRegistry
from .migration import copy_legacy_manual_root
from .paths import RuntimePaths
from .styles import DARK_STYLESHEET
from .ui.common import DASHBOARD_ID
from .ui.configuration_dialog import ConfigurationDialog
from .ui.navigation import AppletNavDelegate, NavigationHost
from .ui.dashboard import DashboardHost
from .module_host import ModuleHost
from .applet_host import AppletHost

class Linspectacles(NavigationHost, DashboardHost, ModuleHost, AppletHost, QMainWindow):
    def _set_context_window_title(self, context):
        """Keep the Qt window title contextual; desktop identity stays LinSpectacles Hub."""
        label = str(context or "").strip() or "Dashboard"
        self.setWindowTitle(label)

    def __init__(self, program_root, integrated_source=False):
        super().__init__()
        self.program_root = Path(program_root).resolve()
        self.runtime_paths = RuntimePaths.for_program(
            self.program_root, integrated_source=integrated_source
        )
        self.runtime_paths.ensure_config_dirs()
        self._set_context_window_title("Dashboard")
        self.resize(1350, 900)

        icon_path = self.program_root / "assets" / "linspectacles-icon.png"
        if icon_path.is_file():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.config = PortableConfig(self.program_root, self.runtime_paths.config_file)
        self._offer_legacy_manual_location_transition()
        self.runtime_paths.ensure_active_manual_dirs()
        manual_source = self.runtime_paths.active_manual_source_label
        manual_source_key = self.runtime_paths.active_manual_source_key
        self.registry = AppletRegistry(
            self.program_root,
            self.runtime_paths.active_manual_applet_store,
            self.runtime_paths.system_applet_store,
            primary_source=manual_source,
            primary_key=manual_source_key,
        )
        self.registry.discover()
        self.config.migrate_legacy_applet_settings(self.registry.manifests.values())
        self.module_registry = ModuleRegistry(
            self.program_root,
            self.runtime_paths.active_manual_module_store,
            self.runtime_paths.system_module_store,
            primary_source=manual_source,
            primary_key=manual_source_key,
        )
        self.module_registry.discover()
        self.config.migrate_legacy_module_states(self.module_registry.manifests.values())
        self.module_events = EventBus()
        self.module_contexts = {}
        self.active_modules = {}
        self.active_module_directories = {}
        self.module_configuration_pages = []
        self.module_applets_extensions = []
        self.module_applets_columns = []
        self.module_applets_actions = []
        self.module_suite_state_items = []
        self.module_coverage_annotations = []
        self.module_coverage_columns = []
        self.module_contextual_actions = []
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
            self.setStyleSheet(DARK_STYLESHEET)

        self.setup_menu()
        self.setup_sidebar()
        self.setup_content_area()
        if app is not None:
            app.installEventFilter(self)
        self.rebuild_sidebar(select_id=DASHBOARD_ID)
        self.sync_suite_modules(show_errors=False)

        if not self.config.lazy_load_utilities:
            self.initialize_enabled_applets()

    def _offer_legacy_manual_location_transition(self):
        """Protect 0.1.5 users whose explicit Manual root differs from 0.1.6 runtime ownership."""
        if not self.config.manual_component_location_confirmed:
            return
        try:
            legacy_root = self.runtime_paths.manual_root(
                self.config.manual_component_location,
                self.config.manual_component_custom_root,
            ).resolve()
            target_root = self.runtime_paths.active_manual_root.resolve()
        except Exception:
            self.config.data["manual_component_location_confirmed"] = False
            self.config.save()
            return
        if legacy_root == target_root:
            self.config.data["manual_component_location_confirmed"] = False
            self.config.save()
            return

        answer = QMessageBox.question(
            self,
            "User Component Location Updated",
            "LinSpectacles 0.1.6 made the User component location follow Hub runtime mode.\n\n"
            f"Previous location: {legacy_root}\n"
            f"Current runtime location: {target_root}\n\n"
            "Copy applets and Hub Modules from the previous location into the current runtime location? "
            "Existing destination components will not be overwritten and the previous location will remain untouched.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if answer == QMessageBox.StandardButton.Yes:
            try:
                result = copy_legacy_manual_root(legacy_root, target_root)
                skipped = list(result["skipped_applets"]) + list(result["skipped_modules"])
                if skipped:
                    QMessageBox.information(
                        self,
                        "User Components Copied",
                        "Copy completed. Existing destination component folders were skipped: " + ", ".join(sorted(skipped)),
                    )
            except Exception as exc:
                QMessageBox.warning(self, "User Component Migration", str(exc))
                return
        self.config.data["manual_component_location_confirmed"] = False
        self.config.save()

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

        self.find_applet_action = QAction("Find Applet", self)
        self.find_applet_action.setShortcut("Ctrl+F")
        self.find_applet_action.triggered.connect(self._focus_applet_search)
        self.addAction(self.find_applet_action)

        self.dashboard_action = QAction("Dashboard", self)
        self.dashboard_action.setShortcut("Ctrl+W")
        self.dashboard_action.triggered.connect(self.show_dashboard)
        self.addAction(self.dashboard_action)

        self.launch_standalone_action = QAction("Launch Standalone", self)
        self.launch_standalone_action.setShortcut("F5")
        self.launch_standalone_action.setEnabled(False)
        self.launch_standalone_action.triggered.connect(self.launch_current_applet_standalone)
        self.addAction(self.launch_standalone_action)

        self.documentation_action = QAction("Documentation", self)
        self.documentation_action.setShortcut("F1")
        self.documentation_action.triggered.connect(self.open_documentation)
        self.addAction(self.documentation_action)

        # 0.2.0 removes the visible Help/Tools menus.  Hub commands remain
        # available through their documented shortcuts and Configuration.
        self.menuBar().setVisible(False)

    def open_documentation(self):
        readme = self.program_root / "README.md"
        if readme.is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(readme)))
            return
        QDesktopServices.openUrl(
            QUrl(REPOSITORY)
        )

    def _focus_applet_search(self):
        if not hasattr(self, "applet_search"):
            return
        self.applet_search.setFocus()
        self.applet_search.selectAll()

    def eventFilter(self, watched, event):
        # Type-to-search is intentionally conservative: it is active on the
        # Dashboard/sidebar navigation surfaces, never while an inspector has
        # keyboard focus. This avoids stealing ordinary applet keystrokes.
        if event.type() == QEvent.Type.KeyPress and self.isActiveWindow():
            if QApplication.activeModalWidget() is None:
                modifiers = event.modifiers()
                text = event.text()
                focus = QApplication.focusWidget()
                # Dashboard modules may own text-entry controls (for example
                # Encyclopedia search).  Hub type-to-search must never steal
                # printable input from a widget that already accepts text.
                text_entry_context = bool(
                    focus is not None
                    and focus.testAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled)
                )
                dashboard_context = self.current_id() == DASHBOARD_ID
                sidebar_context = focus in {
                    getattr(self, "nav_list", None),
                    getattr(self, "dashboard_btn", None),
                    getattr(self, "launch_standalone_btn", None),
                    getattr(self, "contextual_action_container", None),
                }
                if (
                    text
                    and text.isprintable()
                    and not text.isspace()
                    and not (modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.MetaModifier))
                    and focus is not getattr(self, "applet_search", None)
                    and not text_entry_context
                    and (dashboard_context or sidebar_context)
                ):
                    self.applet_search.setFocus()
                    self.applet_search.insert(text)
                    return True
        return super().eventFilter(watched, event)

    def closeEvent(self, event):
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        for instance_id in list(self.active_modules):
            self._deactivate_suite_module(instance_id)
        super().closeEvent(event)

    def open_configuration(self, initial_page_id=None):
        previous_lazy = self.config.lazy_load_utilities
        current = self.current_id()
        module_pages = sorted(
            list(self.module_configuration_pages),
            key=lambda item: (self._module_rank(item[0]), str(item[2]).casefold()),
        )
        applet_extensions = sorted(
            list(self.module_applets_extensions),
            key=lambda item: (self._module_rank(item[0]), str(item[2]).casefold()),
        )
        applet_columns = sorted(
            list(self.module_applets_columns),
            key=lambda item: (self._module_rank(item[0]), str(item[2]).casefold()),
        )
        applet_actions = sorted(
            list(self.module_applets_actions),
            key=lambda item: (self._module_rank(item[0]), str(item[2]).casefold()),
        )
        dialog = ConfigurationDialog(
            self.registry, self.module_registry, self.config, self,
            module_pages=module_pages, applet_extensions=applet_extensions,
            applet_columns=applet_columns, applet_actions=applet_actions,
            initial_page_id=initial_page_id,
        )
        dialog.exec()
        if getattr(dialog, "runtime_migration_completed", False):
            return

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

def run(program_root, integrated_source=False):
    app = QApplication(sys.argv)
    app.setApplicationName("LinSpectacles Hub")
    app.setApplicationDisplayName("LinSpectacles Hub")
    app.setDesktopFileName("linspectacles-hub")
    app.setOrganizationName(ORGANIZATION_ID)
    icon_path = Path(program_root).resolve() / "assets" / "linspectacles-icon.png"
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))
    suite = Linspectacles(program_root, integrated_source=integrated_source)
    suite.show()
    return app.exec()
