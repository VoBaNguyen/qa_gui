import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QStatusBar, 
                             QProgressBar, QTableWidget, QTableWidgetItem,
                             QCheckBox, QComboBox, QSpinBox, QGroupBox, QFormLayout,
                             QFrame, QScrollArea, QTextEdit, QSlider, QLineEdit, 
                             QTreeWidget, QTreeWidgetItem, QSplitter, QStackedWidget,
                             QMessageBox, QFileDialog, QDialogButtonBox, QDialog, QRadioButton)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPalette

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
        
        # Add navigation items
        self.create_navigation_items()
        
        # Connect selection change
        self.nav_tree.itemClicked.connect(self.on_item_clicked)
        
        layout.addWidget(title_label)
        layout.addWidget(self.nav_tree)
        
        self.setLayout(layout)
    
    def create_navigation_items(self):
        """Create navigation tree items"""
        # Settings
        settings_item = QTreeWidgetItem(["⚙️ Settings"])
        settings_item.setData(0, Qt.UserRole, ("settings", "main"))
        self.nav_tree.addTopLevelItem(settings_item)
        
        # Create Package
        package_item = QTreeWidgetItem(["📦 Create Package"])
        package_item.setData(0, Qt.UserRole, ("create_package", "main"))
        self.nav_tree.addTopLevelItem(package_item)
        
        # Compare Packages
        compare_item = QTreeWidgetItem(["🔍 Compare Packages"])
        compare_item.setData(0, Qt.UserRole, ("compare_packages", "main"))
        self.nav_tree.addTopLevelItem(compare_item)
        
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

class MainContentArea(QWidget):
    """Main content area that changes based on left panel selection"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Header area
        self.header_layout = QHBoxLayout()
        self.title_label = QLabel("Create Package")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        
        self.subtitle_label = QLabel("Create and manage QA packages")
        self.subtitle_label.setStyleSheet("color: #666; font-style: italic;")
        
        header_v_layout = QVBoxLayout()
        header_v_layout.addWidget(self.title_label)
        header_v_layout.addWidget(self.subtitle_label)
        header_v_layout.setSpacing(2)
        
        self.header_layout.addLayout(header_v_layout)
        self.header_layout.addStretch()
        
        # Content stack
        self.content_stack = QStackedWidget()
        
        # Create pages to match actual QA tool
        self.create_settings_page()  # Index 0
        self.create_package_creator_page()  # Index 1
        self.create_compare_packages_page()  # Index 2
        self.create_debug_page()  # Index 3
        
        self.layout.addLayout(self.header_layout)
        self.layout.addWidget(self.content_stack)
        
        self.setLayout(self.layout)
    
    def create_settings_page(self):
        """Create Settings page with common settings fields"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Required Settings Group
        required_group = QGroupBox("Required Settings")
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
        required_layout.addRow("PDK Configs:", pdk_config_layout)
        
        # Virtuoso Command
        self.settings_virtuoso_cmd_edit = QLineEdit()
        self.settings_virtuoso_cmd_edit.setPlaceholderText("Enter Virtuoso command")
        required_layout.addRow("Virtuoso Command:", self.settings_virtuoso_cmd_edit)
        
        # .cdsinit
        cdsinit_layout = QHBoxLayout()
        self.settings_cdsinit_edit = QLineEdit()
        self.settings_cdsinit_edit.setPlaceholderText("Enter path to cdsinit local file")
        view_cdsinit_btn = QPushButton("View")
        browse_cdsinit_btn = QPushButton("Browse")
        cdsinit_layout.addWidget(self.settings_cdsinit_edit)
        cdsinit_layout.addWidget(view_cdsinit_btn)
        cdsinit_layout.addWidget(browse_cdsinit_btn)
        required_layout.addRow(".cdsinit:", cdsinit_layout)
        
        required_group.setLayout(required_layout)
        
        # DRC Settings Group
        self.settings_drc_group = QGroupBox("DRC Settings")
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
        
        # Advanced Settings Group
        advanced_group = QGroupBox("Advanced")
        advanced_layout = QFormLayout()
        
        # Max Instances Per Cell View
        self.settings_max_instances_edit = QLineEdit("50")
        self.settings_max_instances_edit.setPlaceholderText("Enter max instances per cellview")
        advanced_layout.addRow("Max Instances Per Cell View:", self.settings_max_instances_edit)
        
        # Log Level
        self.settings_log_level_combo = QComboBox()
        self.settings_log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.settings_log_level_combo.setCurrentText("INFO")
        advanced_layout.addRow("Log Level:", self.settings_log_level_combo)
        
        # Max Jobs
        max_jobs_layout = QHBoxLayout()
        self.settings_max_jobs_edit = QLineEdit("100")
        self.settings_max_jobs_edit.setPlaceholderText("Enter max jobs")
        check_license_btn = QPushButton("Check")
        max_jobs_layout.addWidget(self.settings_max_jobs_edit)
        max_jobs_layout.addWidget(check_license_btn)
        advanced_layout.addRow("Max Jobs:", max_jobs_layout)
        
        # Max retries
        self.settings_retries_edit = QLineEdit("2")
        self.settings_retries_edit.setPlaceholderText("Enter number of retries")
        advanced_layout.addRow("Max retries:", self.settings_retries_edit)
        
        # Options
        options_layout = QHBoxLayout()
        self.settings_save_express_cb = QCheckBox("Save .expressPCell")
        self.settings_cleanup_cb = QCheckBox("Cleanup Output")
        self.settings_save_express_cb.setChecked(True)
        options_layout.addWidget(self.settings_save_express_cb)
        options_layout.addWidget(self.settings_cleanup_cb)
        advanced_layout.addRow("Options:", options_layout)
        
        advanced_group.setLayout(advanced_layout)
        
        # Connect DRC checkbox to enable/disable DRC group
        self.settings_drc_cb.toggled.connect(self.settings_drc_group.setEnabled)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        save_settings_btn = QPushButton("Save Settings")
        load_settings_btn = QPushButton("Load Settings")
        reset_btn = QPushButton("Reset to Defaults")
        
        save_settings_btn.clicked.connect(self.save_settings)
        load_settings_btn.clicked.connect(self.load_settings)
        reset_btn.clicked.connect(self.reset_settings)
        
        action_layout.addWidget(save_settings_btn)
        action_layout.addWidget(load_settings_btn)
        action_layout.addWidget(reset_btn)
        
        layout.addWidget(required_group)
        layout.addWidget(self.settings_drc_group)
        layout.addWidget(advanced_group)
        layout.addLayout(action_layout)
        layout.addStretch()
        
        page.setLayout(layout)
        self.content_stack.addWidget(page)  # Index 0
    
    def create_package_creator_page(self):
        """Create Package Creator interface - simplified without common settings"""
        page = QWidget()
        layout = QVBoxLayout()
        
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
        
        # Run Directory
        run_dir_layout = QHBoxLayout()
        self.run_dir_edit = QLineEdit("./output_qa")
        self.run_dir_edit.setPlaceholderText("Enter run directory path")
        browse_run_btn = QPushButton("Browse")
        run_dir_layout.addWidget(self.run_dir_edit)
        run_dir_layout.addWidget(browse_run_btn)
        package_layout.addRow("Run Directory:", run_dir_layout)
        
        package_group.setLayout(package_layout)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        verify_btn = QPushButton("Verify")
        create_btn = QPushButton("Create")
        stop_btn = QPushButton("Stop")
        stop_btn.setEnabled(False)
        
        verify_btn.clicked.connect(self.verify_package)
        create_btn.clicked.connect(self.create_package)
        
        action_layout.addWidget(verify_btn)
        action_layout.addWidget(create_btn)
        action_layout.addWidget(stop_btn)
        
        layout.addWidget(package_group)
        layout.addLayout(action_layout)
        layout.addStretch()
        
        page.setLayout(layout)
        self.content_stack.addWidget(page)  # Index 1
    
    def create_compare_packages_page(self):
        """Create Package Comparison interface with all required fields"""
        page = QWidget()
        layout = QVBoxLayout()

        # Package Golden Group
        golden_group = QGroupBox("Package Golden")
        golden_layout = QFormLayout()

        # Source selection
        self.golden_radio_existed = QRadioButton("Existed Package")
        self.golden_radio_new = QRadioButton("Create New")
        self.golden_radio_existed.setChecked(True)
        golden_radio_layout = QHBoxLayout()
        golden_radio_layout.addWidget(self.golden_radio_existed)
        golden_radio_layout.addWidget(self.golden_radio_new)
        golden_layout.addRow("Source:", golden_radio_layout)

        # Golden Package Path
        self.golden_path_edit = QLineEdit("./package_golden")
        self.golden_path_edit.setPlaceholderText("Enter golden package path")
        browse_golden_path_btn = QPushButton("Browse")
        golden_path_layout = QHBoxLayout()
        golden_path_layout.addWidget(self.golden_path_edit)
        golden_path_layout.addWidget(browse_golden_path_btn)
        golden_layout.addRow("Package Path:", golden_path_layout)

        # Golden CDF
        self.golden_cdf_edit = QLineEdit("<PACKAGE>/qa_<TECHLIB>__CDF")
        self.golden_cdf_edit.setPlaceholderText("Enter golden CDF folder path")
        browse_golden_cdf_btn = QPushButton("Browse")
        golden_cdf_layout = QHBoxLayout()
        golden_cdf_layout.addWidget(self.golden_cdf_edit)
        golden_cdf_layout.addWidget(browse_golden_cdf_btn)
        golden_layout.addRow("CDF Test Cases Folder:", golden_cdf_layout)

        # Golden TA
        self.golden_ta_edit = QLineEdit("<PACKAGE>/qa_<TECHLIB>__TA")
        self.golden_ta_edit.setPlaceholderText("Enter golden TA folder path")
        browse_golden_ta_btn = QPushButton("Browse")
        golden_ta_layout = QHBoxLayout()
        golden_ta_layout.addWidget(self.golden_ta_edit)
        golden_ta_layout.addWidget(browse_golden_ta_btn)
        golden_layout.addRow("TA Test Cases Folder:", golden_ta_layout)

        # Golden Waived Rules
        self.golden_waived_edit = QLineEdit("<PACKAGE>/waived_rules_drc.xls")
        self.golden_waived_edit.setPlaceholderText("Enter waived rules DRC file path")
        view_golden_waived_btn = QPushButton("View")
        browse_golden_waived_btn = QPushButton("Browse")
        golden_waived_layout = QHBoxLayout()
        golden_waived_layout.addWidget(self.golden_waived_edit)
        golden_waived_layout.addWidget(view_golden_waived_btn)
        golden_waived_layout.addWidget(browse_golden_waived_btn)
        golden_layout.addRow("Waived Rules:", golden_waived_layout)

        # PDK Version
        self.golden_pdk_version_combo = QComboBox()
        self.golden_pdk_version_combo.addItems(["Undefined"])
        golden_layout.addRow("PDK Version:", self.golden_pdk_version_combo)

        # Golden cds.lib
        self.golden_cds_lib_edit = QLineEdit("<PACKAGE>/cds.lib")
        self.golden_cds_lib_edit.setPlaceholderText("Enter cds.lib file path")
        browse_golden_cds_lib_btn = QPushButton("Browse")
        golden_cds_lib_layout = QHBoxLayout()
        golden_cds_lib_layout.addWidget(self.golden_cds_lib_edit)
        golden_cds_lib_layout.addWidget(browse_golden_cds_lib_btn)
        golden_layout.addRow("cds.lib:", golden_cds_lib_layout)

        golden_group.setLayout(golden_layout)

        # Package Alpha Group
        alpha_group = QGroupBox("Package Alpha")
        alpha_layout = QFormLayout()

        # Source selection
        self.alpha_radio_existed = QRadioButton("Existed Package")
        self.alpha_radio_new = QRadioButton("Create New")
        self.alpha_radio_existed.setChecked(True)
        alpha_radio_layout = QHBoxLayout()
        alpha_radio_layout.addWidget(self.alpha_radio_existed)
        alpha_radio_layout.addWidget(self.alpha_radio_new)
        alpha_layout.addRow("Source:", alpha_radio_layout)

        # Alpha Package Path
        self.alpha_path_edit = QLineEdit("./package_alpha")
        self.alpha_path_edit.setPlaceholderText("Enter alpha package path")
        browse_alpha_path_btn = QPushButton("Browse")
        alpha_path_layout = QHBoxLayout()
        alpha_path_layout.addWidget(self.alpha_path_edit)
        alpha_path_layout.addWidget(browse_alpha_path_btn)
        alpha_layout.addRow("Package Path:", alpha_path_layout)

        # Alpha CDF
        self.alpha_cdf_edit = QLineEdit("<PACKAGE>/qa_<TECHLIB>__CDF")
        self.alpha_cdf_edit.setPlaceholderText("Enter alpha CDF folder path")
        browse_alpha_cdf_btn = QPushButton("Browse")
        alpha_cdf_layout = QHBoxLayout()
        alpha_cdf_layout.addWidget(self.alpha_cdf_edit)
        alpha_cdf_layout.addWidget(browse_alpha_cdf_btn)
        alpha_layout.addRow("CDF Test Cases Folder:", alpha_cdf_layout)

        # Alpha TA
        self.alpha_ta_edit = QLineEdit("<PACKAGE>/qa_<TECHLIB>__TA")
        self.alpha_ta_edit.setPlaceholderText("Enter alpha TA folder path")
        browse_alpha_ta_btn = QPushButton("Browse")
        alpha_ta_layout = QHBoxLayout()
        alpha_ta_layout.addWidget(self.alpha_ta_edit)
        alpha_ta_layout.addWidget(browse_alpha_ta_btn)
        alpha_layout.addRow("TA Test Cases Folder:", alpha_ta_layout)

        # Alpha Failed Rules
        self.alpha_failed_edit = QLineEdit("<PACKAGE>/failed_rules.xls")
        self.alpha_failed_edit.setPlaceholderText("Enter failed rules file path")
        view_alpha_failed_btn = QPushButton("View")
        browse_alpha_failed_btn = QPushButton("Browse")
        alpha_failed_layout = QHBoxLayout()
        alpha_failed_layout.addWidget(self.alpha_failed_edit)
        alpha_failed_layout.addWidget(view_alpha_failed_btn)
        alpha_failed_layout.addWidget(browse_alpha_failed_btn)
        alpha_layout.addRow("Failed Rules:", alpha_failed_layout)

        # PDK Version
        self.alpha_pdk_version_combo = QComboBox()
        self.alpha_pdk_version_combo.addItems(["v1.0", "Undefined", "v2.0"])
        alpha_layout.addRow("PDK Version:", self.alpha_pdk_version_combo)

        # Alpha cds.lib
        self.alpha_cds_lib_edit = QLineEdit("<PACKAGE>/cds.lib")
        self.alpha_cds_lib_edit.setPlaceholderText("Enter cds.lib file path")
        browse_alpha_cds_lib_btn = QPushButton("Browse")
        alpha_cds_lib_layout = QHBoxLayout()
        alpha_cds_lib_layout.addWidget(self.alpha_cds_lib_edit)
        alpha_cds_lib_layout.addWidget(browse_alpha_cds_lib_btn)
        alpha_layout.addRow("cds.lib:", alpha_cds_lib_layout)

        alpha_group.setLayout(alpha_layout)

        # Comparison Settings Group
        comparison_group = QGroupBox("Comparison Settings")
        comparison_layout = QFormLayout()

        # Exclude Layers
        exclude_layers_layout = QHBoxLayout()
        self.exclude_layers_edit = QLineEdit("<PACKAGE>/exclude_layers.txt")
        self.exclude_layers_edit.setPlaceholderText("Enter path to exclude layers file")
        view_exclude_btn = QPushButton("View")
        browse_exclude_btn = QPushButton("Browse")
        exclude_layers_layout.addWidget(self.exclude_layers_edit)
        exclude_layers_layout.addWidget(view_exclude_btn)
        exclude_layers_layout.addWidget(browse_exclude_btn)
        comparison_layout.addRow("Exclude Layers:", exclude_layers_layout)

        # Run Directory
        compare_run_dir_layout = QHBoxLayout()
        self.compare_run_dir_edit = QLineEdit("./run_dir_compare")
        self.compare_run_dir_edit.setPlaceholderText("Enter run directory path")
        browse_compare_run_btn = QPushButton("Browse")
        compare_run_dir_layout.addWidget(self.compare_run_dir_edit)
        compare_run_dir_layout.addWidget(browse_compare_run_btn)
        comparison_layout.addRow("Run Directory:", compare_run_dir_layout)

        # Options
        compare_options_layout = QHBoxLayout()
        self.cleanup_compare_cb = QCheckBox("Cleanup Run Directory")
        self.rve_cb = QCheckBox("RVE")
        compare_options_layout.addWidget(self.cleanup_compare_cb)
        compare_options_layout.addWidget(self.rve_cb)
        comparison_layout.addRow("Options:", compare_options_layout)

        comparison_group.setLayout(comparison_layout)

        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        verify_compare_btn = QPushButton("Verify")
        compare_btn = QPushButton("Compare")
        stop_compare_btn = QPushButton("Stop")
        stop_compare_btn.setEnabled(False)

        verify_compare_btn.clicked.connect(self.verify_comparison)
        compare_btn.clicked.connect(self.compare_packages)

        action_layout.addWidget(verify_compare_btn)
        action_layout.addWidget(compare_btn)
        action_layout.addWidget(stop_compare_btn)

        layout.addWidget(golden_group)
        layout.addWidget(alpha_group)
        layout.addWidget(comparison_group)
        layout.addLayout(action_layout)
        layout.addStretch()

        page.setLayout(layout)
        self.content_stack.addWidget(page)  # Index 2
    
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
        self.content_stack.addWidget(page)  # Index 3
    
    def populate_sample_logs(self):
        """Add sample log entries"""
        sample_logs = [
            "[INFO] 2024-01-15 10:30:15 - Application started successfully",
            "[DEBUG] 2024-01-15 10:30:16 - Loading configuration from config.ini",
            "[INFO] 2024-01-15 10:30:17 - Database connection established",
            "[WARNING] 2024-01-15 10:30:20 - Package validation took longer than expected",
            "[ERROR] 2024-01-15 10:30:25 - Failed to create package: insufficient permissions",
            "[INFO] 2024-01-15 10:30:30 - Retrying package creation with elevated privileges",
            "[INFO] 2024-01-15 10:30:35 - Package created successfully",
            "[DEBUG] 2024-01-15 10:30:40 - Cleaning up temporary files"
        ]
        
        for log in sample_logs:
            self.logs_text.append(log)
    
    def show_content(self, section, subsection):
        """Show content based on navigation selection"""
        self.title_label.setText(section.replace('_', ' ').title())
        
        # Map sections to content stack indices
        content_map = {
            "settings": 0,
            "create_package": 1,
            "compare_packages": 2,
            "debug": 3
        }
        
        if section in content_map:
            self.content_stack.setCurrentIndex(content_map[section])
            
            # Update subtitle based on section
            subtitles = {
                "settings": "Configure common settings and preferences",
                "create_package": "Create and manage QA packages",
                "compare_packages": "Compare package versions and analyze differences",
                "debug": "Debug information and system logs"
            }
            self.subtitle_label.setText(subtitles.get(section, ""))
    
    # Action methods for Create Package tab
    def verify_package(self):
        """Verify package settings"""
        QMessageBox.information(self, "Verify", "Package settings verified successfully!")
    
    def create_package(self):
        """Create QA package"""
        QMessageBox.information(self, "Create Package", "Package creation started!")
    
    # Action methods for Compare Packages tab
    def verify_comparison(self):
        """Verify comparison settings"""
        QMessageBox.information(self, "Verify", "Comparison settings verified successfully!")
    
    def compare_packages(self):
        """Compare packages"""
        QMessageBox.information(self, "Compare", "Package comparison started!")
    
    # Action methods for Debug tab
    def refresh_debug(self):
        """Refresh debug information"""
        self.debug_text.append("Debug information refreshed...")
    
    def clear_debug(self):
        """Clear debug information"""
        self.debug_text.clear()
    
    def export_debug(self):
        """Export debug log"""
        QMessageBox.information(self, "Export", "Debug log exported successfully!")

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
            self.settings_proj_mpv_edit.clear()
            self.settings_mpvopts_edit.clear()
            self.settings_runcalx_edit.clear()
            self.settings_max_instances_edit.setText("50")
            self.settings_log_level_combo.setCurrentText("INFO")
            self.settings_max_jobs_edit.setText("100")
            self.settings_retries_edit.setText("2")
            self.settings_save_express_cb.setChecked(True)
            self.settings_cleanup_cb.setChecked(False)
            QMessageBox.information(self, "Reset Settings", "Settings reset to defaults!")

    def show_settings_dialog(self):
        pass  # No longer used

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QA MRVL Techlib Tool")
        self.setGeometry(100, 100, 1200, 800)
        self.setup_ui()
        self.setup_status_bar()

    def apply_stylesheet(self):
        pass  # Method retained for compatibility, but does nothing

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
        self.section_label = QLabel("Current: Create Package")
        self.status_bar.addPermanentWidget(self.section_label)
    
    def on_navigation_changed(self, section, subsection):
        """Handle navigation panel selection change"""
        self.content_area.show_content(section, subsection)
        
        # Update status bar
        section_names = {
            "create_package": "Create Package",
            "compare_packages": "Compare Packages", 
            "debug": "Debug"
        }
        
        current_section = section_names.get(section, section)
        self.section_label.setText(f"Current: {current_section}")
    
    def simulate_operation(self, start_msg, end_msg):
        """Simulate a long-running operation with progress"""
        self.status_label.setText(f"Status: {start_msg}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        timer = QTimer()
        progress = 0
        
        def update_progress():
            nonlocal progress
            progress += 10
            self.progress_bar.setValue(progress)
            if progress >= 100:
                timer.stop()
                self.progress_bar.setVisible(False)
                self.status_label.setText(f"Status: {end_msg}")
                QTimer.singleShot(3000, lambda: self.status_label.setText("Status: Ready"))
        
        timer.timeout.connect(update_progress)
        timer.start(150)

def main():
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()