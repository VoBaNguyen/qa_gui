"""
Module for the Compare tab in QA MRVL Techlib Tool.
Provides UI and logic for comparing QA packages, including settings management and job control.
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
from datetime import datetime, timedelta
from typing import Any, Optional, List, Dict
import psutil  # For process management
import signal  # For os.kill fallback
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QRadioButton, QGroupBox, QFormLayout, QApplication,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QFileDialog, QMessageBox, QStyle, QButtonGroup
)
from PyQt5.QtGui import QIcon
from tabulate import tabulate
from pprint import pformat
from utils import file_utils as utils
from utils import enum
from utils.job_runner import run_jobs
from utils.template_renderer import TemplateRenderer
from frontend.tabs.settings_manager import SettingsManager
from backend.python.models.database import Database
from config import QA_MRVL_TECH, TEMPLATE_DIR_FE
from utils.send_mail import send_jobs_email

logger = logging.getLogger(__name__)

# Thread-safe file lock for JSON operations
file_lock = threading.Lock()

class CompareTab(QWidget):
    """Tab for comparing two packages in the QA tool."""
    def __init__(self, main_window: Any, parent: QWidget = None) -> None:
        """
        Initialize the CompareTab.

        Args:
            main_window (Any): Reference to the main window.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.main_window = main_window
        self.widgets = {}
        self.worker = None
        self.start_time = None  # Store start time
        self.end_time = None    # Store end time
        self.init_ui()

    def init_ui(self) -> None:
        """
        Initialize the user interface for the Compare tab.
        """
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.create_golden_package_group())
        layout.addWidget(self.create_alpha_package_group())
        layout.addWidget(self.create_setting_group())

        # Add buttons for Verify, Compare, Stop with icons
        btn_hbox = QHBoxLayout()
        btn_hbox.addStretch()
        self.verify_btn = QPushButton("Verify")
        self.verify_btn.setVisible(False)
        self.verify_btn.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxQuestion))  # Question icon for verification
        self.run_btn = QPushButton("Compare")
        self.run_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))  # Play icon for running tasks
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))  # Stop icon for stopping tasks
        self.stop_btn.setEnabled(False)  # Initially disabled
        for btn in [self.verify_btn, self.run_btn, self.stop_btn]:
            btn_hbox.addWidget(btn)
        layout.addLayout(btn_hbox)

        # Connect buttons to tab-specific methods
        self.verify_btn.clicked.connect(self.verify_callback)
        self.run_btn.clicked.connect(self.run_callback)
        self.stop_btn.clicked.connect(self.stop_callback)

        # Initialize field states
        self.toggle_settings()

    def add_browse_button(self, line_edit: QLineEdit, is_directory: bool = False, file_filter: Optional[str] = None) -> QPushButton:
        """
        Add a browse button for a QLineEdit field to select a file or directory.

        Parameters
        ----------
        line_edit : QLineEdit
            The line edit widget to attach the browse button to.
        is_directory : bool, optional
            Whether to select a directory (default is False).
        file_filter : Optional[str], optional
            File filter for file dialog (default is None).

        Returns
        -------
        QPushButton
            The browse button widget.
        """
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
        browse_btn.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))  # Folder open icon for browsing
        browse_btn.clicked.connect(browse)
        # Store the browse button in self.widgets with a unique key
        widget_name = line_edit.objectName() + "_browse"
        self.widgets[widget_name] = browse_btn
        return browse_btn

    def create_golden_package_group(self) -> QGroupBox:
        """
        Create a group for configuring golden package settings.

        Returns
        -------
        QGroupBox
            The group box widget for golden package settings.
        """
        group = QGroupBox("Package Golden")
        layout = QFormLayout()

        # Source selection
        self.widgets['radio_existed_golden'] = QRadioButton("Existed Package")
        self.widgets['radio_new_golden'] = QRadioButton("Create New")
        self.widgets['radio_existed_golden'].setChecked(True)
        radio_group = QHBoxLayout()
        radio_group.addWidget(self.widgets['radio_existed_golden'])
        radio_group.addWidget(self.widgets['radio_new_golden'])
        layout.addRow("Source:", radio_group)

        # Golden Package Path
        self.widgets['golden_path'] = QLineEdit("./package_golden")
        self.widgets['golden_path'].setPlaceholderText("Enter golden package path")
        self.widgets['golden_path'].setObjectName("golden_path")
        golden_path_row = QHBoxLayout()
        golden_path_row.addWidget(self.widgets['golden_path'])
        golden_path_row.addWidget(self.add_browse_button(self.widgets['golden_path'], is_directory=True))
        layout.addRow("Package Path:", golden_path_row)

        # Golden CDF (should be a folder path)
        self.widgets['golden_cdf'] = QLineEdit("<PACKAGE>/qa_<TECHLIB>__CDF")
        self.widgets['golden_cdf'].setPlaceholderText("Enter golden CDF folder path")
        self.widgets['golden_cdf'].setObjectName("golden_cdf")
        golden_cdf_row = QHBoxLayout()
        golden_cdf_row.addWidget(self.widgets['golden_cdf'])
        golden_cdf_row.addWidget(self.add_browse_button(self.widgets['golden_cdf'], is_directory=True))
        layout.addRow("CDF Test Cases Folder:", golden_cdf_row)

        # Golden TA (should be a folder path)
        self.widgets['golden_ta'] = QLineEdit("<PACKAGE>/qa_<TECHLIB>__TA")
        self.widgets['golden_ta'].setPlaceholderText("Enter golden TA folder path")
        self.widgets['golden_ta'].setObjectName("golden_ta")
        golden_ta_row = QHBoxLayout()
        golden_ta_row.addWidget(self.widgets['golden_ta'])
        golden_ta_row.addWidget(self.add_browse_button(self.widgets['golden_ta'], is_directory=True))
        layout.addRow("TA Test Cases Folder:", golden_ta_row)

        # Golden Waived Rules
        self.widgets['golden_waived_rules'] = QLineEdit("<PACKAGE>/waived_rules_drc.xls")
        self.widgets['golden_waived_rules'].setPlaceholderText("Enter waived rules DRC file path")
        self.widgets['golden_waived_rules'].setObjectName("golden_waived_rules")
        view_golden_rules_btn = QPushButton("View")
        view_golden_rules_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))  # File icon for viewing
        view_golden_rules_btn.clicked.connect(lambda: utils.open_file(self.widgets['golden_waived_rules'].text(), logger))
        self.widgets['golden_waived_rules_view'] = view_golden_rules_btn  # Store view button
        golden_waived_rules_row = QHBoxLayout()
        golden_waived_rules_row.addWidget(self.widgets['golden_waived_rules'])
        golden_waived_rules_row.addWidget(view_golden_rules_btn)
        golden_waived_rules_row.addWidget(self.add_browse_button(self.widgets['golden_waived_rules'], file_filter="Excel Files (*.xls *.xlsx);;All Files (*)"))
        layout.addRow("Waived Rules:", golden_waived_rules_row)

        # PDK Version
        self.widgets['golden_pdk_version'] = QComboBox()
        self.widgets['golden_pdk_version'].addItems(["Undefined"])
        layout.addRow("PDK Version:", self.widgets['golden_pdk_version'])

        # Golden cds.lib
        self.widgets['golden_cds_lib'] = QLineEdit("<PACKAGE>/cds.lib")
        self.widgets['golden_cds_lib'].setPlaceholderText("Enter cds.lib file path")
        self.widgets['golden_cds_lib'].setObjectName("golden_cds_lib")
        view_golden_cds_btn = QPushButton("View")
        view_golden_cds_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))  # File icon for viewing
        view_golden_cds_btn.clicked.connect(lambda: utils.open_file(self.widgets['golden_cds_lib'].text(), logger))
        self.widgets['golden_cds_lib_view'] = view_golden_cds_btn  # Store view button
        golden_cds_row = QHBoxLayout()
        golden_cds_row.addWidget(self.widgets['golden_cds_lib'])
        golden_cds_row.addWidget(view_golden_cds_btn)
        golden_cds_row.addWidget(self.add_browse_button(self.widgets['golden_cds_lib'], file_filter="Library Files (*.lib);;All Files (*)"))
        layout.addRow("cds.lib:", golden_cds_row)

        self.widgets['radio_existed_golden'].toggled.connect(self.toggle_settings)
        group.setLayout(layout)
        return group

    def create_alpha_package_group(self) -> QGroupBox:
        """
        Create a group for configuring alpha package settings.

        Returns
        -------
        QGroupBox
            The group box widget for alpha package settings.
        """
        group = QGroupBox("Package Alpha")
        layout = QFormLayout()

        # Source selection
        self.widgets['radio_existed_alpha'] = QRadioButton("Existed Package")
        self.widgets['radio_new_alpha'] = QRadioButton("Create New")
        self.widgets['radio_existed_alpha'].setChecked(True)
        radio_group = QHBoxLayout()
        radio_group.addWidget(self.widgets['radio_existed_alpha'])
        radio_group.addWidget(self.widgets['radio_new_alpha'])
        layout.addRow("Source:", radio_group)

        # Alpha Package Path
        self.widgets['alpha_path'] = QLineEdit("./package_alpha")
        self.widgets['alpha_path'].setPlaceholderText("Enter alpha package path")
        self.widgets['alpha_path'].setObjectName("alpha_path")
        alpha_path_row = QHBoxLayout()
        alpha_path_row.addWidget(self.widgets['alpha_path'])
        alpha_path_row.addWidget(self.add_browse_button(self.widgets['alpha_path'], is_directory=True))
        layout.addRow("Package Path:", alpha_path_row)

        # Alpha CDF (should be a folder path)
        self.widgets['alpha_cdf'] = QLineEdit("<PACKAGE>/qa_<TECHLIB>__CDF")
        self.widgets['alpha_cdf'].setPlaceholderText("Enter alpha CDF folder path")
        self.widgets['alpha_cdf'].setObjectName("alpha_cdf")
        alpha_cdf_row = QHBoxLayout()
        alpha_cdf_row.addWidget(self.widgets['alpha_cdf'])
        alpha_cdf_row.addWidget(self.add_browse_button(self.widgets['alpha_cdf'], is_directory=True))
        layout.addRow("CDF Test Cases Folder:", alpha_cdf_row)

        # Alpha TA (should be a folder path)
        self.widgets['alpha_ta'] = QLineEdit("<PACKAGE>/qa_<TECHLIB>__TA")
        self.widgets['alpha_ta'].setPlaceholderText("Enter alpha TA folder path")
        self.widgets['alpha_ta'].setObjectName("alpha_ta")
        alpha_ta_row = QHBoxLayout()
        alpha_ta_row.addWidget(self.widgets['alpha_ta'])
        alpha_ta_row.addWidget(self.add_browse_button(self.widgets['alpha_ta'], is_directory=True))
        layout.addRow("TA Test Cases Folder:", alpha_ta_row)

        # Alpha Failed Rules
        self.widgets['alpha_failed_rules'] = QLineEdit("<PACKAGE>/failed_rules.xls")
        self.widgets['alpha_failed_rules'].setPlaceholderText("Enter failed rules file path")
        self.widgets['alpha_failed_rules'].setToolTip("Path to the file containing failed DRC rules")
        self.widgets['alpha_failed_rules'].setObjectName("alpha_failed_rules")
        view_alpha_rules_btn = QPushButton("View")
        view_alpha_rules_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))  # File icon for viewing
        view_alpha_rules_btn.clicked.connect(lambda: utils.open_file(self.widgets['alpha_failed_rules'].text(), logger))
        self.widgets['alpha_failed_rules_view'] = view_alpha_rules_btn  # Store view button
        alpha_failed_rules_row = QHBoxLayout()
        alpha_failed_rules_row.addWidget(self.widgets['alpha_failed_rules'])
        alpha_failed_rules_row.addWidget(view_alpha_rules_btn)
        alpha_failed_rules_row.addWidget(self.add_browse_button(self.widgets['alpha_failed_rules'], file_filter="Excel Files (*.xls *.xlsx);;All Files (*)"))
        layout.addRow("Failed Rules:", alpha_failed_rules_row)

        # PDK Version
        self.widgets['alpha_pdk_version'] = QComboBox()
        self.widgets['alpha_pdk_version'].addItems(["v1.0", "Undefined", "v2.0"])
        layout.addRow("PDK Version:", self.widgets['alpha_pdk_version'])

        # Alpha cds.lib
        self.widgets['alpha_cds_lib'] = QLineEdit("<PACKAGE>/cds.lib")
        self.widgets['alpha_cds_lib'].setPlaceholderText("Enter cds.lib file path")
        self.widgets['alpha_cds_lib'].setObjectName("alpha_cds_lib")
        view_alpha_cds_btn = QPushButton("View")
        view_alpha_cds_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))  # File icon for viewing
        view_alpha_cds_btn.clicked.connect(lambda: utils.open_file(self.widgets['alpha_cds_lib'].text(), logger))
        self.widgets['alpha_cds_lib_view'] = view_alpha_cds_btn  # Store view button
        alpha_cds_row = QHBoxLayout()
        alpha_cds_row.addWidget(self.widgets['alpha_cds_lib'])
        alpha_cds_row.addWidget(view_alpha_cds_btn)
        alpha_cds_row.addWidget(self.add_browse_button(self.widgets['alpha_cds_lib'], file_filter="Library Files (*.lib);;All Files (*)"))
        layout.addRow("cds.lib:", alpha_cds_row)

        self.widgets['radio_existed_alpha'].toggled.connect(self.toggle_settings)
        group.setLayout(layout)
        return group

    def create_setting_group(self) -> QGroupBox:
        """
        Create a group for additional QA settings.

        Returns
        -------
        QGroupBox
            The group box widget for QA settings.
        """
        group = QGroupBox("QA Settings")
        layout = QFormLayout()

        # Compare Types
        compare_types_layout = QHBoxLayout()
        self.widgets['compare_types'] = {}
        for qa_type in ['CDF', 'DRC', 'TA']:
            checkbox = QCheckBox(qa_type)
            self.widgets['compare_types'][qa_type] = checkbox
            checkbox.stateChanged.connect(self.toggle_compare_types)
            compare_types_layout.addWidget(checkbox)
        layout.addRow("Compare Types:", compare_types_layout)

        # Exclude Layers
        self.widgets['exclude_layers'] = QLineEdit("<PACKAGE>/exclude_layers.txt")
        self.widgets['exclude_layers'].setPlaceholderText("Enter path to exclude layers file")
        self.widgets['exclude_layers'].setObjectName("exclude_layers")
        view_excl_btn = QPushButton("View")
        view_excl_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))  # File icon for viewing
        view_excl_btn.clicked.connect(lambda: utils.open_file(self.widgets['exclude_layers'].text(), logger))
        self.widgets['exclude_layers_view'] = view_excl_btn  # Store view button
        excl_row = QHBoxLayout()
        excl_row.addWidget(self.widgets['exclude_layers'])
        excl_row.addWidget(view_excl_btn)
        excl_row.addWidget(self.add_browse_button(self.widgets['exclude_layers'], file_filter="Text Files (*.txt);;All Files (*)"))
        layout.addRow("Exclude Layers:", excl_row)

        # Run Directory
        self.widgets['run_dir'] = QLineEdit("./run_dir_compare")
        self.widgets['run_dir'].setPlaceholderText("Enter run directory path")
        self.widgets['run_dir'].setObjectName("run_dir")
        run_dir_row = QHBoxLayout()
        run_dir_row.addWidget(self.widgets['run_dir'])
        run_dir_row.addWidget(self.add_browse_button(self.widgets['run_dir'], is_directory=True))
        layout.addRow("Run Directory:", run_dir_row)

        # Cleanup Run Directory and RVE as checkboxes on one row
        options_row = QHBoxLayout()
        self.widgets['cleanup_run_dir'] = QCheckBox("Cleanup Run Directory")
        self.widgets['cleanup_run_dir'].setChecked(False)
        self.widgets['rve'] = QCheckBox("RVE")
        self.widgets['rve'].setChecked(False)
        options_row.addWidget(self.widgets['cleanup_run_dir'])
        options_row.addWidget(self.widgets['rve'])
        layout.addRow("Options:", options_row)

        group.setLayout(layout)
        return group

    def toggle_compare_types(self, state: int) -> None:
        """
        Callback for Compare Types checkboxes to update field enablement.

        Parameters
        ----------
        state : int
            The state of the checkbox.
        """
        self.toggle_settings()

    def toggle_settings(self) -> None:
        """
        Toggle field enablement based on source selection and Compare Types checkboxes.
        """
        is_golden_existed = self.widgets['radio_existed_golden'].isChecked()
        is_alpha_existed = self.widgets['radio_existed_alpha'].isChecked()
        cdf_checked = self.widgets['compare_types']['CDF'].isChecked()
        ta_checked = self.widgets['compare_types']['TA'].isChecked()
        drc_checked = self.widgets['compare_types']['DRC'].isChecked()

        # Golden Package Settings
        self.widgets['golden_path'].setEnabled(is_golden_existed)
        self.widgets['golden_path_browse'].setEnabled(is_golden_existed)
        self.widgets['golden_cdf'].setEnabled(is_golden_existed and cdf_checked)
        self.widgets['golden_cdf_browse'].setEnabled(is_golden_existed and cdf_checked)
        self.widgets['golden_ta'].setEnabled(is_golden_existed and ta_checked)
        self.widgets['golden_ta_browse'].setEnabled(is_golden_existed and ta_checked)
        self.widgets['golden_waived_rules'].setEnabled(drc_checked)
        self.widgets['golden_waived_rules_browse'].setEnabled(drc_checked)
        self.widgets['golden_waived_rules_view'].setEnabled(drc_checked)
        self.widgets['golden_pdk_version'].setEnabled(not is_golden_existed)
        self.widgets['golden_cds_lib'].setEnabled(not is_golden_existed)
        self.widgets['golden_cds_lib_browse'].setEnabled(not is_golden_existed)
        self.widgets['golden_cds_lib_view'].setEnabled(not is_golden_existed)

        # Alpha Package Settings
        self.widgets['alpha_path'].setEnabled(is_alpha_existed)
        self.widgets['alpha_path_browse'].setEnabled(is_alpha_existed)
        self.widgets['alpha_cdf'].setEnabled(is_alpha_existed and cdf_checked)
        self.widgets['alpha_cdf_browse'].setEnabled(is_alpha_existed and cdf_checked)
        self.widgets['alpha_ta'].setEnabled(is_alpha_existed and ta_checked)
        self.widgets['alpha_ta_browse'].setEnabled(is_alpha_existed and ta_checked)
        self.widgets['alpha_failed_rules'].setEnabled(is_alpha_existed and drc_checked)
        self.widgets['alpha_failed_rules_browse'].setEnabled(is_alpha_existed and drc_checked)
        self.widgets['alpha_failed_rules_view'].setEnabled(is_alpha_existed and drc_checked)
        self.widgets['alpha_pdk_version'].setEnabled(not is_alpha_existed)
        self.widgets['alpha_cds_lib'].setEnabled(not is_alpha_existed)
        self.widgets['alpha_cds_lib_browse'].setEnabled(not is_alpha_existed)
        self.widgets['alpha_cds_lib_view'].setEnabled(not is_alpha_existed)

        # QA Settings
        self.widgets['exclude_layers'].setEnabled(cdf_checked or ta_checked)
        self.widgets['exclude_layers_browse'].setEnabled(cdf_checked or ta_checked)
        self.widgets['exclude_layers_view'].setEnabled(cdf_checked or ta_checked)
        self.widgets['run_dir'].setEnabled(True)  # Run directory is always enabled
        self.widgets['run_dir_browse'].setEnabled(True)
        # No cleanup radio buttons to enable/disable

    def update_pdk_versions(self, versions: List[str]) -> None:
        """
        Update the list of PDK versions in the combo box.

        Parameters
        ----------
        versions : List[str]
            List of PDK version strings.
        """
        # Use the desired version if set, else fallback to current
        desired_golden = getattr(self, '_desired_golden_pdk_version', None)
        desired_alpha = getattr(self, '_desired_alpha_pdk_version', None)
        current_golden = desired_golden or self.widgets['golden_pdk_version'].currentText()
        current_alpha = desired_alpha or self.widgets['alpha_pdk_version'].currentText()
        self.widgets['golden_pdk_version'].clear()
        self.widgets['golden_pdk_version'].addItems(versions)
        self.widgets['alpha_pdk_version'].clear()
        self.widgets['alpha_pdk_version'].addItems(versions)
        if current_golden in versions:
            self.widgets['golden_pdk_version'].setCurrentText(current_golden)
        else:
            self.widgets['golden_pdk_version'].setCurrentText(versions[0] if versions else 'Undefined')
        if current_alpha in versions:
            self.widgets['alpha_pdk_version'].setCurrentText(current_alpha)
        else:
            self.widgets['alpha_pdk_version'].setCurrentText(versions[0] if versions else 'Undefined')
        # Clear the desired version after use
        if hasattr(self, '_desired_golden_pdk_version'):
            del self._desired_golden_pdk_version
        if hasattr(self, '_desired_alpha_pdk_version'):
            del self._desired_alpha_pdk_version

    def get_settings(self) -> Dict[str, Any]:
        """
        Return settings for saving, resolving relative paths using QA_MRVL_TECH_CWD.

        Returns
        -------
        dict
            Dictionary of settings.
        """
        base_dir = os.getenv('QA_MRVL_TECH_CWD', os.path.dirname(os.path.abspath(__file__)))  # Use env var or fallback to script dir
        settings = {
            'golden': {
                'source': 'existed' if self.widgets['radio_existed_golden'].isChecked() else 'new',
                'path': self.widgets['golden_path'].text(),
                'cdf': self.widgets['golden_cdf'].text(),
                'ta': self.widgets['golden_ta'].text(),
                'waived_rules': self.widgets['golden_waived_rules'].text(),
                'pdk_version': self.widgets['golden_pdk_version'].currentText(),
                'cds_lib': self.widgets['golden_cds_lib'].text(),
            },
            'alpha': {
                'source': 'existed' if self.widgets['radio_existed_alpha'].isChecked() else 'new',
                'path': self.widgets['alpha_path'].text(),
                'cdf': self.widgets['alpha_cdf'].text(),
                'ta': self.widgets['alpha_ta'].text(),
                'failed_rules': self.widgets['alpha_failed_rules'].text(),
                'pdk_version': self.widgets['alpha_pdk_version'].currentText(),
                'cds_lib': self.widgets['alpha_cds_lib'].text(),
            },
            'qa_settings': {
                'exclude_layers': self.widgets['exclude_layers'].text(),
                'compare_types': {qa_type: checkbox.isChecked() for qa_type, checkbox in self.widgets['compare_types'].items()},
                'run_dir': self.widgets['run_dir'].text(),
                'cleanup': self.widgets['cleanup_run_dir'].isChecked(),
                'rve': self.widgets['rve'].isChecked(),
            },
        }

        def resolve_and_validate_path(path, must_exist=False):
            if path and not os.path.isabs(path):
                resolved_path = os.path.normpath(os.path.join(base_dir, path))
            else:
                resolved_path = path
            valid, message = utils.validate_path(resolved_path, must_exist=must_exist)
            if not valid:
                logger.error(f"Resolved path invalid: {path} -> {resolved_path}: {message}")
            return resolved_path

        # Only validate enabled fields (shortened)
        for prefix, keys, must_exist, _ in [
            ('golden', ['path', 'cdf', 'ta', 'waived_rules', 'cds_lib'], True, {'cdf': True, 'ta': True}),
            ('alpha', ['path', 'cdf', 'ta', 'failed_rules', 'cds_lib'], True, {'cdf': True, 'ta': True}),
            ('qa_settings', ['exclude_layers'], True, {}),
            ('qa_settings', ['run_dir'], False, {}),
        ]:
            for key in keys:
                widget_key = f"{prefix}_{key}" if f"{prefix}_{key}" in self.widgets else key
                widget = self.widgets.get(widget_key)
                if widget is not None and widget.isEnabled():
                    if prefix in settings and key in settings[prefix]:
                        settings[prefix][key] = resolve_and_validate_path(settings[prefix][key], must_exist=must_exist)

        return settings

    def set_settings(self, settings: Dict[str, Any]) -> None:
        """
        Load settings into widgets.

        Parameters
        ----------
        settings : dict
            Settings to load into the UI.
        """
        golden_settings = settings.get('golden', {})
        alpha_settings = settings.get('alpha', {})
        qa_settings = settings.get('qa_settings', {})

        # Store desired PDK versions for use after update_pdk_versions
        self._desired_golden_pdk_version = golden_settings.get('pdk_version', 'Undefined')
        self._desired_alpha_pdk_version = alpha_settings.get('pdk_version', 'Undefined')

        source_golden = golden_settings.get('source', 'existed')
        self.widgets['radio_existed_golden'].setChecked(source_golden == 'existed')
        self.widgets['radio_new_golden'].setChecked(source_golden == 'new')
        self.widgets['golden_path'].setText(golden_settings.get('path', './package_golden'))
        self.widgets['golden_cdf'].setText(golden_settings.get('cdf', '<PACKAGE>/qa_<TECHLIB>__CDF'))
        self.widgets['golden_ta'].setText(golden_settings.get('ta', '<PACKAGE>/qa_<TECHLIB>__TA'))
        self.widgets['golden_waived_rules'].setText(golden_settings.get('waived_rules', '<PACKAGE>/waived_rules_drc.xls'))
        # Do not setCurrentText here, will be handled after update_pdk_versions
        self.widgets['golden_cds_lib'].setText(golden_settings.get('cds_lib', '<PACKAGE>/cds.lib'))

        source_alpha = alpha_settings.get('source', 'existed')
        self.widgets['radio_existed_alpha'].setChecked(source_alpha == 'existed')
        self.widgets['radio_new_alpha'].setChecked(source_alpha == 'new')
        self.widgets['alpha_path'].setText(alpha_settings.get('path', './package_alpha'))
        self.widgets['alpha_cdf'].setText(alpha_settings.get('cdf', '<PACKAGE>/qa_<TECHLIB>__CDF'))
        self.widgets['alpha_ta'].setText(alpha_settings.get('ta', '<PACKAGE>/qa_<TECHLIB>__TA'))
        self.widgets['alpha_failed_rules'].setText(alpha_settings.get('failed_rules', '<PACKAGE>/failed_rules.xls'))
        # Do not setCurrentText here, will be handled after update_pdk_versions
        self.widgets['alpha_cds_lib'].setText(alpha_settings.get('cds_lib', '<PACKAGE>/cds.lib'))

        self.widgets['exclude_layers'].setText(qa_settings.get('exclude_layers', '<PACKAGE>/exclude_layers.txt'))
        for qa_type, enabled in qa_settings.get('compare_types', {}).items():
            if qa_type in self.widgets['compare_types']:
                self.widgets['compare_types'][qa_type].setChecked(enabled)
        self.widgets['run_dir'].setText(qa_settings.get('run_dir', './run_dir_compare'))
        self.widgets['cleanup_run_dir'].setChecked(qa_settings.get('cleanup', False))
        self.widgets['rve'].setChecked(qa_settings.get('rve', False))

        self.toggle_settings()

    class Worker(QThread):
        progress = pyqtSignal(str)
        finished = pyqtSignal(bool, str)
        error = pyqtSignal(str)
        log_output = pyqtSignal(str)
        cache_db_ready = pyqtSignal(object)  # New signal for main thread db assignment

        def __init__(self, parent: QWidget, settings: Dict[str, Any]) -> None:
            """
            Parameters
            ----------
            parent : QWidget
                Parent widget.
            settings : dict
                Settings for the worker.
            """
            super().__init__(parent)
            self.parent = parent
            self.settings = settings
            self._is_running = True
            self.processes = []  # Track subprocesses for stopping

        def stop(self) -> None:
            """
            Flag to stop the thread and terminate subprocesses (including all children).
            """
            import os
            import signal
            self._is_running = False
            for proc in self.processes:
                try:
                    # Kill the whole process group
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    proc.wait(timeout=10)
                    logger.info(f"Terminated process group for PID {proc.pid}")
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    logger.info(f"Force killed process group for PID {proc.pid}")
                except Exception as e:
                    logger.error(f"Failed to terminate process group for PID {proc.pid}: {e}. Traceback: {traceback.format_exc()}")
            self.processes.clear()

        def run_subprocess(self, script_path: Any, run_dir: Any) -> bool:
            """
            Execute a script using subprocess and stream stdout.

            Parameters
            ----------
            script_path : Any
                Path to the script to execute.
            run_dir : Any
                Directory to run the script in.

            Returns
            -------
            bool
                True if the subprocess succeeded, False otherwise.
            """
            try:
                import os
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
                    preexec_fn=os.setsid  # Start new process group
                )
                self.processes.append(proc)
                logger.info(f"Started subprocess PID {proc.pid} for script {script_path}")
                self.progress.emit(f"Executing script: {script_path}")

                # Stream stdout in real-time
                while self._is_running:
                    line = proc.stdout.readline()
                    if line:
                        self.log_output.emit(line.strip())
                    if proc.poll() is not None:
                        break

                # Close stdout immediately if stopped
                if not self._is_running:
                    proc.stdout.close()
                    returncode = proc.wait()
                    logger.info(f"Subprocess PID {proc.pid} stopped by user")
                    if proc in self.processes:  # Avoid ValueError if stop cleared processes
                        self.processes.remove(proc)
                    return False

                # Process remaining output only if still running
                for line in proc.stdout:
                    if line and self._is_running:
                        self.log_output.emit(line.strip())
                proc.stdout.close()
                returncode = proc.wait()
                if proc in self.processes:  # Avoid ValueError
                    self.processes.remove(proc)
                if returncode != 0:
                    logger.error(f"Subprocess PID {proc.pid} failed with return code {returncode}")
                return returncode == 0
            except Exception as e:
                error_message = f"Failed to execute {script_path}: {str(e)}. Traceback: {traceback.format_exc()}"
                logger.error(error_message)
                self.error.emit(error_message)
                if 'proc' in locals() and proc in self.processes:
                    self.processes.remove(proc)
                return False

        def run_create_packages(self, run_dir: Any) -> bool:
            """
            Run package creation tasks.

            Parameters
            ----------
            run_dir : Any
                Directory to run the package creation in.

            Returns
            -------
            bool
                True if successful, False otherwise.
            """
            try:
                compare_settings = self.settings.get('compare_settings', {})
                for mode in ['golden', 'alpha']:
                    if not self._is_running:
                        self.progress.emit(f"Package creation for {mode} stopped")
                        return False

                    if compare_settings.get(mode, {}).get('source', 'existed') == 'new':
                        self.progress.emit(f"Generating run script for {mode} package")
                        pkg_name = f"package_{mode}"
                        file_name = f"run_create_package_{mode}.csh"
                        file_run = run_dir / file_name
                        file_log = file_run.with_name(f"{file_run.name}.log")
                        utils.update_debug_log(file_log, logger)
                        context = {
                            "MODE": mode,
                            "DB": self.cache_db,
                            "PKG_NAME": pkg_name,
                            "QA_MRVL_TECH": QA_MRVL_TECH,
                            "RUN_DIR": run_dir,
                            "SETTINGS": self.settings,
                            "LOG_FILE": file_log,
                        }
                        renderer = TemplateRenderer(TEMPLATE_DIR_FE)
                        renderer.render("run_create_package.csh.j2", file_run, context, chmod=True)
                        self.progress.emit(f"Generated run script: {file_run}")

                        self.progress.emit(f"Executing script: {file_run}")
                        if not self._is_running:
                            self.progress.emit(f"Execution of {file_run} stopped")
                            return False
                        success = self.run_subprocess(file_run, run_dir)
                        if not success:
                            if not self._is_running:
                                self.progress.emit(f"Execution of {file_run} stopped")
                                return False
                            error_message = f"Failed to execute {file_run}"
                            logger.error(error_message)
                            self.error.emit(error_message)
                            return False
                        self.progress.emit(f"Completed execution of {file_run}")
                return True
            except Exception as e:
                error_message = f"Failed to create packages: {str(e)}. Traceback: {traceback.format_exc()}"
                logger.error(error_message)
                self.error.emit(error_message)
                return False

        def run_compare_packages(self, run_dir: Any) -> bool:
            """
            Run package comparison tasks.

            Parameters
            ----------
            run_dir : Any
                Directory to run the package comparison in.

            Returns
            -------
            bool
                True if successful, False otherwise.
            """
            try:
                compare_settings = self.settings.get('compare_settings', {})
                techlib = self.settings.get('create_package_settings', {}).get('required_settings', {}).get('techlib', 'Undefined')

                for mode in ['golden', 'alpha']:
                    if not self._is_running:
                        self.progress.emit(f"Package comparison for {mode} stopped")
                        return False
                    if compare_settings.get(mode, {}).get('source', 'new') == 'new':
                        self.progress.emit(f"Collecting package structure for {mode} package")
                        compare_settings[mode]['path'] = run_dir / 'packages' / f"package_{mode}"
                        compare_settings[mode]['cdf'] = run_dir / 'packages' / f"package_{mode}" / f"qa_{techlib}__CDF"
                        compare_settings[mode]['ta'] = run_dir / 'packages' / f"package_{mode}" / f"qa_{techlib}__TA"
                        compare_settings[mode]['pdk_version'] = compare_settings[mode].get('pdk_version', 'Undefined')
                        compare_settings[mode]['cds_lib'] = compare_settings[mode].get('cds_lib', 'Undefined')
                        if mode == 'alpha':
                            compare_settings[mode]['failed_rules'] = run_dir / 'packages' / f"package_{mode}" / enum.XLS.FR_FILE_NAME

                run_dir = Path(compare_settings['qa_settings']['run_dir'])
                run_dir.mkdir(parents=True, exist_ok=True)
                self.progress.emit(f"Created run directory: {run_dir}")

                pkg_name = "compare_packages"
                file_name = "run_compare_packages.csh"
                file_run = run_dir / file_name
                file_log = file_run.with_name(f"{file_run.name}.log")
                utils.update_debug_log(file_log, logger)
                context = {
                    "MODE": "compare",
                    "DB": self.cache_db,
                    "PKG_NAME": pkg_name,
                    "QA_MRVL_TECH": QA_MRVL_TECH,
                    "RUN_DIR": run_dir,
                    "SETTINGS": self.settings,
                    "LOG_FILE": file_log,
                }
                renderer = TemplateRenderer(TEMPLATE_DIR_FE)
                renderer.render("run_compare_packages.csh.j2", file_run, context, chmod=True)
                self.progress.emit(f"Generated script compare package: {file_run}")

                if self._is_running:
                    success = self.run_subprocess(file_run, run_dir)
                    logger.debug(f"Subprocess for {file_run} finished with status: {success}")
                    if success:
                        self.progress.emit(f"Completed package comparison: {file_run}")
                        return True
                    else:
                        self.progress.emit(f"Execution of {file_run} failed")
                        if not self._is_running:
                            self.progress.emit(f"Package comparison stopped")
                            return False
                        error_message = f"Failed to execute {file_run}"
                        logger.error(error_message)
                        self.error.emit(error_message)
                        return False
                else:
                    self.progress.emit(f"Package comparison stopped")
                    return False
            except Exception as e:
                error_message = f"Failed to compare packages: {str(e)}. Traceback: {traceback.format_exc()}"
                logger.error(error_message)
                self.error.emit(error_message)
                return False

        def run(self) -> None:
            """
            Main thread execution logic.
            """
            try:
                utils.update_qa_run_status(True, logger)
                compare_settings = self.settings.get('compare_settings', {})
                qa_settings = compare_settings.get('qa_settings', {})
                cleanup = qa_settings.get('cleanup', False)
                run_dir = Path(qa_settings.get('run_dir', './output_compare_package'))
                # Backup run directory if cleanup is enabled
                if cleanup and os.path.exists(run_dir):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_dir = f"{run_dir}_backup_{timestamp}"
                    try:
                        shutil.move(run_dir, backup_dir)
                        logger.info(f"Moved run directory to backup: {backup_dir}")
                    except Exception as e:
                        logger.error(f"Failed to move run directory to backup: {e}. Traceback: {traceback.format_exc()}")
                        return  # Do not return a value
                # Check if parent directory is writable before mkdir
                parent_dir = run_dir.parent
                if not utils.is_writable_dir(str(parent_dir)):
                    error_message = f"Permission denied: Cannot write to directory {parent_dir}. Please check your permissions."
                    logger.error(error_message)
                    self.error.emit(error_message)
                    return  # Do not return a value
                run_dir.mkdir(parents=True, exist_ok=True)
                                
                # Cache database is at run_dir / ".cache.db"
                self.cache_db = run_dir / ".cache.db"
                if not self.cache_db.exists():
                    db_obj = Database(self.cache_db)
                    db_obj.create_tables()
                
                # Emit signal for main thread to handle db assignment
                self.cache_db_ready.emit(self.cache_db)
                
                utils.update_qa_run_dir(run_dir, logger)

                if not self._is_running:
                    self.finished.emit(False, "Task stopped.")
                    return

                # Run package creation
                success = self.run_create_packages(run_dir)
                if not success:
                    if not self._is_running:
                        self.finished.emit(False, "Task stopped.")
                    return

                # Run package comparison
                success = self.run_compare_packages(run_dir)
                if success:
                    self.progress.emit(f"Completed package comparison in {run_dir}")
                    self.finished.emit(True, "Completed package comparison!")
                else:
                    if not self._is_running:
                        self.finished.emit(False, "Task stopped.")
            except Exception as e:
                error_message = f"Failed to run QA: {str(e)}. Traceback: {traceback.format_exc()}"
                logger.error(error_message)
                self.error.emit(error_message)
                self.finished.emit(False, "Task failed.")
            finally:
                utils.update_qa_run_status(False, logger)

    def pre_run_validation(self) -> bool:
        """
        Perform pre-run validations before starting the compare process.
        Returns
        -------
        bool
            True if all validations pass, False otherwise.
        """
        # Check if golden and alpha cds.lib are the same, only if both fields are enabled
        golden_widget = self.widgets.get('golden_cds_lib')
        alpha_widget = self.widgets.get('alpha_cds_lib')
        if golden_widget is not None and alpha_widget is not None:
            if golden_widget.isEnabled() and alpha_widget.isEnabled():
                golden_cds_lib = golden_widget.text().strip()
                alpha_cds_lib = alpha_widget.text().strip()
                golden_cds_lib_abs = os.path.abspath(golden_cds_lib)
                alpha_cds_lib_abs = os.path.abspath(alpha_cds_lib)
                if golden_cds_lib_abs == alpha_cds_lib_abs:
                    QMessageBox.warning(self, "Validation Error", "Golden and Alpha cds.lib paths are the same. Please select different files.")
                    return False

        # List of (widget_key, label, must_be_dir) to check
        file_fields = [
            ('golden_cds_lib', 'Golden cds.lib', False),
            ('alpha_cds_lib', 'Alpha cds.lib', False),
            ('golden_cdf', 'Golden CDF folder', True),
            ('alpha_cdf', 'Alpha CDF folder', True),
            ('golden_ta', 'Golden TA folder', True),
            ('alpha_ta', 'Alpha TA folder', True),
            ('golden_waived_rules', 'Golden Waived Rules', False),
            ('alpha_failed_rules', 'Alpha Failed Rules', False),
            ('exclude_layers', 'Exclude Layers', False),
            ('run_dir', 'Run Directory', True),
        ]
        for key, label, must_be_dir in file_fields:
            widget = self.widgets.get(key)
            if widget is not None and widget.isEnabled():
                path = widget.text().strip()
                if not path:
                    QMessageBox.warning(self, "Validation Error", f"{label} path is empty.")
                    return False
                abs_path = os.path.abspath(path)
                if must_be_dir:
                    if not os.path.isdir(abs_path):
                        QMessageBox.warning(self, "Validation Error", f"{label} directory does not exist: {abs_path}")
                        return False
                else:
                    if not os.path.exists(abs_path):
                        QMessageBox.warning(self, "Validation Error", f"{label} file does not exist: {abs_path}")
                        return False
        return True

    def run_callback(self) -> None:
        """
        Run QA tasks for the Compare tab in a separate thread.
        """
        # Pre-run validation
        if not self.pre_run_validation():
            logger.error("Pre-run validation failed, cannot start QA tasks.")
            return

        # Set Debug tab active (index 2)
        if hasattr(self.main_window, 'tabs'):
            self.main_window.tabs.setCurrentIndex(2)

        try:
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

            self.start_time = datetime.now()  # Record start time
            self.end_time = None

            self.worker = self.Worker(self, settings)
            self.worker.progress.connect(self.update_status)
            self.worker.finished.connect(self.task_finished)
            self.worker.error.connect(self.task_error)
            # Connect log_output signal to DebugTab's update_log
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

    def update_status(self, message: str) -> None:
        """
        Update the status label with progress messages.

        Parameters
        ----------
        message : str
            The progress message to display.
        """
        self.main_window.status_label.setText(f"Status: {message}")
        logger.info(message)  # Log the progress message

    def task_finished(self, success: bool, message: str) -> None:
        """
        Handle task completion and send jobs table via email.
        Also update status of all RUNNING and PENDING jobs to STOPPED if task was stopped.

        Parameters
        ----------
        success : bool
            Whether the task succeeded.
        message : str
            Completion message.
        """
        self.main_window.status_label.setText(f"Status: {message}")
        self.run_btn.setEnabled(True)
        self.verify_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.worker = None

        self.end_time = datetime.now()  # Record end time

        # --- Update job statuses if stopped ---
        if message == "Task stopped.":
            try:
                with open("./last_qa_settings.json", 'r') as f:
                    settings = json.load(f)
                run_dir = Path(settings.get('compare_settings', {}).get('qa_settings', {}).get('run_dir', './output_compare_package'))
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
            run_dir = Path(settings.get('compare_settings', {}).get('qa_settings', {}).get('run_dir', './output_compare_package'))
            db_path = run_dir / ".cache.db"
            recipient = os.getenv('USER', 'user') + '@marvell.com'
            send_jobs_email(
                settings,
                run_dir,
                db_path,
                email_recipient=recipient,
                cc_emails=["nguyenv@marvell.com", "nquan@marvell.com"],
                logger=logger,
                title=f"[QA MRVL Techlib] Compare Package: {message}",
                start_time=self.start_time,
                end_time=self.end_time
            )
            logger.info("Jobs table email sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send jobs table email: {e}")

        if success:
            QMessageBox.information(self, "Success", message)
        elif message == "Task stopped.":
            QMessageBox.information(self, "Info", "QA task Compare Packages was stopped by the user.")
        else:
            QMessageBox.warning(self, "Warning", message)
        logger.info(f"Task finished: {message}")

    def task_error(self, error_message: str) -> None:
        """
        Handle errors from the worker thread.

        Parameters
        ----------
        error_message : str
            The error message to display.
        """
        self.main_window.status_label.setText(f"Status: {error_message}")
        self.run_btn.setEnabled(True)
        self.verify_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.worker = None
        self.end_time = datetime.now()  # Record end time
        QMessageBox.critical(self, "Error", error_message)
        logger.error(f"Task error: {error_message}")

    def stop_callback(self) -> None:
        """
        Stop QA tasks for the Compare Packages tab and terminate associated processes in a worker thread.
        Updates the status_label to show progress of the kill process.
        """
        if self.worker and self.worker.isRunning():
            logger.info("User requested to stop QA tasks")
            self.worker.stop()
            self.main_window.status_label.setText("Status: Stopping QA tasks...")
            self.stop_btn.setEnabled(False)

            settings = self.get_settings()
            run_dir = Path(settings['qa_settings'].get('run_dir', './output_qa'))
            # Start StopWorker thread
            self.stop_worker = StopWorker(run_dir, enum, self.main_window.status_label.setText)
            self.stop_worker.finished.connect(lambda msg: QMessageBox.information(self, "Info", msg))
            self.stop_worker.error.connect(lambda err: QMessageBox.warning(self, "Warning", f"Error stopping tasks: {err}"))
            self.stop_worker.start()
        else:
            self.main_window.status_label.setText("Status: No tasks running")
            QMessageBox.information(self, "Info", "No tasks are currently running.")

    def verify_callback(self) -> None:
        """
        Verify settings for the Compare tab.
        """
        print("Compare: Verification not implemented")
        self.main_window.status_label.setText("Status: Compare verification not implemented")
        QMessageBox.information(self, "Info", "Compare verification functionality is not yet implemented.")

class StopWorker(QThread):
    """
    Worker thread to handle stopping QA tasks and terminating processes without blocking the GUI.
    """
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, run_dir: Path, enum, status_callback):
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
            try:
                pids = db.list_pids()
            except Exception as e:
                if "no such table" in str(e):
                    self.status_callback(f"Status: No running jobs table found in database for {self.run_dir}.")
                    self.finished.emit("No running jobs found.")
                    return
                else:
                    raise
            if not pids:
                self.status_callback(f"Status: No running jobs found in database for {self.run_dir}.")
                self.finished.emit("No running jobs found.")
                return
            killed = 0
            for row in pids:
                pid = row['pid']
                try:
                    subprocess.run(['sgdel', str(pid)], check=True, capture_output=True)
                    self.status_callback(f"Status: Stopping job with PID {pid}...")
                    logger.info(f"Stopping job with PID {pid}...")
                    # Remove the PID from the database after stopping
                    logger.debug(f"Removing PID {pid} from database")
                    db.delete_pid(pid)
                    killed += 1
                except Exception as e:
                    logger.error(f"Failed to stop job with PID {pid}: {e}")
                    self.status_callback(f"Status: Failed to stop job with PID {pid}: {e}")
                    # Continue to attempt to stop other jobs even if one fails
                    continue
            self.status_callback(f"Status: Stopped {killed} running jobs from database.")
            self.finished.emit(f"Stopped {killed} running jobs.")
        except Exception as e:
            import traceback
            logger.error(f"Error while stopping jobs from database in {self.run_dir}: {e}\n{traceback.format_exc()}")
            self.error.emit(str(e))