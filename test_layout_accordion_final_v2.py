import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QStatusBar, 
                             QProgressBar, QTableWidget, QTableWidgetItem,
                             QCheckBox, QComboBox, QSpinBox, QGroupBox, QFormLayout,
                             QFrame, QScrollArea, QTextEdit, QSlider, QLineEdit, 
                             QTreeWidget, QTreeWidgetItem, QSplitter, QStackedWidget,
                             QMessageBox, QFileDialog, QDialogButtonBox, QDialog, 
                             QRadioButton, QTabWidget)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPalette

class CollapsibleGroupBox(QGroupBox):
    """Custom collapsible group box"""
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(True)
        self.toggled.connect(self.on_toggled)
        self.content_widget = None
        
    def on_toggled(self, checked):
        """Toggle content visibility"""
        if self.content_widget:
            self.content_widget.setVisible(checked)
        else:
            # Hide/show all child widgets
            for child in self.findChildren(QWidget):
                if child.parent() == self:
                    child.setVisible(checked)

class LeftNavigationPanel(QWidget):
    """Left side navigation panel"""
    item_selected = pyqtSignal(str, str)  # section, subsection
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedWidth(180)
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Title
        title_label = QLabel("QA MRVL Tool")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white; margin-bottom: 10px;")
        
        # Navigation tree
        self.nav_tree = QTreeWidget()
        self.nav_tree.setHeaderHidden(True)
        self.nav_tree.setRootIsDecorated(True)
        self.nav_tree.setIndentation(15)
        
        # Add navigation items - Updated for accordion layout
        self.create_navigation_items()
        
        # Connect selection change
        self.nav_tree.itemClicked.connect(self.on_item_clicked)
        
        layout.addWidget(title_label)
        layout.addWidget(self.nav_tree)
        
        self.setLayout(layout)
    
    def create_navigation_items(self):
        """Create navigation tree items for accordion layout"""
        # Settings & Actions (combined)
        settings_item = QTreeWidgetItem(["⚙️ Settings & Actions"])
        settings_item.setData(0, Qt.UserRole, ("settings_actions", "main"))
        self.nav_tree.addTopLevelItem(settings_item)
        
        # Debug
        debug_item = QTreeWidgetItem(["🐛 Debug"])
        debug_item.setData(0, Qt.UserRole, ("debug", "main"))
        self.nav_tree.addTopLevelItem(debug_item)
        
        # Select first item by default
        self.nav_tree.setCurrentItem(settings_item)
    
    def on_item_clicked(self, item, column):
        """Handle navigation item click"""
        data = item.data(0, Qt.UserRole)
        if data:
            section, subsection = data
            self.item_selected.emit(section, subsection)

class AccordionSettingsPanel(QScrollArea):
    """Top accordion settings panel"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setup_ui()
        
    def setup_ui(self):
        self.setWidgetResizable(True)
        self.setMaximumHeight(450)  # Limit height for top panel
        
        # Container widget
        container = QWidget()
        layout = QVBoxLayout()
        
        # Required Settings Group (Always expanded)
        self.required_group = CollapsibleGroupBox("📋 Required Settings")
        required_layout = QFormLayout()
        
        # Techlib
        self.settings_techlib_combo = QComboBox()
        self.settings_techlib_combo.addItems(["gf12lpp", "gf22fdx", "gf28hpk", "gf12lp", "gf14lpp"])
        required_layout.addRow("Techlib:", self.settings_techlib_combo)
        
        # QA Types
        qa_types_layout = QHBoxLayout()
        self.settings_cdf_cb = QCheckBox("CDF")
        self.settings_drc_cb = QCheckBox("DRC")
        self.settings_ta_cb = QCheckBox("TA")
        self.settings_cdf_cb.setChecked(True)
        qa_types_layout.addWidget(self.settings_cdf_cb)
        qa_types_layout.addWidget(self.settings_drc_cb)
        qa_types_layout.addWidget(self.settings_ta_cb)
        required_layout.addRow("QA Types:", qa_types_layout)
        
        # QA Settings file
        qa_setting_layout = QHBoxLayout()
        self.settings_qa_setting_edit = QLineEdit()
        self.settings_qa_setting_edit.setPlaceholderText("Enter path to QA setting file")
        view_qa_btn = QPushButton("View")
        browse_qa_btn = QPushButton("Browse")
        qa_setting_layout.addWidget(self.settings_qa_setting_edit)
        qa_setting_layout.addWidget(view_qa_btn)
        qa_setting_layout.addWidget(browse_qa_btn)
        required_layout.addRow("QA Settings:", qa_setting_layout)
        
        # Virtuoso Command
        self.settings_virtuoso_cmd_edit = QLineEdit()
        self.settings_virtuoso_cmd_edit.setPlaceholderText("Enter Virtuoso command")
        required_layout.addRow("Virtuoso Command:", self.settings_virtuoso_cmd_edit)
        
        # Run Directory
        run_dir_layout = QHBoxLayout()
        self.settings_run_dir_edit = QLineEdit("./output_qa")
        self.settings_run_dir_edit.setPlaceholderText("Enter run directory path")
        browse_run_dir_btn = QPushButton("Browse")
        run_dir_layout.addWidget(self.settings_run_dir_edit)
        run_dir_layout.addWidget(browse_run_dir_btn)
        required_layout.addRow("Run Directory:", run_dir_layout)
        
        # Cleanup Run Directory option (moved from advanced settings)
        self.settings_cleanup_cb = QCheckBox("Cleanup Run Directory")
        self.settings_cleanup_cb.setChecked(False)
        required_layout.addRow("", self.settings_cleanup_cb)
        
        self.required_group.setLayout(required_layout)
        
        # File Paths Group (Collapsible)
        self.paths_group = CollapsibleGroupBox("📁 File Paths")
        self.paths_group.setChecked(False)  # Initially collapsed
        paths_layout = QFormLayout()
        
        # PDK Configs
        pdk_config_layout = QHBoxLayout()
        self.settings_pdk_config_edit = QLineEdit()
        self.settings_pdk_config_edit.setPlaceholderText("PDK configuration file (auto-set)")
        self.settings_pdk_config_edit.setReadOnly(True)
        load_pdk_btn = QPushButton("Load")
        view_pdk_btn = QPushButton("View")
        pdk_config_layout.addWidget(self.settings_pdk_config_edit)
        pdk_config_layout.addWidget(load_pdk_btn)
        pdk_config_layout.addWidget(view_pdk_btn)
        paths_layout.addRow("PDK Configs:", pdk_config_layout)
        
        # .cdsinit
        cdsinit_layout = QHBoxLayout()
        self.settings_cdsinit_edit = QLineEdit()
        self.settings_cdsinit_edit.setPlaceholderText("Enter path to cdsinit local file")
        view_cdsinit_btn = QPushButton("View")
        browse_cdsinit_btn = QPushButton("Browse")
        cdsinit_layout.addWidget(self.settings_cdsinit_edit)
        cdsinit_layout.addWidget(view_cdsinit_btn)
        cdsinit_layout.addWidget(browse_cdsinit_btn)
        paths_layout.addRow(".cdsinit:", cdsinit_layout)
        
        self.paths_group.setLayout(paths_layout)
        
        # DRC Settings Group (Collapsible)
        self.settings_drc_group = CollapsibleGroupBox("🔧 DRC Settings")
        self.settings_drc_group.setChecked(False)  # Initially collapsed
        drc_layout = QFormLayout()
        
        # Project MPV
        proj_mpv_layout = QHBoxLayout()
        self.settings_proj_mpv_edit = QLineEdit()
        self.settings_proj_mpv_edit.setPlaceholderText("Enter project MPV")
        view_proj_btn = QPushButton("View")
        browse_proj_btn = QPushButton("Browse")
        proj_mpv_layout.addWidget(self.settings_proj_mpv_edit)
        proj_mpv_layout.addWidget(view_proj_btn)
        proj_mpv_layout.addWidget(browse_proj_btn)
        drc_layout.addRow("Project MPV:", proj_mpv_layout)
        
        # mpvopt DRC
        mpvopts_layout = QHBoxLayout()
        self.settings_mpvopts_edit = QLineEdit()
        self.settings_mpvopts_edit.setPlaceholderText("Enter mpvopts for DRC")
        view_mpvopts_btn = QPushButton("View")
        browse_mpvopts_btn = QPushButton("Browse")
        mpvopts_layout.addWidget(self.settings_mpvopts_edit)
        mpvopts_layout.addWidget(view_mpvopts_btn)
        mpvopts_layout.addWidget(browse_mpvopts_btn)
        drc_layout.addRow("mpvopt DRC:", mpvopts_layout)
        
        # Runcalx Version
        self.settings_runcalx_edit = QLineEdit()
        self.settings_runcalx_edit.setPlaceholderText("Enter Runcalx version")
        drc_layout.addRow("Runcalx Version:", self.settings_runcalx_edit)
        
        self.settings_drc_group.setLayout(drc_layout)
        self.settings_drc_group.setEnabled(False)  # Initially disabled
        
        # Advanced Settings Button (replaced accordion with dialog)
        advanced_button_layout = QHBoxLayout()
        advanced_button_layout.addStretch()
        self.advanced_settings_btn = QPushButton("⚙️ Advanced Settings...")
        self.advanced_settings_btn.clicked.connect(self.show_advanced_settings_dialog)
        advanced_button_layout.addWidget(self.advanced_settings_btn)
        
        # Settings Actions (moved to top for better UX)
        settings_actions_layout = QHBoxLayout()
        save_settings_btn = QPushButton("💾 Save")
        load_settings_btn = QPushButton("📂 Load")
        reset_btn = QPushButton("🔄 Reset")
        
        save_settings_btn.clicked.connect(self.save_settings)
        load_settings_btn.clicked.connect(self.load_settings)
        reset_btn.clicked.connect(self.reset_settings)
        
        settings_actions_layout.addWidget(save_settings_btn)
        settings_actions_layout.addWidget(load_settings_btn)
        settings_actions_layout.addWidget(reset_btn)
        settings_actions_layout.addStretch()
        
        # Connect DRC checkbox to enable/disable DRC group
        self.settings_drc_cb.toggled.connect(self.settings_drc_group.setEnabled)
        
        layout.addWidget(self.required_group)
        layout.addLayout(settings_actions_layout)  # Settings actions after required settings
        layout.addWidget(self.paths_group)
        layout.addWidget(self.settings_drc_group)
        layout.addLayout(advanced_button_layout)
        layout.addStretch()
        
        container.setLayout(layout)
        self.setWidget(container)
        
        # Initialize advanced settings values
        self.settings_max_instances_value = "50"
        self.settings_log_level_value = "INFO"
        self.settings_max_jobs_value = "100"
        self.settings_retries_value = "2"
        self.settings_save_express_value = True
        # Cleanup is now handled by main checkbox, not advanced settings
    
    def show_advanced_settings_dialog(self):
        """Show advanced settings dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Advanced Settings")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # Form layout for settings
        form_layout = QFormLayout()
        
        # Max Instances Per Cell View
        max_instances_edit = QLineEdit(self.settings_max_instances_value)
        max_instances_edit.setPlaceholderText("Enter max instances per cellview")
        form_layout.addRow("Max Instances Per Cell View:", max_instances_edit)
        
        # Log Level
        log_level_combo = QComboBox()
        log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_level_combo.setCurrentText(self.settings_log_level_value)
        form_layout.addRow("Log Level:", log_level_combo)
        
        # Max Jobs
        max_jobs_layout = QHBoxLayout()
        max_jobs_edit = QLineEdit(self.settings_max_jobs_value)
        max_jobs_edit.setPlaceholderText("Enter max jobs")
        check_license_btn = QPushButton("Check")
        max_jobs_layout.addWidget(max_jobs_edit)
        max_jobs_layout.addWidget(check_license_btn)
        form_layout.addRow("Max Jobs:", max_jobs_layout)
        
        # Max retries
        retries_edit = QLineEdit(self.settings_retries_value)
        retries_edit.setPlaceholderText("Enter number of retries")
        form_layout.addRow("Max retries:", retries_edit)
        
        # Options
        options_layout = QHBoxLayout()
        save_express_cb = QCheckBox("Save .expressPCell")
        # Removed cleanup_cb since it's now in main settings
        save_express_cb.setChecked(self.settings_save_express_value)
        options_layout.addWidget(save_express_cb)
        form_layout.addRow("Options:", options_layout)
        
        layout.addLayout(form_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            # Save the values
            self.settings_max_instances_value = max_instances_edit.text()
            self.settings_log_level_value = log_level_combo.currentText()
            self.settings_max_jobs_value = max_jobs_edit.text()
            self.settings_retries_value = retries_edit.text()
            self.settings_save_express_value = save_express_cb.isChecked()
            # Cleanup value is now handled by the main checkbox in settings
    
    def save_settings(self):
        """Save current settings to file"""
        QMessageBox.information(self, "Save Settings", "Settings saved successfully!")
    
    def load_settings(self):
        """Load settings from file"""
        QMessageBox.information(self, "Load Settings", "Settings loaded successfully!")
    
    def reset_settings(self):
        """Reset settings to defaults"""
        reply = QMessageBox.question(self, "Reset Settings", 
                                   "Are you sure you want to reset all settings to defaults?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Reset all form fields to defaults
            self.settings_techlib_combo.setCurrentIndex(0)
            self.settings_cdf_cb.setChecked(True)
            self.settings_drc_cb.setChecked(False)
            self.settings_ta_cb.setChecked(False)
            self.settings_qa_setting_edit.clear()
            self.settings_pdk_config_edit.clear()
            self.settings_virtuoso_cmd_edit.clear()
            self.settings_cdsinit_edit.clear()
            self.settings_run_dir_edit.setText("./output_qa")
            self.settings_proj_mpv_edit.clear()
            self.settings_mpvopts_edit.clear()
            self.settings_runcalx_edit.clear()
            
            # Reset advanced settings values
            self.settings_max_instances_value = "50"
            self.settings_log_level_value = "INFO"
            self.settings_max_jobs_value = "100"
            self.settings_retries_value = "2"
            self.settings_save_express_value = True
            # Reset cleanup checkbox in main settings
            self.settings_cleanup_cb.setChecked(False)
            
            QMessageBox.information(self, "Reset Settings", "Settings reset to defaults!")

class ActionTabsWidget(QTabWidget):
    """Bottom tabs for Create Package and Compare Packages"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setup_ui()
        
    def setup_ui(self):
        # Create Package Tab
        create_tab = QWidget()
        create_layout = QVBoxLayout()
        
        # Package Specific Settings Group
        package_group = QGroupBox("Package Settings")
        package_layout = QFormLayout()
        
        # cds.lib
        cds_lib_layout = QHBoxLayout()
        self.cds_lib_edit = QLineEdit()
        self.cds_lib_edit.setPlaceholderText("Enter cds.lib file path")
        view_cds_btn = QPushButton("View")
        browse_cds_btn = QPushButton("Browse")
        cds_lib_layout.addWidget(self.cds_lib_edit)
        cds_lib_layout.addWidget(view_cds_btn)
        cds_lib_layout.addWidget(browse_cds_btn)
        package_layout.addRow("cds.lib:", cds_lib_layout)
        
        # PDK Version
        self.pdk_version_combo = QComboBox()
        self.pdk_version_combo.addItems(["Undefined"])
        self.pdk_version_combo.setEnabled(False)
        package_layout.addRow("PDK Version:", self.pdk_version_combo)
        
        package_group.setLayout(package_layout)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        verify_btn = QPushButton("✅ Verify")
        create_btn = QPushButton("📦 Create")
        stop_btn = QPushButton("⏹️ Stop")
        stop_btn.setEnabled(False)
        
        verify_btn.clicked.connect(self.verify_package)
        create_btn.clicked.connect(self.create_package)
        
        action_layout.addWidget(verify_btn)
        action_layout.addWidget(create_btn)
        action_layout.addWidget(stop_btn)
        
        create_layout.addWidget(package_group)
        create_layout.addLayout(action_layout)
        create_layout.addStretch()
        create_tab.setLayout(create_layout)
        
        # Compare Package Tab
        compare_tab = QWidget()
        compare_layout = QVBoxLayout()
        
        # Golden Package Group
        golden_group = QGroupBox("Package Golden")
        golden_layout = QFormLayout()
        
        # Golden Source selection
        golden_source_layout = QHBoxLayout()
        self.golden_existed_rb = QRadioButton("Existed Package")
        self.golden_new_rb = QRadioButton("Create New")
        self.golden_existed_rb.setChecked(True)
        golden_source_layout.addWidget(self.golden_existed_rb)
        golden_source_layout.addWidget(self.golden_new_rb)
        golden_layout.addRow("Source:", golden_source_layout)
        
        # Golden Package Path
        golden_path_layout = QHBoxLayout()
        self.golden_path_edit = QLineEdit("./package_golden")
        self.golden_path_edit.setPlaceholderText("Enter golden package path")
        browse_golden_btn = QPushButton("Browse")
        golden_path_layout.addWidget(self.golden_path_edit)
        golden_path_layout.addWidget(browse_golden_btn)
        golden_layout.addRow("Package Path:", golden_path_layout)
        
        # Golden CDF Test Cases Folder
        golden_cdf_layout = QHBoxLayout()
        self.golden_cdf_edit = QLineEdit("<PACKAGE>/qa_<TECHLIB>__CDF")
        self.golden_cdf_edit.setPlaceholderText("Enter golden CDF folder path")
        browse_golden_cdf_btn = QPushButton("Browse")
        golden_cdf_layout.addWidget(self.golden_cdf_edit)
        golden_cdf_layout.addWidget(browse_golden_cdf_btn)
        golden_layout.addRow("CDF Test Cases Folder:", golden_cdf_layout)
        
        # Golden TA Test Cases Folder
        golden_ta_layout = QHBoxLayout()
        self.golden_ta_edit = QLineEdit("<PACKAGE>/qa_<TECHLIB>__TA")
        self.golden_ta_edit.setPlaceholderText("Enter golden TA folder path")
        browse_golden_ta_btn = QPushButton("Browse")
        golden_ta_layout.addWidget(self.golden_ta_edit)
        golden_ta_layout.addWidget(browse_golden_ta_btn)
        golden_layout.addRow("TA Test Cases Folder:", golden_ta_layout)
        
        # Golden Waived Rules
        golden_waived_layout = QHBoxLayout()
        self.golden_waived_edit = QLineEdit("<PACKAGE>/waived_rules_drc.xls")
        self.golden_waived_edit.setPlaceholderText("Enter waived rules DRC file path")
        view_golden_waived_btn = QPushButton("View")
        browse_golden_waived_btn = QPushButton("Browse")
        golden_waived_layout.addWidget(self.golden_waived_edit)
        golden_waived_layout.addWidget(view_golden_waived_btn)
        golden_waived_layout.addWidget(browse_golden_waived_btn)
        golden_layout.addRow("Waived Rules:", golden_waived_layout)
        
        # Golden PDK Version
        self.golden_pdk_combo = QComboBox()
        self.golden_pdk_combo.addItems(["Undefined", "v1.0", "v2.0"])
        golden_layout.addRow("PDK Version:", self.golden_pdk_combo)
        
        # Golden cds.lib
        golden_cds_layout = QHBoxLayout()
        self.golden_cds_edit = QLineEdit("<PACKAGE>/cds.lib")
        self.golden_cds_edit.setPlaceholderText("Enter cds.lib file path")
        view_golden_cds_btn = QPushButton("View")
        browse_golden_cds_btn = QPushButton("Browse")
        golden_cds_layout.addWidget(self.golden_cds_edit)
        golden_cds_layout.addWidget(view_golden_cds_btn)
        golden_cds_layout.addWidget(browse_golden_cds_btn)
        golden_layout.addRow("cds.lib:", golden_cds_layout)
        
        golden_group.setLayout(golden_layout)
        
        # Alpha Package Group
        alpha_group = QGroupBox("Package Alpha")
        alpha_layout = QFormLayout()
        
        # Alpha Source selection
        alpha_source_layout = QHBoxLayout()
        self.alpha_existed_rb = QRadioButton("Existed Package")
        self.alpha_new_rb = QRadioButton("Create New")
        self.alpha_existed_rb.setChecked(True)
        alpha_source_layout.addWidget(self.alpha_existed_rb)
        alpha_source_layout.addWidget(self.alpha_new_rb)
        alpha_layout.addRow("Source:", alpha_source_layout)
        
        # Alpha Package Path
        alpha_path_layout = QHBoxLayout()
        self.alpha_path_edit = QLineEdit("./package_alpha")
        self.alpha_path_edit.setPlaceholderText("Enter alpha package path")
        browse_alpha_btn = QPushButton("Browse")
        alpha_path_layout.addWidget(self.alpha_path_edit)
        alpha_path_layout.addWidget(browse_alpha_btn)
        alpha_layout.addRow("Package Path:", alpha_path_layout)
        
        # Alpha CDF Test Cases Folder
        alpha_cdf_layout = QHBoxLayout()
        self.alpha_cdf_edit = QLineEdit("<PACKAGE>/qa_<TECHLIB>__CDF")
        self.alpha_cdf_edit.setPlaceholderText("Enter alpha CDF folder path")
        browse_alpha_cdf_btn = QPushButton("Browse")
        alpha_cdf_layout.addWidget(self.alpha_cdf_edit)
        alpha_cdf_layout.addWidget(browse_alpha_cdf_btn)
        alpha_layout.addRow("CDF Test Cases Folder:", alpha_cdf_layout)
        
        # Alpha TA Test Cases Folder
        alpha_ta_layout = QHBoxLayout()
        self.alpha_ta_edit = QLineEdit("<PACKAGE>/qa_<TECHLIB>__TA")
        self.alpha_ta_edit.setPlaceholderText("Enter alpha TA folder path")
        browse_alpha_ta_btn = QPushButton("Browse")
        alpha_ta_layout.addWidget(self.alpha_ta_edit)
        alpha_ta_layout.addWidget(browse_alpha_ta_btn)
        alpha_layout.addRow("TA Test Cases Folder:", alpha_ta_layout)
        
        # Alpha Failed Rules
        alpha_failed_layout = QHBoxLayout()
        self.alpha_failed_edit = QLineEdit("<PACKAGE>/failed_rules.xls")
        self.alpha_failed_edit.setPlaceholderText("Enter failed rules file path")
        view_alpha_failed_btn = QPushButton("View")
        browse_alpha_failed_btn = QPushButton("Browse")
        alpha_failed_layout.addWidget(self.alpha_failed_edit)
        alpha_failed_layout.addWidget(view_alpha_failed_btn)
        alpha_failed_layout.addWidget(browse_alpha_failed_btn)
        alpha_layout.addRow("Failed Rules:", alpha_failed_layout)
        
        # Alpha PDK Version
        self.alpha_pdk_combo = QComboBox()
        self.alpha_pdk_combo.addItems(["Undefined", "v1.0", "v2.0"])
        alpha_layout.addRow("PDK Version:", self.alpha_pdk_combo)
        
        # Alpha cds.lib
        alpha_cds_layout = QHBoxLayout()
        self.alpha_cds_edit = QLineEdit("<PACKAGE>/cds.lib")
        self.alpha_cds_edit.setPlaceholderText("Enter cds.lib file path")
        view_alpha_cds_btn = QPushButton("View")
        browse_alpha_cds_btn = QPushButton("Browse")
        alpha_cds_layout.addWidget(self.alpha_cds_edit)
        alpha_cds_layout.addWidget(view_alpha_cds_btn)
        alpha_cds_layout.addWidget(browse_alpha_cds_btn)
        alpha_layout.addRow("cds.lib:", alpha_cds_layout)
        
        alpha_group.setLayout(alpha_layout)
        
        # QA Settings Group
        qa_settings_group = QGroupBox("QA Settings")
        qa_settings_layout = QFormLayout()
        
        # Exclude Layers
        exclude_layers_layout = QHBoxLayout()
        self.exclude_layers_edit = QLineEdit("<PACKAGE>/exclude_layers.txt")
        self.exclude_layers_edit.setPlaceholderText("Enter path to exclude layers file")
        view_exclude_btn = QPushButton("View")
        browse_exclude_btn = QPushButton("Browse")
        exclude_layers_layout.addWidget(self.exclude_layers_edit)
        exclude_layers_layout.addWidget(view_exclude_btn)
        exclude_layers_layout.addWidget(browse_exclude_btn)
        qa_settings_layout.addRow("Exclude Layers:", exclude_layers_layout)
        
        qa_settings_group.setLayout(qa_settings_layout)
        
        # Compare action buttons
        compare_action_layout = QHBoxLayout()
        compare_action_layout.addStretch()
        verify_compare_btn = QPushButton("✅ Verify")
        compare_packages_btn = QPushButton("🔍 Compare")
        export_btn = QPushButton("📊 Export")
        
        verify_compare_btn.clicked.connect(self.verify_comparison)
        compare_packages_btn.clicked.connect(self.compare_packages)
        export_btn.clicked.connect(self.export_results)
        
        compare_action_layout.addWidget(verify_compare_btn)
        compare_action_layout.addWidget(compare_packages_btn)
        compare_action_layout.addWidget(export_btn)
        
        compare_layout.addWidget(golden_group)
        compare_layout.addWidget(alpha_group)
        compare_layout.addWidget(qa_settings_group)
        compare_layout.addLayout(compare_action_layout)
        compare_layout.addStretch()
        compare_tab.setLayout(compare_layout)
        
        self.addTab(create_tab, "📦 Create Package")
        self.addTab(compare_tab, "🔍 Compare Packages")
    
    # Action methods
    def verify_package(self):
        """Verify package settings"""
        QMessageBox.information(self, "Verify", "Package settings verified successfully!")
    
    def create_package(self):
        """Create QA package"""
        QMessageBox.information(self, "Create Package", "Package creation started!")
    
    def verify_comparison(self):
        """Verify comparison settings"""
        QMessageBox.information(self, "Verify", "Comparison settings verified successfully!")
    
    def compare_packages(self):
        """Compare packages"""
        QMessageBox.information(self, "Compare", "Package comparison started!")
    
    def export_results(self):
        """Export comparison results"""
        QMessageBox.information(self, "Export", "Comparison results exported successfully!")

class MainContentArea(QWidget):
    """Main content area with accordion layout"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Header area
        self.header_layout = QHBoxLayout()
        self.title_label = QLabel("Settings & Actions")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        
        self.subtitle_label = QLabel("Configure settings and manage QA packages")
        self.subtitle_label.setStyleSheet("color: #666; font-style: italic;")
        
        header_v_layout = QVBoxLayout()
        header_v_layout.addWidget(self.title_label)
        header_v_layout.addWidget(self.subtitle_label)
        header_v_layout.setSpacing(2)
        
        self.header_layout.addLayout(header_v_layout)
        self.header_layout.addStretch()
        
        # Content stack
        self.content_stack = QStackedWidget()
        
        # Create pages
        self.create_accordion_page()  # Index 0
        self.create_debug_page()      # Index 1
        
        self.layout.addLayout(self.header_layout)
        self.layout.addWidget(self.content_stack)
        
        self.setLayout(self.layout)
    
    def create_accordion_page(self):
        """Create accordion layout page"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Vertical splitter for top/bottom layout
        splitter = QSplitter(Qt.Vertical)
        
        # Top: Settings (Accordion)
        self.settings_panel = AccordionSettingsPanel(self)
        
        # Bottom: Action Tabs
        self.action_tabs = ActionTabsWidget(self)
        
        splitter.addWidget(self.settings_panel)
        splitter.addWidget(self.action_tabs)
        splitter.setSizes([400, 300])  # Settings larger, actions smaller
        
        layout.addWidget(splitter)
        page.setLayout(layout)
        self.content_stack.addWidget(page)  # Index 0
    
    def create_debug_page(self):
        """Create Debug interface"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Debug information
        debug_group = QGroupBox("Debug Information")
        debug_layout = QVBoxLayout()
        
        self.debug_text = QTextEdit()
        self.debug_text.setPlaceholderText("Debug information will appear here...")
        self.debug_text.setReadOnly(True)
        debug_layout.addWidget(self.debug_text)
        
        debug_group.setLayout(debug_layout)
        
        # Debug controls
        controls_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        clear_btn = QPushButton("Clear")
        export_debug_btn = QPushButton("Export Log")
        
        refresh_btn.clicked.connect(self.refresh_debug)
        clear_btn.clicked.connect(self.clear_debug)
        export_debug_btn.clicked.connect(self.export_debug)
        
        controls_layout.addWidget(refresh_btn)
        controls_layout.addWidget(clear_btn)
        controls_layout.addWidget(export_debug_btn)
        controls_layout.addStretch()
        
        layout.addWidget(debug_group)
        layout.addLayout(controls_layout)
        
        page.setLayout(layout)
        self.content_stack.addWidget(page)  # Index 1
    
    def show_content(self, section, subsection):
        """Show content based on navigation selection"""
        if section == "settings_actions":
            self.title_label.setText("Settings & Actions")
            self.subtitle_label.setText("Configure settings and manage QA packages")
            self.content_stack.setCurrentIndex(0)
        elif section == "debug":
            self.title_label.setText("Debug")
            self.subtitle_label.setText("Debug information and system logs")
            self.content_stack.setCurrentIndex(1)
    
    # Debug methods
    def refresh_debug(self):
        """Refresh debug information"""
        self.debug_text.append("[INFO] Debug information refreshed...")
    
    def clear_debug(self):
        """Clear debug information"""
        self.debug_text.clear()
    
    def export_debug(self):
        """Export debug log"""
        QMessageBox.information(self, "Export", "Debug log exported successfully!")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QA MRVL Techlib Tool - Accordion Layout")
        self.setGeometry(100, 100, 1200, 800)
        self.setup_ui()
        self.setup_status_bar()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create horizontal splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left navigation panel
        self.nav_panel = LeftNavigationPanel(self)
        self.nav_panel.item_selected.connect(self.on_navigation_changed)
        
        # Main content area
        self.content_area = MainContentArea(self)
        
        # Add to splitter
        splitter.addWidget(self.nav_panel)
        splitter.addWidget(self.content_area)
        
        # Set splitter proportions (left panel smaller)
        splitter.setSizes([180, 1020])
        splitter.setCollapsible(0, False)  # Don't allow left panel to collapse
        
        # Main layout
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        
        central_widget.setLayout(layout)
    
    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status label
        self.status_label = QLabel("Status: Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Current section info
        self.section_label = QLabel("Current: Settings & Actions")
        self.status_bar.addPermanentWidget(self.section_label)
    
    def on_navigation_changed(self, section, subsection):
        """Handle navigation panel selection change"""
        self.content_area.show_content(section, subsection)
        
        # Update status bar
        section_names = {
            "settings_actions": "Settings & Actions",
            "debug": "Debug"
        }
        
        current_section = section_names.get(section, section)
        self.section_label.setText(f"Current: {current_section}")

def main():
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
