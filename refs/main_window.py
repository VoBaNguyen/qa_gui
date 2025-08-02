"""
Main window for QA MRVL Techlib Tool.
Initializes the main UI, tabs, and handles settings management and status updates.
"""

import os
import sys
import json
import logging
import traceback
from io import StringIO
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QStatusBar,
    QProgressBar, QHBoxLayout, QPushButton, QFileDialog, QMessageBox, QDesktopWidget, QLabel, QStyle
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from frontend.tabs.tab_create_package import CreatePackageTab
from frontend.tabs.tab_compare import CompareTab
from frontend.tabs.settings_manager import SettingsManager
from frontend.tabs.tab_debug import DebugTab
from utils import file_utils as utils

logger = logging.getLogger(__name__)

class QAToolWindow(QMainWindow):
    """
    Main window for the QA MRVL Techlib Tool.
    """
    def __init__(self) -> None:
        """
        Initialize the main window and UI components.
        """
        super().__init__()
        self.setWindowTitle("QA MRVL Techlib Tool")
        self.log_stream = StringIO()
        sys.stdout = self.log_stream  # Redirect stdout to capture logs
        self.init_ui()

    def init_ui(self) -> None:
        """
        Initialize the user interface with tabs and buttons.
        """
        self.resize(1400, 800)
        self.center_window()

        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Tabs
        self.tabs = QTabWidget()
        self.tab_create_package = CreatePackageTab(self)
        self.tab_compare = CompareTab(self)
        # DebugTab can be initialized with db_path=None
        self.tab_debug = DebugTab(self, db_path=None)
        self.tabs.addTab(self.tab_create_package, "Create Package")
        self.tabs.addTab(self.tab_compare, "Compare Packages")
        self.tabs.addTab(self.tab_debug, "Debug")
        main_layout.addWidget(self.tabs)

        # Connect CreatePackageTab's techlib_callback_signal to main window's techlib_callback
        self.tab_create_package.pdk_versions_loaded.connect(self.update_pdk_versions)
        self.tab_create_package.techlib_callback_signal.connect(self.techlib_callback)

        # Bottom buttons
        btn_hbox = QHBoxLayout()
        btn_hbox.addStretch()
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.load_btn = QPushButton("Load Settings")
        self.load_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogToParent))
        for btn in [self.save_btn, self.load_btn]:
            btn_hbox.addWidget(btn)
        main_layout.addLayout(btn_hbox)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Status: Idle")
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.status_bar.addWidget(self.status_label)
        self.status_bar.addWidget(self.progress)

        # Connect signals
        self.save_btn.clicked.connect(self.save_settings)
        self.load_btn.clicked.connect(self.prompt_load_settings)


        # Load default settings
        default_settings = "./last_qa_settings.json"
        if os.path.isfile(default_settings):
            logger.info(f"Loading default settings from {default_settings}")
            self.status_label.setText("Status: Loading default settings...")
            success, message = SettingsManager.load_settings(self, default_settings)
            # Always update PDK config path after loading settings
            techlib = self.tab_create_package.widgets['tech_combo'].currentText()
            self.techlib_callback(techlib)
            if success:
                self.resolve_paths()
            self.status_label.setText(f"Status: {message}")

    def center_window(self) -> None:
        """
        Center the window on the primary monitor.
        """
        frame_geometry = self.frameGeometry()
        screen = QDesktopWidget().screenGeometry()
        frame_geometry.moveCenter(screen.center())
        self.move(frame_geometry.topLeft())

    def update_pdk_versions(self, versions) -> None:
        """
        Update PDK versions in the Compare tab.

        Parameters
        ----------
        versions : list
            List of PDK versions to update.
        """
        self.tab_create_package.update_pdk_versions(versions)
        self.tab_compare.update_pdk_versions(versions)
        self.status_label.setText(f"Status: Loaded {len(versions)} PDK versions")

    def save_settings(self) -> None:
        """
        Save settings to a user-specified JSON file.
        """
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Settings", "./qa_settings.json", "JSON Files (*.json)")
        if file_name:
            success, message = SettingsManager.save_settings(self, file_name)
            self.status_label.setText(f"Status: {message}")
            if not success:
                QMessageBox.critical(self, "Error", message)

    def prompt_load_settings(self) -> None:
        """
        Prompt user to select a JSON file and load settings.
        """
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Settings", ".", "JSON Files (*.json)")
        if file_name:
            success, message = SettingsManager.load_settings(self, file_name)
            self.status_label.setText(f"Status: {message}")
            if not success:
                QMessageBox.critical(self, "Error", message)
            else:
                # Ensure paths are resolved and log level is updated
                self.resolve_paths()

    def resolve_paths(self) -> None:
        """
        Resolve relative paths in settings using QA_MRVL_TECH_CWD environment variable.
        Warn user if any required file is missing.
        """
        base_dir = os.getenv('QA_MRVL_TECH_CWD', os.path.dirname(os.path.abspath(__file__)))  # Use env var or fallback to script dir
        missing_files = []
        for tab in [self.tab_create_package, self.tab_compare]:
            settings = tab.get_settings()

            def resolve_and_validate_path(path, must_exist=False):
                if path and not os.path.isabs(path):
                    resolved_path = os.path.normpath(os.path.join(base_dir, path))
                    valid, message = utils.validate_path(resolved_path, must_exist=must_exist)
                    if not valid:
                        logger.warning(f"Resolved path invalid: {path} -> {resolved_path}: {message}")
                        if must_exist:
                            missing_files.append(resolved_path)
                    return resolved_path
                if must_exist and path and not os.path.exists(path):
                    missing_files.append(path)
                return path

            # Handle CreatePackageTab settings
            if tab == self.tab_create_package:
                # Only validate enabled fields
                for key in ['cds_lib', 'qa_setting']:
                    widget = tab.widgets.get(key)
                    path = settings.get('required_settings', {}).get(key, '')
                    if widget is not None and widget.isEnabled() and path:
                        settings['required_settings'][key] = resolve_and_validate_path(path, must_exist=True)
                for key in ['run_dir', 'cdsinit']:
                    widget = tab.widgets.get(key)
                    path = settings.get('common_settings', {}).get(key, '')
                    if widget is not None and widget.isEnabled() and path:
                        settings['common_settings'][key] = resolve_and_validate_path(path, must_exist=False)
                if settings.get('required_settings', {}).get('qa_types', {}).get('DRC', False):
                    for key in ['proj_mpv', 'mpvopts_drc', 'runcalx_version']:
                        widget = tab.drc_widgets.get(key)
                        path = settings.get('drc_settings', {}).get(key, '')
                        if widget is not None and widget.isEnabled() and path:
                            settings['drc_settings'][key] = resolve_and_validate_path(path, must_exist=True)
            # Handle CompareTab settings
            else:
                # Only validate enabled fields
                for key in ['exclude_layers', 'run_dir']:
                    widget = tab.widgets.get(key)
                    path = settings.get('qa_settings', {}).get(key, '')
                    if widget is not None and widget.isEnabled() and path:
                        settings['qa_settings'][key] = resolve_and_validate_path(path, must_exist=False)
                for package in ['golden', 'alpha']:
                    package_settings = settings.get(package, {})
                    keys = ['path', 'cdf', 'ta', 'cds_lib']
                    if package == 'golden':
                        keys.append('waived_rules')
                    else:
                        keys.append('failed_rules')
                    for key in keys:
                        widget_key = f"{package}_{key}" if f"{package}_{key}" in tab.widgets else key
                        widget = tab.widgets.get(widget_key)
                        path = package_settings.get(key, '')
                        if widget is not None and widget.isEnabled() and path:
                            settings[package][key] = resolve_and_validate_path(path, must_exist=True)

            # Process caches (no UI, keep as is)
            for key in ['QA_MRVL_DEBUG_LOG']:
                path = settings.get('caches', {}).get(key, '')
                if path:
                    settings['caches'][key] = resolve_and_validate_path(path, must_exist=False)

            tab.set_settings(settings)

        if missing_files:
            QMessageBox.warning(self, "Missing Files", f"The following required files are missing:\n" + '\n'.join(missing_files))

    def assign_debug_db(self, db_path) -> None:
        """
        Assign the cache_db path to DebugTab after a run.

        Parameters
        ----------
        db_path : str
            The database path to assign to the DebugTab.
        """
        self.tab_debug.set_db_path(db_path)

    def techlib_callback(self, techlib: str):
        """
        Central techlib change handler. Auto-fills fields in tabs based on techlib selection.
        """
        from config import QA_MRVL_TECH, SUPPORTED_TECHLIBS
        from pathlib import Path
        import re
        # Set PDK config path in Create tab
        pdk_path = f"{QA_MRVL_TECH}/backend/pdk_configs/config_{techlib}.yaml"
        if hasattr(self.tab_create_package, 'widgets') and 'pdk_config' in self.tab_create_package.widgets:
            self.tab_create_package.widgets['pdk_config'].setText(pdk_path)
            self.tab_create_package.load_pdk_config()
        # --- Auto-fill fields from ./<techlib> if exists ---
        tech_dir = Path(f"./{techlib}")
        if tech_dir.exists() and tech_dir.is_dir():
            # Find all files matching cds*lib
            cds_lib_files = list(tech_dir.glob("cds*lib"))
            if cds_lib_files:
                cds_lib_path = str(cds_lib_files[0].resolve())
                if hasattr(self.tab_create_package, 'widgets') and 'cds_lib' in self.tab_create_package.widgets:
                    self.tab_create_package.widgets['cds_lib'].setText(cds_lib_path)
                if hasattr(self.tab_compare, 'widgets') and 'golden_cds_lib' in self.tab_compare.widgets:
                    self.tab_compare.widgets['golden_cds_lib'].setText(cds_lib_path)
                if hasattr(self.tab_compare, 'widgets') and 'alpha_cds_lib' in self.tab_compare.widgets:
                    self.tab_compare.widgets['alpha_cds_lib'].setText(cds_lib_path)
            # Find exclude_layers.txt
            exclude_layers_path = tech_dir / "exclude_layers.txt"
            if exclude_layers_path.exists():
                if hasattr(self.tab_compare, 'widgets') and 'exclude_layers' in self.tab_compare.widgets:
                    self.tab_compare.widgets['exclude_layers'].setText(str(exclude_layers_path.resolve()))
            # Find .cdsinit
            cdsinit_path = tech_dir / ".cdsinit"
            if cdsinit_path.exists():
                if hasattr(self.tab_create_package, 'widgets') and 'cdsinit' in self.tab_create_package.widgets:
                    self.tab_create_package.widgets['cdsinit'].setText(str(cdsinit_path.resolve()))
            # Change run_dir suffix in both tabs
            for tab, run_dir_key in [
                (self.tab_create_package, 'run_dir'),
                (self.tab_compare, 'run_dir')
            ]:
                if hasattr(tab, 'widgets') and run_dir_key in tab.widgets:
                    run_dir_val = tab.widgets[run_dir_key].text()
                    if run_dir_val:
                        techlib_pattern = '|'.join([re.escape(t) for t in SUPPORTED_TECHLIBS])
                        run_dir_base = re.sub(rf'_({techlib_pattern})$', '', run_dir_val)
                        tab.widgets[run_dir_key].setText(f"{run_dir_base}_{techlib}")