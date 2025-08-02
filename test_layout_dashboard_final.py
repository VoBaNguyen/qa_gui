import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QStatusBar, 
                             QProgressBar, QTableWidget, QTableWidgetItem,
                             QCheckBox, QComboBox, QSpinBox, QGroupBox, QFormLayout,
                             QFrame, QScrollArea, QTextEdit, QSlider, QLineEdit, 
                             QTreeWidget, QTreeWidgetItem, QSplitter, QStackedWidget,
                             QMessageBox, QFileDialog, QDialogButtonBox, QDialog, 
                             QRadioButton, QGridLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPalette

class ModularCard(QFrame):
    """Base class for modular cards"""
    def __init__(self, title, icon="", parent=None):
        super().__init__(parent)
        self.title = title
        self.icon = icon
        self.setup_base_ui()
        
    def setup_base_ui(self):
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(1)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: white;
                margin: 4px;
            }
            QFrame:hover {
                border-color: #0078d4;
                box-shadow: 0 2px 8px rgba(0,120,212,0.3);
            }
        """)
        
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 8)
        
        title_label = QLabel(f"{self.icon} {self.title}")
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        title_label.setStyleSheet("color: #333; border: none;")
        
        # Minimize/maximize button
        self.toggle_btn = QPushButton("−")
        self.toggle_btn.setFixedSize(20, 20)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: #f0f0f0;
                color: #666;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_content)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.toggle_btn)
        
        self.main_layout.addLayout(header_layout)
        
        # Content area (to be overridden)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_widget.setLayout(self.content_layout)
        self.main_layout.addWidget(self.content_widget)
        
        self.setLayout(self.main_layout)
        self.content_visible = True
        
    def toggle_content(self):
        """Toggle content visibility"""
        self.content_visible = not self.content_visible
        self.content_widget.setVisible(self.content_visible)
        self.toggle_btn.setText("−" if self.content_visible else "+")

class BasicConfigCard(ModularCard):
    """Basic configuration card"""
    def __init__(self):
        super().__init__("Basic Configuration", "⚙️")
        self.setup_content()
        
    def setup_content(self):
        # Techlib
        techlib_layout = QFormLayout()
        self.techlib_combo = QComboBox()
        self.techlib_combo.addItems(["gf12lpp", "gf22fdx", "gf28hpk", "gf12lp", "gf14lpp"])
        techlib_layout.addRow("Techlib:", self.techlib_combo)
        
        # QA Types
        qa_types_layout = QHBoxLayout()
        self.cdf_cb = QCheckBox("CDF")
        self.drc_cb = QCheckBox("DRC")
        self.ta_cb = QCheckBox("TA")
        self.cdf_cb.setChecked(True)
        qa_types_layout.addWidget(self.cdf_cb)
        qa_types_layout.addWidget(self.drc_cb)
        qa_types_layout.addWidget(self.ta_cb)
        techlib_layout.addRow("QA Types:", qa_types_layout)
        
        # Virtuoso command
        self.virtuoso_edit = QLineEdit()
        self.virtuoso_edit.setPlaceholderText("Enter Virtuoso command")
        techlib_layout.addRow("Virtuoso:", self.virtuoso_edit)
        
        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        techlib_layout.addRow("Log Level:", self.log_level_combo)
        
        self.content_layout.addLayout(techlib_layout)

class FilePathsCard(ModularCard):
    """File paths configuration card"""
    def __init__(self):
        super().__init__("File Paths", "📁")
        self.setup_content()
        
    def setup_content(self):
        paths_layout = QFormLayout()
        
        # QA Settings
        qa_layout = QHBoxLayout()
        self.qa_setting_edit = QLineEdit()
        self.qa_setting_edit.setPlaceholderText("QA settings file")
        qa_browse_btn = QPushButton("📂")
        qa_browse_btn.setFixedSize(30, 25)
        qa_layout.addWidget(self.qa_setting_edit)
        qa_layout.addWidget(qa_browse_btn)
        paths_layout.addRow("QA Settings:", qa_layout)
        
        # PDK Configs
        pdk_layout = QHBoxLayout()
        self.pdk_config_edit = QLineEdit()
        self.pdk_config_edit.setPlaceholderText("PDK configuration file")
        self.pdk_config_edit.setReadOnly(True)
        pdk_load_btn = QPushButton("Load")
        pdk_load_btn.setFixedSize(40, 25)
        pdk_layout.addWidget(self.pdk_config_edit)
        pdk_layout.addWidget(pdk_load_btn)
        paths_layout.addRow("PDK Configs:", pdk_layout)
        
        # cdsinit
        cdsinit_layout = QHBoxLayout()
        self.cdsinit_edit = QLineEdit()
        self.cdsinit_edit.setPlaceholderText(".cdsinit file")
        cdsinit_browse_btn = QPushButton("📂")
        cdsinit_browse_btn.setFixedSize(30, 25)
        cdsinit_layout.addWidget(self.cdsinit_edit)
        cdsinit_layout.addWidget(cdsinit_browse_btn)
        paths_layout.addRow(".cdsinit:", cdsinit_layout)
        
        self.content_layout.addLayout(paths_layout)

class DRCSettingsCard(ModularCard):
    """DRC settings card"""
    def __init__(self):
        super().__init__("DRC Settings", "🔧")
        self.setup_content()
        
    def setup_content(self):
        drc_layout = QFormLayout()
        
        # Project MPV
        proj_mpv_layout = QHBoxLayout()
        self.proj_mpv_edit = QLineEdit()
        self.proj_mpv_edit.setPlaceholderText("Project MPV")
        proj_browse_btn = QPushButton("📂")
        proj_browse_btn.setFixedSize(30, 25)
        proj_mpv_layout.addWidget(self.proj_mpv_edit)
        proj_mpv_layout.addWidget(proj_browse_btn)
        drc_layout.addRow("Project MPV:", proj_mpv_layout)
        
        # mpvopt DRC
        mpvopts_layout = QHBoxLayout()
        self.mpvopts_edit = QLineEdit()
        self.mpvopts_edit.setPlaceholderText("mpvopts for DRC")
        mpvopts_browse_btn = QPushButton("📂")
        mpvopts_browse_btn.setFixedSize(30, 25)
        mpvopts_layout.addWidget(self.mpvopts_edit)
        mpvopts_layout.addWidget(mpvopts_browse_btn)
        drc_layout.addRow("mpvopt DRC:", mpvopts_layout)
        
        # Runcalx Version
        self.runcalx_edit = QLineEdit()
        self.runcalx_edit.setPlaceholderText("Runcalx version")
        drc_layout.addRow("Runcalx Version:", self.runcalx_edit)
        
        self.content_layout.addLayout(drc_layout)

class PerformanceCard(ModularCard):
    """Performance settings card"""
    def __init__(self):
        super().__init__("Performance", "🚀")
        self.setup_content()
        
    def setup_content(self):
        perf_layout = QFormLayout()
        
        # Max instances
        self.max_instances_edit = QLineEdit("50")
        perf_layout.addRow("Max Instances:", self.max_instances_edit)
        
        # Max jobs with license check
        jobs_layout = QHBoxLayout()
        self.max_jobs_edit = QLineEdit("100")
        check_btn = QPushButton("Check")
        check_btn.setFixedSize(50, 25)
        jobs_layout.addWidget(self.max_jobs_edit)
        jobs_layout.addWidget(check_btn)
        perf_layout.addRow("Max Jobs:", jobs_layout)
        
        # Retries
        self.retries_edit = QLineEdit("2")
        perf_layout.addRow("Max Retries:", self.retries_edit)
        
        # Options
        options_layout = QHBoxLayout()
        self.save_express_cb = QCheckBox("Save .expressPCell")
        self.cleanup_cb = QCheckBox("Cleanup")
        self.save_express_cb.setChecked(True)
        options_layout.addWidget(self.save_express_cb)
        options_layout.addWidget(self.cleanup_cb)
        perf_layout.addRow("Options:", options_layout)
        
        self.content_layout.addLayout(perf_layout)

class PackageActionsCard(ModularCard):
    """Package creation actions card"""
    def __init__(self):
        super().__init__("Package Actions", "📦")
        self.setup_content()
        
    def setup_content(self):
        # Package specific settings
        package_layout = QFormLayout()
        
        # cds.lib
        cds_layout = QHBoxLayout()
        self.cds_lib_edit = QLineEdit()
        self.cds_lib_edit.setPlaceholderText("cds.lib file")
        cds_browse_btn = QPushButton("📂")
        cds_browse_btn.setFixedSize(30, 25)
        cds_layout.addWidget(self.cds_lib_edit)
        cds_layout.addWidget(cds_browse_btn)
        package_layout.addRow("cds.lib:", cds_layout)
        
        # PDK Version
        self.pdk_version_combo = QComboBox()
        self.pdk_version_combo.addItems(["Undefined", "v1.0", "v2.0"])
        package_layout.addRow("PDK Version:", self.pdk_version_combo)
        
        # Run directory
        run_layout = QHBoxLayout()
        self.run_dir_edit = QLineEdit("./output_qa")
        run_browse_btn = QPushButton("📂")
        run_browse_btn.setFixedSize(30, 25)
        run_layout.addWidget(self.run_dir_edit)
        run_layout.addWidget(run_browse_btn)
        package_layout.addRow("Run Directory:", run_layout)
        
        self.content_layout.addLayout(package_layout)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        verify_btn = QPushButton("✅ Verify")
        create_btn = QPushButton("📦 Create")
        stop_btn = QPushButton("⏹️ Stop")
        
        verify_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; border: none; padding: 8px; border-radius: 4px; }")
        create_btn.setStyleSheet("QPushButton { background-color: #007bff; color: white; border: none; padding: 8px; border-radius: 4px; }")
        stop_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; border: none; padding: 8px; border-radius: 4px; }")
        
        verify_btn.clicked.connect(self.verify_package)
        create_btn.clicked.connect(self.create_package)
        
        actions_layout.addWidget(verify_btn)
        actions_layout.addWidget(create_btn)
        actions_layout.addWidget(stop_btn)
        
        self.content_layout.addLayout(actions_layout)
        
        # Progress area
        self.progress_text = QTextEdit()
        self.progress_text.setMaximumHeight(80)
        self.progress_text.setPlaceholderText("Package creation progress...")
        self.progress_text.setReadOnly(True)
        self.progress_text.setStyleSheet("border: 1px solid #ddd; border-radius: 4px; background-color: #f8f9fa;")
        
        self.content_layout.addWidget(self.progress_text)
    
    def verify_package(self):
        """Verify package settings"""
        self.progress_text.append("[INFO] Verifying package settings...")
        self.progress_text.append("[INFO] Package settings verified successfully!")
        QMessageBox.information(self, "Verify", "Package settings verified successfully!")
    
    def create_package(self):
        """Create QA package"""
        self.progress_text.append("[INFO] Starting package creation...")
        self.progress_text.append("[INFO] Package creation in progress...")
        QMessageBox.information(self, "Create Package", "Package creation started!")

class CompareActionsCard(ModularCard):
    """Package comparison actions card"""
    def __init__(self):
        super().__init__("Compare Actions", "🔍")
        self.setup_content()
        
    def setup_content(self):
        # Quick compare setup
        compare_layout = QFormLayout()
        
        # Golden package
        golden_layout = QHBoxLayout()
        self.golden_path_edit = QLineEdit("./package_golden")
        golden_browse_btn = QPushButton("📂")
        golden_browse_btn.setFixedSize(30, 25)
        golden_layout.addWidget(self.golden_path_edit)
        golden_layout.addWidget(golden_browse_btn)
        compare_layout.addRow("Golden:", golden_layout)
        
        # Alpha package
        alpha_layout = QHBoxLayout()
        self.alpha_path_edit = QLineEdit("./package_alpha")
        alpha_browse_btn = QPushButton("📂")
        alpha_browse_btn.setFixedSize(30, 25)
        alpha_layout.addWidget(self.alpha_path_edit)
        alpha_layout.addWidget(alpha_browse_btn)
        compare_layout.addRow("Alpha:", alpha_layout)
        
        # Run directory
        run_layout = QHBoxLayout()
        self.compare_run_dir_edit = QLineEdit("./run_dir_compare")
        run_browse_btn = QPushButton("📂")
        run_browse_btn.setFixedSize(30, 25)
        run_layout.addWidget(self.compare_run_dir_edit)
        run_layout.addWidget(run_browse_btn)
        compare_layout.addRow("Run Directory:", run_layout)
        
        # Options
        options_layout = QHBoxLayout()
        self.cleanup_compare_cb = QCheckBox("Cleanup")
        self.rve_cb = QCheckBox("RVE")
        options_layout.addWidget(self.cleanup_compare_cb)
        options_layout.addWidget(self.rve_cb)
        compare_layout.addRow("Options:", options_layout)
        
        self.content_layout.addLayout(compare_layout)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        verify_compare_btn = QPushButton("✅ Verify")
        compare_btn = QPushButton("🔍 Compare")
        export_btn = QPushButton("📊 Export")
        
        verify_compare_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; border: none; padding: 8px; border-radius: 4px; }")
        compare_btn.setStyleSheet("QPushButton { background-color: #17a2b8; color: white; border: none; padding: 8px; border-radius: 4px; }")
        export_btn.setStyleSheet("QPushButton { background-color: #6c757d; color: white; border: none; padding: 8px; border-radius: 4px; }")
        
        verify_compare_btn.clicked.connect(self.verify_comparison)
        compare_btn.clicked.connect(self.compare_packages)
        export_btn.clicked.connect(self.export_results)
        
        actions_layout.addWidget(verify_compare_btn)
        actions_layout.addWidget(compare_btn)
        actions_layout.addWidget(export_btn)
        
        self.content_layout.addLayout(actions_layout)
        
        # Results area
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(80)
        self.results_text.setPlaceholderText("Comparison results...")
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("border: 1px solid #ddd; border-radius: 4px; background-color: #f8f9fa;")
        
        self.content_layout.addWidget(self.results_text)
    
    def verify_comparison(self):
        """Verify comparison settings"""
        self.results_text.append("[INFO] Verifying comparison settings...")
        self.results_text.append("[INFO] Comparison settings verified successfully!")
        QMessageBox.information(self, "Verify", "Comparison settings verified successfully!")
    
    def compare_packages(self):
        """Compare packages"""
        self.results_text.append("[INFO] Starting package comparison...")
        self.results_text.append("[INFO] Comparing golden vs alpha packages...")
        QMessageBox.information(self, "Compare", "Package comparison started!")
    
    def export_results(self):
        """Export comparison results"""
        QMessageBox.information(self, "Export", "Comparison results exported successfully!")

class SettingsActionsCard(ModularCard):
    """Settings management actions card"""
    def __init__(self):
        super().__init__("Settings Actions", "💾")
        self.setup_content()
        
    def setup_content(self):
        # Settings info
        info_layout = QVBoxLayout()
        
        status_label = QLabel("Current Status: Default Settings")
        status_label.setStyleSheet("color: #666; font-style: italic;")
        info_layout.addWidget(status_label)
        
        last_saved_label = QLabel("Last Saved: Never")
        last_saved_label.setStyleSheet("color: #666; font-size: 11px;")
        info_layout.addWidget(last_saved_label)
        
        self.content_layout.addLayout(info_layout)
        
        # Action buttons
        actions_layout = QVBoxLayout()
        
        save_btn = QPushButton("💾 Save Settings")
        load_btn = QPushButton("📂 Load Settings")
        reset_btn = QPushButton("🔄 Reset to Defaults")
        export_btn = QPushButton("📤 Export Config")
        
        save_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; border: none; padding: 8px; border-radius: 4px; margin: 2px; }")
        load_btn.setStyleSheet("QPushButton { background-color: #007bff; color: white; border: none; padding: 8px; border-radius: 4px; margin: 2px; }")
        reset_btn.setStyleSheet("QPushButton { background-color: #ffc107; color: black; border: none; padding: 8px; border-radius: 4px; margin: 2px; }")
        export_btn.setStyleSheet("QPushButton { background-color: #6c757d; color: white; border: none; padding: 8px; border-radius: 4px; margin: 2px; }")
        
        save_btn.clicked.connect(self.save_settings)
        load_btn.clicked.connect(self.load_settings)
        reset_btn.clicked.connect(self.reset_settings)
        export_btn.clicked.connect(self.export_config)
        
        actions_layout.addWidget(save_btn)
        actions_layout.addWidget(load_btn)
        actions_layout.addWidget(reset_btn)
        actions_layout.addWidget(export_btn)
        
        self.content_layout.addLayout(actions_layout)
    
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
            QMessageBox.information(self, "Reset Settings", "Settings reset to defaults!")
    
    def export_config(self):
        """Export configuration"""
        QMessageBox.information(self, "Export Config", "Configuration exported successfully!")

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
        """Create navigation tree items for dashboard"""
        # Dashboard
        dashboard_item = QTreeWidgetItem(["📊 Dashboard"])
        dashboard_item.setData(0, Qt.UserRole, ("dashboard", "main"))
        self.nav_tree.addTopLevelItem(dashboard_item)
        
        # Debug
        debug_item = QTreeWidgetItem(["🐛 Debug"])
        debug_item.setData(0, Qt.UserRole, ("debug", "main"))
        self.nav_tree.addTopLevelItem(debug_item)
        
        # Select first item by default
        self.nav_tree.setCurrentItem(dashboard_item)
    
    def on_item_clicked(self, item, column):
        """Handle navigation item click"""
        data = item.data(0, Qt.UserRole)
        if data:
            section, subsection = data
            self.item_selected.emit(section, subsection)

class DashboardGrid(QScrollArea):
    """Scrollable grid container for modular cards"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Container widget
        container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(8)
        self.grid_layout.setContentsMargins(16, 16, 16, 16)
        
        # Create cards
        self.cards = [
            BasicConfigCard(),      # (0, 0)
            FilePathsCard(),        # (0, 1)
            DRCSettingsCard(),      # (1, 0)
            PerformanceCard(),      # (1, 1)
            PackageActionsCard(),   # (2, 0)
            CompareActionsCard(),   # (2, 1)
            SettingsActionsCard()   # (0, 2) - spans across
        ]
        
        # Add cards to grid - optimized layout
        self.grid_layout.addWidget(self.cards[0], 0, 0)  # Basic Config
        self.grid_layout.addWidget(self.cards[1], 0, 1)  # File Paths
        self.grid_layout.addWidget(self.cards[2], 1, 0)  # DRC Settings
        self.grid_layout.addWidget(self.cards[3], 1, 1)  # Performance
        self.grid_layout.addWidget(self.cards[4], 2, 0)  # Package Actions
        self.grid_layout.addWidget(self.cards[5], 2, 1)  # Compare Actions
        self.grid_layout.addWidget(self.cards[6], 0, 2, 3, 1)  # Settings Actions (spans 3 rows)
        
        container.setLayout(self.grid_layout)
        self.setWidget(container)

class MainContentArea(QWidget):
    """Main content area with dashboard layout"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Header area
        self.header_layout = QHBoxLayout()
        self.title_label = QLabel("Dashboard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        
        self.subtitle_label = QLabel("Configure settings and manage packages using modular cards")
        self.subtitle_label.setStyleSheet("color: #666; font-style: italic;")
        
        header_v_layout = QVBoxLayout()
        header_v_layout.addWidget(self.title_label)
        header_v_layout.addWidget(self.subtitle_label)
        header_v_layout.setSpacing(2)
        
        # Quick stats
        stats_layout = QHBoxLayout()
        
        config_status = QLabel("📊 Config: Ready")
        config_status.setStyleSheet("background-color: #d4edda; color: #155724; padding: 4px 8px; border-radius: 4px; font-size: 11px;")
        
        package_status = QLabel("📦 Package: Not Created")
        package_status.setStyleSheet("background-color: #f8d7da; color: #721c24; padding: 4px 8px; border-radius: 4px; font-size: 11px;")
        
        compare_status = QLabel("🔍 Compare: Not Run")
        compare_status.setStyleSheet("background-color: #fff3cd; color: #856404; padding: 4px 8px; border-radius: 4px; font-size: 11px;")
        
        stats_layout.addWidget(config_status)
        stats_layout.addWidget(package_status)
        stats_layout.addWidget(compare_status)
        stats_layout.addStretch()
        
        self.header_layout.addLayout(header_v_layout)
        self.header_layout.addStretch()
        self.header_layout.addLayout(stats_layout)
        
        # Content stack
        self.content_stack = QStackedWidget()
        
        # Create pages
        self.create_dashboard_page()  # Index 0
        self.create_debug_page()      # Index 1
        
        self.layout.addLayout(self.header_layout)
        self.layout.addWidget(self.content_stack)
        
        self.setLayout(self.layout)
    
    def create_dashboard_page(self):
        """Create dashboard page with modular cards"""
        # Dashboard grid
        self.dashboard_grid = DashboardGrid()
        self.content_stack.addWidget(self.dashboard_grid)  # Index 0
    
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
        if section == "dashboard":
            self.title_label.setText("Dashboard")
            self.subtitle_label.setText("Configure settings and manage packages using modular cards")
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
        self.setWindowTitle("QA MRVL Techlib Tool - Dashboard Layout")
        self.setGeometry(100, 100, 1400, 900)
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
        splitter.setSizes([180, 1220])
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
        self.section_label = QLabel("Current: Dashboard")
        self.status_bar.addPermanentWidget(self.section_label)
    
    def on_navigation_changed(self, section, subsection):
        """Handle navigation panel selection change"""
        self.content_area.show_content(section, subsection)
        
        # Update status bar
        section_names = {
            "dashboard": "Dashboard",
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
