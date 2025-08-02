"""
Module for the Create Package tab in QA MRVL Techlib Tool.
Provides UI and logic for creating QA packages, including settings management and job control.
"""

import os
import sys
import json
import logging
import threading
import traceback
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Union, List
import yaml
import psutil  # For process management
import signal  # For os.kill fallback
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget, QGroupBox, QFormLayout, QLineEdit, QPushButton, QApplication,
    QComboBox, QHBoxLayout, QRadioButton, QCheckBox, QFileDialog, QLabel, QMessageBox, QVBoxLayout, QStyle, QButtonGroup,
    QDialog, QTextEdit
)
from PyQt5.QtGui import QIcon, QIntValidator
from tabulate import tabulate
from pprint import pformat
from utils import file_utils as utils
from utils import enum
from utils.template_renderer import TemplateRenderer
from backend.python.models.database import Database
from frontend.tabs.settings_manager import SettingsManager
from config import QA_MRVL_TECH, TEMPLATE_DIR_FE, LICENSE_FEATURES, SUPPORTED_TECHLIBS
from utils.send_mail import send_jobs_email

logger = logging.getLogger(__name__)

VIRTUOSO_CMD_TEMPLATE = (
    "mvirtuoso -fdry {{foundry}} -proc {{process}} -fpdkv {{foundry_pdk_version}} "
    "-icRel {{icrel}} -ap {{ap}} -prov {{prov}} -mstk {{pdk_metal_stack}}"
)

class CreatePackageTab(QWidget):
    """
    Tab for creating a QA package in the QA tool.
    """
    pdk_versions_loaded = pyqtSignal(list)
    techlib_callback_signal = pyqtSignal(str)  # Signal emitted when techlib changes

    def __init__(self, main_window: QWidget, parent: QWidget = None) -> None:
        """
        Initialize the CreatePackageTab.

        Args:
            main_window (QWidget): Reference to the main window.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.main_window = main_window
        self.widgets = {}
        self.drc_widgets = {}
        self.drc_settings_group = None
        self.worker = None
        self.init_ui()

    def init_ui(self) -> None:
        """
        Initialize the user interface for the Create Package tab.
        """
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.create_required_setting_group())
        layout.addWidget(self.create_common_setting_group())
        self.drc_settings_group = self.create_drc_settings_group()
        layout.addWidget(self.drc_settings_group)

        # Add buttons for Verify, Create, Stop with icons
        btn_hbox = QHBoxLayout()
        btn_hbox.addStretch()
        self.verify_btn = QPushButton("Verify")
        self.verify_btn.setVisible(False)
        self.verify_btn.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxQuestion))
        self.run_btn = QPushButton("Create")
        self.run_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_btn.setEnabled(False)
        for btn in [self.verify_btn, self.run_btn, self.stop_btn]:
            btn_hbox.addWidget(btn)
        layout.addLayout(btn_hbox)

        # Connect buttons to tab-specific methods
        self.verify_btn.clicked.connect(self.verify_callback)
        self.run_btn.clicked.connect(self.run_callback)
        self.stop_btn.clicked.connect(self.stop_callback)

    def add_browse_button(self, line_edit, is_directory=False, file_filter=None):
        def browse():
            if is_directory:
                path = QFileDialog.getExistingDirectory(
                    self, "Select Directory", line_edit.text() or os.getcwd()
                )
            else:
                path, _ = QFileDialog.getOpenFileName(
                    self, "Select File", line_edit.text() or os.getcwd(), file_filter or "All Files (*)"
                )
            if path:
                line_edit.setText(path)
                logger.info(f"Selected path for {line_edit.objectName()}: {path}")

        browse_btn = QPushButton("")
        browse_btn.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        browse_btn.clicked.connect(browse)
        widget_name = line_edit.objectName() + "_browse"
        if line_edit in self.drc_widgets.values():
            self.drc_widgets[widget_name] = browse_btn
        else:
            self.widgets[widget_name] = browse_btn
        return browse_btn

    def create_required_setting_group(self):
        """Create a group for required settings."""
        group = QGroupBox("Required Settings")
        layout = QFormLayout()

        self.widgets['tech_combo'] = QComboBox()
        self.widgets['tech_combo'].addItems(SUPPORTED_TECHLIBS)
        self.widgets['tech_combo'].setCurrentText(SUPPORTED_TECHLIBS[0])
        self.widgets['tech_combo'].setToolTip("Select the technology library")
        # Connect tech_combo change to emit techlib callback
        self.widgets['tech_combo'].currentTextChanged.connect(self._emit_techlib_callback)
        layout.addRow("Techlib:", self.widgets['tech_combo'])

        qa_types_layout = QHBoxLayout()
        self.widgets['qa_types'] = {}
        for qa_type in ['CDF', 'DRC', 'TA']:
            checkbox = QCheckBox(qa_type)
            self.widgets['qa_types'][qa_type] = checkbox
            qa_types_layout.addWidget(checkbox)
            if qa_type == 'DRC':
                checkbox.stateChanged.connect(self.toggle_drc_settings_group)
        layout.addRow("QA Types:", qa_types_layout)

        self.widgets['cds_lib'] = QLineEdit("")
        self.widgets['cds_lib'].setPlaceholderText("Enter cds.lib file path")
        self.widgets['cds_lib'].setToolTip("Path to the cds.lib file to start Virtuoso")
        self.widgets['cds_lib'].setObjectName("cds_lib")
        view_cds_btn = QPushButton("View")
        view_cds_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        view_cds_btn.clicked.connect(lambda: utils.open_file(self.widgets['cds_lib'].text(), logger))
        self.widgets['cds_lib_view'] = view_cds_btn
        cds_row = QHBoxLayout()
        cds_row.addWidget(self.widgets['cds_lib'])
        cds_row.addWidget(view_cds_btn)
        cds_row.addWidget(self.add_browse_button(self.widgets['cds_lib'], file_filter="Library Files (*.lib);;All Files (*)"))
        layout.addRow("cds.lib:", cds_row)

        self.widgets['qa_setting'] = QLineEdit("")
        self.widgets['qa_setting'].setPlaceholderText("Enter path to QA setting file")
        self.widgets['qa_setting'].setToolTip("Path to the QA setting file in .xls format")
        self.widgets['qa_setting'].setObjectName("qa_setting")
        view_qa_btn = QPushButton("View")
        view_qa_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        view_qa_btn.clicked.connect(lambda: utils.open_file(self.widgets['qa_setting'].text(), logger))
        self.widgets['qa_setting_view'] = view_qa_btn
        qa_row = QHBoxLayout()
        qa_row.addWidget(self.widgets['qa_setting'])
        qa_row.addWidget(view_qa_btn)
        qa_row.addWidget(self.add_browse_button(self.widgets['qa_setting'], file_filter="Excel Files (*.xls *.xlsx);;All Files (*)"))
        layout.addRow("QA Setting:", qa_row)

        # --- PDK Config: disabled, auto-set, no browse, allow Load/View ---
        self.widgets['pdk_config'] = QLineEdit("")
        self.widgets['pdk_config'].setReadOnly(True)
        self.widgets['pdk_config'].setDisabled(True)  # Disable the field
        self.widgets['pdk_config'].setToolTip("Path to the PDK configuration file in YAML format (auto-set)")
        self.widgets['pdk_config'].setObjectName("pdk_config")
        pdk_load_btn = QPushButton("Load")
        pdk_load_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        pdk_load_btn.clicked.connect(self.load_pdk_config)
        self.widgets['pdk_config_load'] = pdk_load_btn
        pdk_view_btn = QPushButton("View")
        pdk_view_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        pdk_view_btn.clicked.connect(lambda: utils.open_file(self.widgets['pdk_config'].text(), logger))
        self.widgets['pdk_config_view'] = pdk_view_btn
        pdk_row = QHBoxLayout()
        pdk_row.addWidget(self.widgets['pdk_config'])
        pdk_row.addWidget(pdk_load_btn)
        pdk_row.addWidget(pdk_view_btn)
        layout.addRow("PDK Config:", pdk_row)

        self.widgets['pdk_version'] = QComboBox()
        self.widgets['pdk_version'].addItems(["Undefined"])
        self.widgets['pdk_version'].setCurrentText("Undefined")
        self.widgets['pdk_version'].setToolTip("Select the PDK version to use for the QA run")
        self.widgets['pdk_version'].setEnabled(False)
        layout.addRow("PDK Version:", self.widgets['pdk_version'])

        # Virtuoso command field is always set to the template, not updated by PDK config or version
        self.widgets['virtuoso_cmd'] = QLineEdit("")
        self.widgets['virtuoso_cmd'].setPlaceholderText("Enter Virtuoso command")
        self.widgets['virtuoso_cmd'].setToolTip("Command to open Virtuoso, auto-filled from PDK config")
        self.widgets['virtuoso_cmd'].setObjectName("virtuoso_cmd")
        self.widgets['virtuoso_cmd'].setText(VIRTUOSO_CMD_TEMPLATE)
        layout.addRow("Virtuoso:", self.widgets['virtuoso_cmd'])

        self.pdk_versions_loaded.emit([])  # Emit empty list initially

        group.setLayout(layout)
        return group

    def _emit_techlib_callback(self, techlib: str):
        """Emit techlib_callback_signal when techlib changes."""
        self.techlib_callback_signal.emit(techlib)

    def create_common_setting_group(self):
        """Create a group for common settings."""
        group = QGroupBox("Common Settings")
        layout = QFormLayout()

        self.widgets['run_dir'] = QLineEdit("./output_qa")
        self.widgets['run_dir'].setPlaceholderText("Enter run directory path")
        self.widgets['run_dir'].setToolTip("Directory where the run will be executed")
        self.widgets['run_dir'].setObjectName("run_dir")
        run_row = QHBoxLayout()
        run_row.addWidget(self.widgets['run_dir'])
        run_row.addWidget(self.add_browse_button(self.widgets['run_dir'], is_directory=True))
        layout.addRow("Run Directory:", run_row)

        self.widgets['max_instances'] = QLineEdit("50")
        self.widgets['max_instances'].setValidator(QIntValidator(1, 1000))
        self.widgets['max_instances'].setPlaceholderText("Enter max instances per cellview")
        self.widgets['max_instances'].setToolTip("Maximum number of instances per cellview")
        self.widgets['max_instances'].setObjectName("max_instances")
        layout.addRow("Max Instances:", self.widgets['max_instances'])

        self.widgets['log_level'] = QComboBox()
        self.widgets['log_level'].addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.widgets['log_level'].setCurrentText("INFO")
        self.widgets['log_level'].setToolTip("Set the logging level for the QA run")
        layout.addRow("Log Level:", self.widgets['log_level'])

        self.widgets['max_jobs'] = QLineEdit("100")
        self.widgets['max_jobs'].setValidator(QIntValidator(1, 1000))
        self.widgets['max_jobs'].setPlaceholderText("Enter max jobs")
        self.widgets['max_jobs'].setToolTip("Maximum number of jobs to run in parallel")
        self.widgets['max_jobs'].setObjectName("max_jobs")
        # Add Check button next to Max Jobs
        check_btn = QPushButton("Check")
        check_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        check_btn.clicked.connect(self.check_license_availability)
        self.widgets['max_jobs_check'] = check_btn
        max_jobs_row = QHBoxLayout()
        max_jobs_row.addWidget(self.widgets['max_jobs'])
        max_jobs_row.addWidget(check_btn)
        layout.addRow("Max Jobs:", max_jobs_row)

        self.widgets['retries'] = QLineEdit("2")
        self.widgets['retries'].setValidator(QIntValidator(0, 10))
        self.widgets['retries'].setPlaceholderText("Enter number of retries")
        self.widgets['retries'].setToolTip("Number of retries for failed jobs")
        self.widgets['retries'].setObjectName("retries")
        layout.addRow("Retries:", self.widgets['retries'])

        self.widgets['cdsinit'] = QLineEdit("")
        self.widgets['cdsinit'].setPlaceholderText("Enter path to cdsinit local file")
        self.widgets['cdsinit'].setToolTip("Path to the .cdsinit file for Cadence settings")
        self.widgets['cdsinit'].setObjectName("cdsinit")
        view_cdsinit_btn = QPushButton("View")
        view_cdsinit_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        view_cdsinit_btn.clicked.connect(lambda: utils.open_file(self.widgets['cdsinit'].text(), logger))
        self.widgets['cdsinit_view'] = view_cdsinit_btn
        cdsinit_row = QHBoxLayout()
        cdsinit_row.addWidget(self.widgets['cdsinit'])
        cdsinit_row.addWidget(view_cdsinit_btn)
        cdsinit_row.addWidget(self.add_browse_button(self.widgets['cdsinit'], file_filter="All Files (*)"))
        layout.addRow(".cdsinit:", cdsinit_row)

        # Save .expressPcells and Cleanup Run Directory as checkboxes on one row
        options_row = QHBoxLayout()
        self.widgets['save_express_pcells'] = QCheckBox("Save .expressPcells")
        self.widgets['save_express_pcells'].setChecked(True)
        self.widgets['cleanup_run_dir'] = QCheckBox("Cleanup Run Directory")
        self.widgets['cleanup_run_dir'].setChecked(False)
        options_row.addWidget(self.widgets['save_express_pcells'])
        options_row.addWidget(self.widgets['cleanup_run_dir'])
        layout.addRow("Options:", options_row)

        group.setLayout(layout)
        return group

    def create_drc_settings_group(self):
        """Create a group for DRC settings."""
        group = QGroupBox("DRC Settings")
        layout = QFormLayout()

        self.drc_widgets['proj_mpv'] = QLineEdit()
        self.drc_widgets['proj_mpv'].setPlaceholderText("Enter project MPV")
        self.drc_widgets['proj_mpv'].setToolTip("Project MPV setting for DRC")
        self.drc_widgets['proj_mpv'].setObjectName("proj_mpv")
        view_proj_mpv_btn = QPushButton("View")
        view_proj_mpv_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        view_proj_mpv_btn.clicked.connect(lambda: utils.open_file(self.drc_widgets['proj_mpv'].text(), logger))
        self.drc_widgets['proj_mpv_view'] = view_proj_mpv_btn
        proj_mpv_row = QHBoxLayout()
        proj_mpv_row.addWidget(self.drc_widgets['proj_mpv'])
        proj_mpv_row.addWidget(view_proj_mpv_btn)
        proj_mpv_row.addWidget(self.add_browse_button(self.drc_widgets['proj_mpv'], file_filter="All Files (*)"))
        layout.addRow("Proj MPV:", proj_mpv_row)

        self.drc_widgets['mpvopts_drc'] = QLineEdit()
        self.drc_widgets['mpvopts_drc'].setPlaceholderText("Enter mpvopts for DRC")
        self.drc_widgets['mpvopts_drc'].setToolTip("mpvopts settings for DRC")
        self.drc_widgets['mpvopts_drc'].setObjectName("mpvopts_drc")
        view_mpvopts_drc_btn = QPushButton("View")
        view_mpvopts_drc_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        view_mpvopts_drc_btn.clicked.connect(lambda: utils.open_file(self.drc_widgets['mpvopts_drc'].text(), logger))
        self.drc_widgets['mpvopts_drc_view'] = view_mpvopts_drc_btn
        mpvopts_drc_row = QHBoxLayout()
        mpvopts_drc_row.addWidget(self.drc_widgets['mpvopts_drc'])
        mpvopts_drc_row.addWidget(view_mpvopts_drc_btn)
        mpvopts_drc_row.addWidget(self.add_browse_button(self.drc_widgets['mpvopts_drc'], file_filter="All Files (*)"))
        layout.addRow("mpvopts DRC:", mpvopts_drc_row)

        self.drc_widgets['runcalx_version'] = QLineEdit()
        self.drc_widgets['runcalx_version'].setPlaceholderText("Enter Runcalx version")
        self.drc_widgets['runcalx_version'].setToolTip("Runcalx version for DRC")
        self.drc_widgets['runcalx_version'].setObjectName("runcalx_version")
        layout.addRow("Runcalx Version:", self.drc_widgets['runcalx_version'])

        group.setLayout(layout)
        group.setEnabled(False)
        return group

    def toggle_drc_settings_group(self, state):
        """Enable or disable the DRC Settings group and its buttons based on DRC checkbox state."""
        is_enabled = state == Qt.Checked
        self.drc_settings_group.setEnabled(is_enabled)
        self.drc_widgets['proj_mpv'].setEnabled(is_enabled)
        self.drc_widgets['proj_mpv_browse'].setEnabled(is_enabled)
        self.drc_widgets['proj_mpv_view'].setEnabled(is_enabled)
        self.drc_widgets['mpvopts_drc'].setEnabled(is_enabled)
        self.drc_widgets['mpvopts_drc_browse'].setEnabled(is_enabled)
        self.drc_widgets['mpvopts_drc_view'].setEnabled(is_enabled)
        self.drc_widgets['runcalx_version'].setEnabled(is_enabled)

    def load_pdk_config(self):
        """Load PDK versions from the specified YAML config file."""
        file_path = self.widgets['pdk_config'].text()
        versions = []

        valid, message = utils.validate_path(file_path, must_exist=True)
        if not valid:
            logger.error(message)
            self.pdk_versions_loaded.emit(versions)
            return

        try:
            import yaml
            with open(file_path, 'r') as f:
                config = yaml.safe_load(f)
            if config and isinstance(config, dict) and 'versions' in config:
                versions = list(config['versions'].keys())
                if not versions:
                    logger.warning(f"No versions found in {file_path}")
            else:
                logger.error(f"Invalid or empty YAML configuration in {file_path}")
            self.pdk_versions_loaded.emit(versions)
            logger.info(f"Successfully loaded {len(versions)} PDK versions from {file_path}")
        except Exception as e:
            logger.error(f"Failed to load PDK config {file_path}: {str(e)}. Traceback: {traceback.format_exc()}")
            self.pdk_versions_loaded.emit([])

    def update_pdk_versions(self, versions):
        """Update the PDK Version dropdown with new versions."""
        current_version = self.widgets['pdk_version'].currentText()
        self.widgets['pdk_version'].clear()
        if versions:
            self.widgets['pdk_version'].addItems(versions)
            if current_version in versions:
                self.widgets['pdk_version'].setCurrentText(current_version)
            else:
                self.widgets['pdk_version'].setCurrentText(versions[0])
            self.widgets['pdk_version'].setEnabled(True)
        else:
            self.widgets['pdk_version'].addItem("Undefined")
            self.widgets['pdk_version'].setCurrentText("Undefined")
            self.widgets['pdk_version'].setEnabled(False)

    def get_settings(self):
        base_dir = os.getenv('QA_MRVL_TECH_CWD', os.path.dirname(os.path.abspath(__file__)))
        settings = {
            'required_settings': {
                'techlib': self.widgets['tech_combo'].currentText(),
                'qa_types': {
                    qa_type: checkbox.isChecked() for qa_type, checkbox in self.widgets['qa_types'].items()
                },
                'cds_lib': self.widgets['cds_lib'].text(),
                'qa_setting': self.widgets['qa_setting'].text(),
                'pdk_config': self.widgets['pdk_config'].text(),
                'pdk_version': self.widgets['pdk_version'].currentText(),
                'virtuoso_cmd': self.widgets['virtuoso_cmd'].text()
            },
            'common_settings': {
                'run_dir': self.widgets['run_dir'].text() or "./output_qa",
                'max_instances': self.widgets['max_instances'].text() or "50",
                'log_level': self.widgets['log_level'].currentText(),
                'max_jobs': self.widgets['max_jobs'].text() or "100",
                'retries': self.widgets['retries'].text() or "2",
                'cdsinit': self.widgets['cdsinit'].text(),
                'save_express_pcells': self.widgets['save_express_pcells'].isChecked(),
                'cleanup': self.widgets['cleanup_run_dir'].isChecked(),
            },
            'drc_settings': {
                'proj_mpv': self.drc_widgets['proj_mpv'].text(),
                'mpvopts_drc': self.drc_widgets['mpvopts_drc'].text(),
                'runcalx_version': self.drc_widgets['runcalx_version'].text(),
            }
        }

        def resolve_and_validate_path(path, must_exist=False):
            if path and not os.path.isabs(path):
                resolved_path = os.path.normpath(os.path.join(base_dir, path))
                valid, message = utils.validate_path(resolved_path, must_exist=must_exist)
                if not valid:
                    logger.error(f"Resolved path invalid: {path} -> {resolved_path}: {message}")
                return resolved_path
            valid, message = utils.validate_path(path, must_exist=must_exist)
            if not valid:
                logger.error(f"Path invalid: {path}: {message}")
            return path

        # Only validate enabled fields
        # Required settings
        for key in ['cds_lib', 'qa_setting', 'pdk_config']:
            widget = self.widgets.get(key)
            path = settings['required_settings'].get(key, '')
            if widget is not None and widget.isEnabled() and path:
                settings['required_settings'][key] = resolve_and_validate_path(path, must_exist=True)

        # Common settings
        for key in ['run_dir', 'cdsinit']:
            widget = self.widgets.get(key)
            path = settings['common_settings'].get(key, '')
            if widget is not None and widget.isEnabled() and path:
                settings['common_settings'][key] = resolve_and_validate_path(path, must_exist=False)

        # DRC settings (only if DRC is checked and widget is enabled)
        if settings['required_settings']['qa_types'].get('DRC', False):
            for key in ['proj_mpv', 'mpvopts_drc', 'runcalx_version']:
                widget = self.drc_widgets.get(key)
                path = settings['drc_settings'].get(key, '')
                if widget is not None and widget.isEnabled() and path:
                    settings['drc_settings'][key] = resolve_and_validate_path(path, must_exist=True)

        return settings

    def set_settings(self, settings):
        required_settings = settings.get('required_settings', {})
        common_settings = settings.get('common_settings', {})
        drc_settings = settings.get('drc_settings', {})
        techlib = required_settings.get('techlib', SUPPORTED_TECHLIBS[0])
        if techlib not in [self.widgets['tech_combo'].itemText(i) for i in range(self.widgets['tech_combo'].count())]:
            logger.warning(f"Invalid techlib value {techlib}, defaulting to {SUPPORTED_TECHLIBS[0]}")
            techlib = SUPPORTED_TECHLIBS[0]
        self.widgets['tech_combo'].setCurrentText(techlib)
        for qa_type, status in required_settings.get('qa_types', {}).items():
            if qa_type in self.widgets['qa_types']:
                self.widgets['qa_types'][qa_type].setChecked(status)
        self.widgets['cds_lib'].setText(required_settings.get('cds_lib', ''))
        self.widgets['qa_setting'].setText(required_settings.get('qa_setting', ''))
        # Always set PDK config path programmatically
        self.techlib_callback_signal.emit(techlib)
        self.widgets['pdk_version'].setCurrentText(required_settings.get('pdk_version', 'Undefined'))

        self.widgets['run_dir'].setText(common_settings.get('run_dir', './output_qa'))
        self.widgets['max_instances'].setText(common_settings.get('max_instances', '50'))
        self.widgets['log_level'].setCurrentText(common_settings.get('log_level', 'INFO'))
        self.widgets['max_jobs'].setText(common_settings.get('max_jobs', '100'))
        self.widgets['retries'].setText(common_settings.get('retries', '2'))
        self.widgets['cdsinit'].setText(common_settings.get('cdsinit', ''))
        self.widgets['save_express_pcells'].setChecked(common_settings.get('save_express_pcells', True))
        self.widgets['cleanup_run_dir'].setChecked(common_settings.get('cleanup', False))

        self.drc_widgets['proj_mpv'].setText(drc_settings.get('proj_mpv', ''))
        self.drc_widgets['mpvopts_drc'].setText(drc_settings.get('mpvopts_drc', ''))
        self.drc_widgets['runcalx_version'].setText(drc_settings.get('runcalx_version', ''))

        self.toggle_drc_settings_group(Qt.Checked if self.widgets['qa_types']['DRC'].isChecked() else Qt.Unchecked)

    class Worker(QThread):
        """Worker thread to handle long-running QA tasks with robust process group management.

        Attributes
        ----------
        parent : QWidget
            The parent widget.
        settings : dict
            Settings for the QA run.
        _is_running : bool
            Flag to control thread execution.
        processes : list[subprocess.Popen]
            List of running subprocesses.
        """
        progress = pyqtSignal(str)
        finished = pyqtSignal(bool, str)
        error = pyqtSignal(str)
        log_output = pyqtSignal(str)
        cache_db_ready = pyqtSignal(object)

        def __init__(self, parent: QWidget, settings: dict) -> None:
            super().__init__(parent)
            self.parent = parent
            self.settings = settings
            self._is_running = True
            self.processes: list[subprocess.Popen] = []

        def stop(self) -> None:
            """Flag to stop the thread and terminate subprocesses and their children using process groups."""
            self._is_running = False
            import signal
            for proc in self.processes:
                try:
                    if hasattr(proc, 'pid') and proc.pid:
                        # Kill the whole process group
                        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                        logger.info(f"Sent SIGTERM to process group {os.getpgid(proc.pid)} (PID {proc.pid})")
                        try:
                            proc.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                            logger.info(f"Sent SIGKILL to process group {os.getpgid(proc.pid)} (PID {proc.pid})")
                    else:
                        proc.terminate()
                        proc.wait(timeout=10)
                except Exception as e:
                    logger.error(f"Failed to terminate process group for PID {getattr(proc, 'pid', None)}: {e}")
            self.processes.clear()

        def run_subprocess(self, script_path: Union[str, Path], run_dir: Union[str, Path]) -> bool:
            """
            Execute a script using subprocess and stream stdout, starting in a new process group for robust termination.

            Parameters
            ----------
            script_path : str or Path
                Path to the shell script to execute.
            run_dir : str or Path
                Directory to use as the working directory for the subprocess.

            Returns
            -------
            bool
                True if the script executed successfully, False otherwise.
            """
            import signal
            try:
                script_path = Path(script_path)
                script_dir = script_path.parent
                cmd = f"pushd {script_dir}; {script_path}; popd"
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    shell=True,
                    cwd=run_dir,
                    preexec_fn=os.setsid  # Start the process in a new session (process group)
                )
                self.processes.append(proc)
                logger.info(f"Started subprocess PID {proc.pid} for script {script_path} (PGID {os.getpgid(proc.pid)})")
                self.progress.emit(f"Executing script: {script_path}")

                while self._is_running:
                    line = proc.stdout.readline()
                    if line:
                        self.log_output.emit(line.strip())
                    if proc.poll() is not None:
                        break

                if not self._is_running:
                    proc.stdout.close()
                    returncode = proc.wait()
                    logger.info(f"Subprocess PID {proc.pid} stopped by user")
                    if proc in self.processes:
                        self.processes.remove(proc)
                    return False

                for line in proc.stdout:
                    if line and self._is_running:
                        self.log_output.emit(line.strip())
                proc.stdout.close()
                returncode = proc.wait()
                if proc in self.processes:
                    self.processes.remove(proc)
                if returncode != 0:
                    logger.error(f"Subprocess PID {proc.pid} failed with return code {returncode}")
                return returncode == 0
            except Exception as e:
                error_message = f"Failed to execute {script_path}: {str(e)}"
                logger.error(error_message)
                self.error.emit(error_message)
                if 'proc' in locals() and proc in self.processes:
                    self.processes.remove(proc)
                return False

        def run(self) -> None:
            """Main thread execution logic.

            Removes the status directory if it exists and cleanup is enabled, then proceeds with the QA run.
            """
            try:
                utils.update_qa_run_status(True, logger)
                settings = self.settings.get('create_package_settings', {})
                common_settings = settings.get('common_settings', {})
                cleanup = common_settings.get('cleanup', False)
                run_dir = Path(common_settings.get('run_dir', './output_qa'))
                if cleanup and run_dir.exists():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_dir = run_dir.parent / f"{run_dir.name}_backup_{timestamp}"
                    try:
                        shutil.move(run_dir, backup_dir)
                        logger.info(f"Moved run directory to backup: {backup_dir}")
                    except Exception as e:
                        logger.error(f"Failed to move run directory to backup: {e}. Traceback: {traceback.format_exc()}")
                        QMessageBox.critical(self, "Error", f"Failed to move run directory to backup: {e}")
                        return
                    
                run_dir.mkdir(parents=True, exist_ok=True)
                self.cache_db = run_dir / ".cache.db"
                if not self.cache_db.exists():
                    db_obj = Database(self.cache_db)
                    db_obj.create_tables()
                    
                # Instead of direct call, emit signal for main thread to handle
                self.cache_db_ready.emit(self.cache_db)
                utils.update_qa_run_dir(run_dir, logger)
                if not self._is_running:
                    self.finished.emit(False, "Task stopped.")
                    return
                
                pkg_name = "new_package"
                file_name = "run_create_package.csh"
                file_run = run_dir / file_name
                file_log = file_run.with_name(f"{file_run.name}.log")
                utils.update_debug_log(file_log, logger)
                context = {
                    "MODE": "new",
                    "DB": self.cache_db,
                    "PKG_NAME": pkg_name,
                    "QA_MRVL_TECH": QA_MRVL_TECH,
                    "RUN_DIR": run_dir,
                    "SETTINGS": self.settings,
                    "LOG_FILE": file_log,
                }
                renderer = TemplateRenderer(TEMPLATE_DIR_FE)
                renderer.render("run_create_package.csh.j2", file_run, context, chmod=True)
                self.progress.emit(f"File run create new package: {file_run}")
                self.progress.emit(f"Executing script: {file_run}")
                if not self._is_running:
                    self.progress.emit(f"Execution of {file_run} stopped")
                    self.finished.emit(False, "Task stopped.")
                    return
                success = self.run_subprocess(file_run, run_dir)
                if success and self._is_running:
                    self.progress.emit(f"Completed execution of {file_run}")
                    self.finished.emit(True, "Package creation completed successfully.")
                else:
                    if not self._is_running:
                        self.progress.emit(f"Execution of {file_run} stopped")
                        self.finished.emit(False, "Task stopped.")
                    else:
                        error_message = f"Failed to execute {file_run}"
                        logger.error(error_message)
                        self.error.emit(error_message)
                        self.finished.emit(False, "Task failed.")
            except Exception as e:
                error_message = f"Failed to run QA: {str(e)}. Traceback: {traceback.format_exc()}"
                logger.error(error_message)
                self.error.emit(error_message)
                self.finished.emit(False, "Task failed.")
            finally:
                utils.update_qa_run_status(False, logger)

    def verify_callback(self):
        """Verify settings for the Create Package tab."""
        settings = self.get_settings()
        self.main_window.status_label.setText("Status: Verification not fully implemented")
        QMessageBox.information(self, "Info", "Verification functionality is not fully implemented.")
        logger.info("Verification triggered, but not fully implemented")

    def pre_run_validation(self) -> bool:
        """
        Perform pre-run validations before starting the create process.
        Returns
        -------
        bool
            True if all validations pass, False otherwise.
        """
        # List of (widget_key, label, must_exist) to check
        required_fields = [
            ('cds_lib', 'cds.lib', True),
            ('qa_setting', 'QA Setting', True),
            ('pdk_config', 'PDK Config', True),
        ]
        for key, label, must_exist in required_fields:
            widget = self.widgets.get(key)
            if widget is not None and widget.isEnabled():
                path = widget.text().strip()
                if not path:
                    QMessageBox.warning(self, "Validation Error", f"{label} path is empty.")
                    return False
                abs_path = os.path.abspath(path)
                if must_exist and not os.path.exists(abs_path):
                    QMessageBox.warning(self, "Validation Error", f"{label} does not exist: {abs_path}")
                    return False
        # .cdsinit is optional, but if filled and enabled, check existence
        cdsinit_widget = self.widgets.get('cdsinit')
        if cdsinit_widget is not None and cdsinit_widget.isEnabled():
            cdsinit_path = cdsinit_widget.text().strip()
            if cdsinit_path:
                abs_path = os.path.abspath(cdsinit_path)
                if not os.path.exists(abs_path):
                    QMessageBox.warning(self, "Validation Error", f".cdsinit file does not exist: {abs_path}")
                    return False
        # DRC settings: only if DRC is checked and widgets are enabled
        if self.widgets.get('qa_types', {}).get('DRC', None) and self.widgets['qa_types']['DRC'].isChecked():
            drc_required = [
                ('proj_mpv', 'Proj MPV', True),
                ('mpvopts_drc', 'mpvopts DRC', True),
                ('runcalx_version', 'Runcalx Version', True),
            ]
            for key, label, must_exist in drc_required:
                widget = self.drc_widgets.get(key)
                if widget is not None and widget.isEnabled():
                    value = widget.text().strip()
                    if not value:
                        QMessageBox.warning(self, "Validation Error", f"{label} is empty.")
                        return False
                    abs_path = os.path.abspath(value)
                    if must_exist and not os.path.exists(abs_path):
                        QMessageBox.warning(self, "Validation Error", f"{label} does not exist: {abs_path}")
                        return False
        return True

    def run_callback(self):
        """
        Run QA tasks for the Create Package tab in a separate thread.
        """
        if not self.pre_run_validation():
            logger.error("Pre-run validation failed, cannot start QA tasks.")
            return
        
        # Set Debug tab active (index 2)
        if hasattr(self.main_window, 'tabs'):
            self.main_window.tabs.setCurrentIndex(2)

        try:
            logger.info("Resolve paths and save settings for Create Package tab")
            self.main_window.resolve_paths()

            logger.info("Get settings create package tab")
            settings = self.get_settings()

            # Validate required paths before proceeding
            required_paths = [
                (settings['required_settings'].get('cds_lib'), True, 'cds.lib'),
                (settings['required_settings'].get('qa_setting'), True, 'QA Setting'),
                (settings['required_settings'].get('pdk_config'), True, 'PDK Config'),
            ]
            for path, must_exist, label in required_paths:
                valid, message = utils.validate_path(path, must_exist=must_exist)
                if not valid:
                    QMessageBox.critical(self, "Invalid Path", f"{label}: {message}")
                    logger.error(f"Validation failed for {label}: {message}")
                    return

            # .cdsinit is optional, do not require it
            # Validate DRC fields if DRC is checked
            if settings['required_settings']['qa_types'].get('DRC', False):
                drc_required = [
                    (settings['drc_settings'].get('proj_mpv'), True, 'Proj MPV'),
                    (settings['drc_settings'].get('mpvopts_drc'), True, 'mpvopts DRC'),
                    (settings['drc_settings'].get('runcalx_version'), True, 'Runcalx Version'),
                ]
                for value, must_exist, label in drc_required:
                    valid, message = utils.validate_path(value, must_exist=must_exist)
                    if not valid:
                        QMessageBox.critical(self, "Invalid Path", f"{label}: {message}")
                        logger.error(f"Validation failed for {label}: {message}")
                        return

            success, message = SettingsManager.save_settings(self.main_window, "./last_qa_settings.json")
            self.main_window.status_label.setText(f"Status: {message}")
            if not success:
                QMessageBox.critical(self, "Error", message)
                return

            utils.monitor_user_jobs("./last_qa_settings.json")
            with open("./last_qa_settings.json", 'r') as f:
                settings = json.load(f)

            self.run_btn.setEnabled(False)
            self.verify_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.main_window.status_label.setText("Status: Starting QA tasks...")

            self.worker = self.Worker(self, settings)
            self.worker.progress.connect(self.update_status)
            self.worker.finished.connect(self.task_finished)
            self.worker.error.connect(self.task_error)
            self.worker.log_output.connect(
                lambda line: self.main_window.tab_debug.update_log(line, "debug_log")
            )
            # Connect cache_db_ready to assign_debug_db in main thread
            self.worker.cache_db_ready.connect(self.main_window.assign_debug_db)
            self.worker.start()

        except Exception as e:
            error_message = f"Failed to start QA: {str(e)}. Traceback: {traceback.format_exc()}"
            logger.error(error_message)
            self.main_window.status_label.setText(f"Status: {error_message}")
            QMessageBox.critical(self, "Error", error_message)

    def update_status(self, message):
        """Update the status label with progress messages."""
        self.main_window.status_label.setText(f"Status: {message}")

    def task_finished(self, success, message):
        """
        Handle task completion and send jobs table via email.
        Also update status of all RUNNING and PENDING jobs to STOPPED if task was stopped.
        """
        self.main_window.status_label.setText(f"Status: {message}")
        self.run_btn.setEnabled(True)
        self.verify_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.worker = None

        # --- Update job statuses if stopped ---
        if message == "Task stopped.":
            try:
                with open("./last_qa_settings.json", 'r') as f:
                    settings = json.load(f)
                run_dir = Path(settings.get('create_package_settings', {}).get('common_settings', {}).get('run_dir', './output_create_package'))
                db_path = run_dir / ".cache.db"
                db = Database(str(db_path))
                for job in db.list_jobs():
                    if job['status'] in ('RUNNING', 'PENDING'):
                        db.update_job(job['id'], status='STOPPED', reason='Stopped by user')
                logger.info("Updated RUNNING and PENDING jobs to STOPPED.")
            except Exception as e:
                logger.error(f"Failed to update job statuses to STOPPED: {e}")

        # --- Send jobs table email ---
        logger.info("Sending jobs table email...")
        try:
            with open("./last_qa_settings.json", 'r') as f:
                settings = json.load(f)
            run_dir = Path(settings.get('create_package_settings', {}).get('common_settings', {}).get('run_dir', './output_create_package'))
            db_path = run_dir / ".cache.db"
            recipient = os.getenv('USER', 'user') + '@marvell.com'
            send_jobs_email(
                settings,
                run_dir,
                db_path,
                email_recipient=recipient,
                cc_emails=["nguyenv@marvell.com", "nquan@marvell.com"],
                logger=logger,
                title=f"[QA MRVL Techlib] Create Package: { message }",
                start_time=self.start_time,
                end_time=self.end_time
            )
            logger.info("Jobs table email sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send jobs table email: {e}")

        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Warning", message)

    def task_error(self, error_message: str) -> None:
        """
        Handle errors from the worker thread and always show a clear error message.

        Parameters
        ----------
        error_message : str
            The error message to display to the user.
        """
        self.main_window.status_label.setText(f"Status: {error_message}")
        self.run_btn.setEnabled(True)
        self.verify_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.worker = None
        QMessageBox.critical(self, "Error", error_message)

    def stop_callback(self) -> None:
        """
        Stop QA tasks for the Create Package tab and terminate associated processes in a worker thread.
        Always show a meaningful message to the user.
        """
        if self.worker and self.worker.isRunning():
            logger.info("User requested to stop QA tasks")
            self.worker.stop()
            self.main_window.status_label.setText("Status: Stopping QA tasks...")
            QApplication.processEvents()
            self.stop_btn.setEnabled(False)

            settings = self.get_settings()
            run_dir = Path(settings['common_settings'].get('run_dir', './output_qa'))
            # Start StopWorker thread
            self.stop_worker = StopWorker(run_dir, enum, self.main_window.status_label.setText)
            self.stop_worker.finished.connect(lambda msg: QMessageBox.information(self, "Info", msg))
            self.stop_worker.error.connect(lambda err: QMessageBox.critical(self, "Error", f"Error stopping tasks: {err}"))
            self.stop_worker.error.connect(lambda err: self.main_window.status_label.setText(f"Status: Error stopping tasks: {err}"))
            self.stop_worker.start()
        else:
            msg = "No tasks are currently running."
            self.main_window.status_label.setText(f"Status: {msg}")
            QApplication.processEvents()
            QMessageBox.information(self, "Info", msg)

    def check_license_availability(self) -> None:
        """
        Check available licenses for all features in LICENSE_FEATURES in a separate thread and show live output in a popup.
        Always show a meaningful error if license check fails.

        Returns
        -------
        None
        """
        from config import LICENSE_FEATURES
        self.main_window.status_label.setText("Status: Checking license availability...")
        logger.info("Checking license availability for features: %s", LICENSE_FEATURES)
        self.license_dialog = LicenseCheckDialog(self)
        self.license_worker = LicenseCheckWorker(LICENSE_FEATURES, self)
        self.license_worker.output.connect(self.license_dialog.append_text, type=Qt.QueuedConnection)
        self.license_worker.finished.connect(self.license_dialog.enable_close, type=Qt.QueuedConnection)
        self.license_worker.finished.connect(lambda: self.main_window.status_label.setText("Status: License check complete."), type=Qt.QueuedConnection)
        self.license_worker.error.connect(lambda err: QMessageBox.critical(self, "Error", f"License check error: {err}"))
        self.license_worker.error.connect(lambda err: self.main_window.status_label.setText(f"Status: License check error: {err}"))
        self.license_dialog.show()
        self.license_worker.start()

class LicenseCheckWorker(QThread):
    """
    Worker thread to check license availability for features in LICENSE_FEATURES.
    Emits stdout lines and completion signal.
    """
    output = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, features: List[str], parent: QWidget = None) -> None:
        super().__init__(parent)
        self.features = features
        self._is_running = True

    def run(self) -> None:
        for idx, feature in enumerate(self.features, 1):
            if not self._is_running:
                break
            command = f'lmstat -f {feature}'
            self.output.emit(f"[{idx}/{len(self.features)}] Checking {feature}...")
            self.output.emit(f"Executing command: {command}")
            try:
                result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
                output_lines = []
                for line in result.stdout.splitlines():
                    if not self._is_running:
                        break
                    if line.strip():
                        line = line.strip("\n")
                        if f"Users of {feature}" in line:
                            output_lines.append(line)
                            self.output.emit(line)
            except Exception as e:
                error_msg = f"{feature}: Error: {str(e)}"
                self.output.emit(error_msg + "\n")
                self.error.emit(error_msg)
        self.finished.emit()

    def stop(self) -> None:
        self._is_running = False

class LicenseCheckDialog(QDialog):
    """
    Dialog to show live license check output.
    """
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("License Availability")
        self.resize(900, 400)
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        self.close_btn = QPushButton("Close", self)
        self.close_btn.setEnabled(False)
        layout.addWidget(self.close_btn)
        self.close_btn.clicked.connect(self.accept)

    def append_text(self, text: str) -> None:
        self.text_edit.append(text)

    def enable_close(self) -> None:
        self.close_btn.setEnabled(True)

class StopWorker(QThread):
    """
    Worker thread to handle stopping QA tasks and terminating processes without blocking the GUI.
    """
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, run_dir: Path, enum, status_callback) -> None:
        super().__init__()
        self.run_dir = run_dir
        self.enum = enum
        self.status_callback = status_callback

    def run(self) -> None:
        try:
            from backend.python.models.database import Database
            import signal
            import os
            db_path = str(self.run_dir / ".cache.db")
            db = Database(db_path)
            pids = db.list_pids()
            if not pids:
                msg = f"No running jobs found in database for {self.run_dir}."
                self.status_callback(f"Status: {msg}")
                self.finished.emit(msg)
                return
            killed = 0
            for row in pids:
                pid = row['pid']
                try:
                    subprocess.run(['sgdel', str(pid)], check=True, capture_output=True)
                    self.status_callback(f"Status: Stopping job with PID {pid}...")
                    logger.info(f"Stopping job with PID {pid}...")
                    db.delete_pid(pid)
                    killed += 1
                except Exception as e:
                    error_msg = f"Failed to stop job with PID {pid}: {str(e)}"
                    logger.error(error_msg)
                    self.status_callback(f"Status: {error_msg}")
                    self.error.emit(error_msg)
            msg = f"Stopped {killed} running jobs."
            self.status_callback(f"Status: {msg}")
            self.finished.emit(msg)
        except Exception as e:
            import traceback
            error_msg = f"Error while stopping jobs from database in {self.run_dir}: {e}\n{traceback.format_exc()}"
            logger.error(error_msg)
            self.status_callback(f"Status: {error_msg}")
            self.error.emit(error_msg)