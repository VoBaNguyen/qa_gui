"""
Layout Idea 3: Sidebar Navigation with Contextual Panels
- Left sidebar với các category chính
- Main area thay đổi theo selection
- Settings được group theo context
- Quick actions panel ở right side
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QGroupBox, QFormLayout,
                             QComboBox, QLineEdit, QCheckBox, QListWidget, QListWidgetItem,
                             QSplitter, QFrame, QTextEdit, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

class SettingsCategoryList(QListWidget):
    """Left sidebar for settings categories"""
    category_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedWidth(200)
        self.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #f5f5f5;
                alternate-background-color: #efefef;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #ddd;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        
        categories = [
            ("⚙️ Basic Settings", "basic"),
            ("🔧 QA Configuration", "qa_config"),
            ("📁 File Paths", "file_paths"),
            ("🚀 Performance", "performance"),
            ("📦 Package Actions", "package_actions"),
            ("🔍 Compare Actions", "compare_actions")
        ]
        
        for display_name, category_id in categories:
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, category_id)
            self.addItem(item)
            
        self.setCurrentRow(0)
        self.itemSelectionChanged.connect(self.on_selection_changed)
        
    def on_selection_changed(self):
        current_item = self.currentItem()
        if current_item:
            category_id = current_item.data(Qt.UserRole)
            self.category_changed.emit(category_id)

class BasicSettingsPanel(QWidget):
    """Basic settings panel"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Basic Settings")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        
        form_group = QGroupBox("Essential Configuration")
        form_layout = QFormLayout()
        
        self.techlib_combo = QComboBox()
        self.techlib_combo.addItems(["gf12lpp", "gf22fdx", "gf28hpk", "gf12lp", "gf14lpp"])
        form_layout.addRow("Technology Library:", self.techlib_combo)
        
        self.virtuoso_cmd_edit = QLineEdit()
        self.virtuoso_cmd_edit.setPlaceholderText("Enter Virtuoso command")
        form_layout.addRow("Virtuoso Command:", self.virtuoso_cmd_edit)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText("INFO")
        form_layout.addRow("Log Level:", self.log_level_combo)
        
        form_group.setLayout(form_layout)
        
        layout.addWidget(title)
        layout.addWidget(form_group)
        layout.addStretch()
        
        self.setLayout(layout)

class QAConfigPanel(QWidget):
    """QA Configuration panel"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("QA Configuration")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        
        # QA Types
        qa_group = QGroupBox("QA Types")
        qa_layout = QVBoxLayout()
        
        self.cdf_cb = QCheckBox("CDF (Circuit Design Framework)")
        self.cdf_cb.setChecked(True)
        self.drc_cb = QCheckBox("DRC (Design Rule Check)")
        self.ta_cb = QCheckBox("TA (Timing Analysis)")
        
        qa_layout.addWidget(self.cdf_cb)
        qa_layout.addWidget(self.drc_cb)
        qa_layout.addWidget(self.ta_cb)
        qa_group.setLayout(qa_layout)
        
        # DRC Specific
        self.drc_group = QGroupBox("DRC Specific Settings")
        drc_layout = QFormLayout()
        
        self.proj_mpv_edit = QLineEdit()
        drc_layout.addRow("Project MPV:", self.proj_mpv_edit)
        
        self.mpvopts_edit = QLineEdit()
        drc_layout.addRow("mpvopt DRC:", self.mpvopts_edit)
        
        self.runcalx_edit = QLineEdit()
        drc_layout.addRow("Runcalx Version:", self.runcalx_edit)
        
        self.drc_group.setLayout(drc_layout)
        self.drc_group.setEnabled(False)
        
        self.drc_cb.toggled.connect(self.drc_group.setEnabled)
        
        layout.addWidget(title)
        layout.addWidget(qa_group)
        layout.addWidget(self.drc_group)
        layout.addStretch()
        
        self.setLayout(layout)

class FilePathsPanel(QWidget):
    """File paths configuration panel"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("File Paths Configuration")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        
        paths_group = QGroupBox("Required Files")
        paths_layout = QFormLayout()
        
        # QA Settings
        qa_layout = QHBoxLayout()
        self.qa_setting_edit = QLineEdit()
        qa_browse_btn = QPushButton("Browse")
        qa_view_btn = QPushButton("View")
        qa_layout.addWidget(self.qa_setting_edit)
        qa_layout.addWidget(qa_browse_btn)
        qa_layout.addWidget(qa_view_btn)
        paths_layout.addRow("QA Settings:", qa_layout)
        
        # PDK Configs
        pdk_layout = QHBoxLayout()
        self.pdk_config_edit = QLineEdit()
        self.pdk_config_edit.setReadOnly(True)
        pdk_load_btn = QPushButton("Load")
        pdk_view_btn = QPushButton("View")
        pdk_layout.addWidget(self.pdk_config_edit)
        pdk_layout.addWidget(pdk_load_btn)
        pdk_layout.addWidget(pdk_view_btn)
        paths_layout.addRow("PDK Configs:", pdk_layout)
        
        # cdsinit
        cdsinit_layout = QHBoxLayout()
        self.cdsinit_edit = QLineEdit()
        cdsinit_browse_btn = QPushButton("Browse")
        cdsinit_view_btn = QPushButton("View")
        cdsinit_layout.addWidget(self.cdsinit_edit)
        cdsinit_layout.addWidget(cdsinit_browse_btn)
        cdsinit_layout.addWidget(cdsinit_view_btn)
        paths_layout.addRow(".cdsinit:", cdsinit_layout)
        
        paths_group.setLayout(paths_layout)
        
        layout.addWidget(title)
        layout.addWidget(paths_group)
        layout.addStretch()
        
        self.setLayout(layout)

class PackageActionsPanel(QWidget):
    """Package creation actions"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Package Creation")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        
        config_group = QGroupBox("Package Configuration")
        config_layout = QFormLayout()
        
        # cds.lib
        cds_layout = QHBoxLayout()
        self.cds_lib_edit = QLineEdit()
        cds_browse_btn = QPushButton("Browse")
        cds_view_btn = QPushButton("View")
        cds_layout.addWidget(self.cds_lib_edit)
        cds_layout.addWidget(cds_browse_btn)
        cds_layout.addWidget(cds_view_btn)
        config_layout.addRow("cds.lib:", cds_layout)
        
        # PDK Version
        self.pdk_version_combo = QComboBox()
        self.pdk_version_combo.addItems(["Undefined"])
        config_layout.addRow("PDK Version:", self.pdk_version_combo)
        
        # Run Directory
        run_layout = QHBoxLayout()
        self.run_dir_edit = QLineEdit("./output_qa")
        run_browse_btn = QPushButton("Browse")
        run_layout.addWidget(self.run_dir_edit)
        run_layout.addWidget(run_browse_btn)
        config_layout.addRow("Run Directory:", run_layout)
        
        config_group.setLayout(config_layout)
        
        # Progress area
        progress_group = QGroupBox("Creation Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_text = QTextEdit()
        self.progress_text.setMaximumHeight(150)
        self.progress_text.setPlaceholderText("Package creation logs will appear here...")
        self.progress_text.setReadOnly(True)
        
        progress_layout.addWidget(self.progress_text)
        progress_group.setLayout(progress_layout)
        
        layout.addWidget(title)
        layout.addWidget(config_group)
        layout.addWidget(progress_group)
        layout.addStretch()
        
        self.setLayout(layout)

class CompareActionsPanel(QWidget):
    """Package comparison actions"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Package Comparison")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        
        # Quick comparison setup
        compare_group = QGroupBox("Quick Compare Setup")
        compare_layout = QFormLayout()
        
        # Golden package
        golden_layout = QHBoxLayout()
        self.golden_path_edit = QLineEdit("./package_golden")
        golden_browse_btn = QPushButton("Browse")
        golden_layout.addWidget(self.golden_path_edit)
        golden_layout.addWidget(golden_browse_btn)
        compare_layout.addRow("Golden Package:", golden_layout)
        
        # Alpha package
        alpha_layout = QHBoxLayout()
        self.alpha_path_edit = QLineEdit("./package_alpha")
        alpha_browse_btn = QPushButton("Browse")
        alpha_layout.addWidget(self.alpha_path_edit)
        alpha_layout.addWidget(alpha_browse_btn)
        compare_layout.addRow("Alpha Package:", alpha_layout)
        
        # Run directory
        run_layout = QHBoxLayout()
        self.compare_run_dir_edit = QLineEdit("./run_dir_compare")
        run_browse_btn = QPushButton("Browse")
        run_layout.addWidget(self.compare_run_dir_edit)
        run_layout.addWidget(run_browse_btn)
        compare_layout.addRow("Run Directory:", run_layout)
        
        # Options
        options_layout = QHBoxLayout()
        self.cleanup_cb = QCheckBox("Cleanup")
        self.rve_cb = QCheckBox("RVE")
        options_layout.addWidget(self.cleanup_cb)
        options_layout.addWidget(self.rve_cb)
        compare_layout.addRow("Options:", options_layout)
        
        compare_group.setLayout(compare_layout)
        
        # Results area
        results_group = QGroupBox("Comparison Results")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(200)
        self.results_text.setPlaceholderText("Comparison results will appear here...")
        self.results_text.setReadOnly(True)
        
        results_layout.addWidget(self.results_text)
        results_group.setLayout(results_layout)
        
        layout.addWidget(title)
        layout.addWidget(compare_group)
        layout.addWidget(results_group)
        layout.addStretch()
        
        self.setLayout(layout)

class QuickActionsPanel(QWidget):
    """Right sidebar with quick actions"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedWidth(180)
        layout = QVBoxLayout()
        
        title = QLabel("Quick Actions")
        title.setFont(QFont("Arial", 10, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        
        # Settings actions
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout()
        
        save_btn = QPushButton("💾 Save")
        load_btn = QPushButton("📂 Load")
        reset_btn = QPushButton("🔄 Reset")
        
        save_btn.setStyleSheet("text-align: left; padding: 8px;")
        load_btn.setStyleSheet("text-align: left; padding: 8px;")
        reset_btn.setStyleSheet("text-align: left; padding: 8px;")
        
        settings_layout.addWidget(save_btn)
        settings_layout.addWidget(load_btn)
        settings_layout.addWidget(reset_btn)
        settings_group.setLayout(settings_layout)
        
        # Package actions
        package_group = QGroupBox("Package")
        package_layout = QVBoxLayout()
        
        verify_btn = QPushButton("✅ Verify")
        create_btn = QPushButton("📦 Create")
        stop_btn = QPushButton("⏹️ Stop")
        
        verify_btn.setStyleSheet("text-align: left; padding: 8px;")
        create_btn.setStyleSheet("text-align: left; padding: 8px;")
        stop_btn.setStyleSheet("text-align: left; padding: 8px;")
        
        package_layout.addWidget(verify_btn)
        package_layout.addWidget(create_btn)
        package_layout.addWidget(stop_btn)
        package_group.setLayout(package_layout)
        
        # Compare actions
        compare_group = QGroupBox("Compare")
        compare_layout = QVBoxLayout()
        
        verify_compare_btn = QPushButton("✅ Verify")
        compare_packages_btn = QPushButton("🔍 Compare")
        export_btn = QPushButton("📊 Export")
        
        verify_compare_btn.setStyleSheet("text-align: left; padding: 8px;")
        compare_packages_btn.setStyleSheet("text-align: left; padding: 8px;")
        export_btn.setStyleSheet("text-align: left; padding: 8px;")
        
        compare_layout.addWidget(verify_compare_btn)
        compare_layout.addWidget(compare_packages_btn)
        compare_layout.addWidget(export_btn)
        compare_group.setLayout(compare_layout)
        
        layout.addWidget(title)
        layout.addWidget(settings_group)
        layout.addWidget(package_group)
        layout.addWidget(compare_group)
        layout.addStretch()
        
        self.setLayout(layout)

class MainContentArea(QWidget):
    """Main content area that changes based on category selection"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Create all panels
        self.panels = {
            'basic': BasicSettingsPanel(),
            'qa_config': QAConfigPanel(),
            'file_paths': FilePathsPanel(),
            'performance': self.create_performance_panel(),
            'package_actions': PackageActionsPanel(),
            'compare_actions': CompareActionsPanel()
        }
        
        # Add scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Show basic panel by default
        self.scroll_area.setWidget(self.panels['basic'])
        
        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)
        
    def create_performance_panel(self):
        """Create performance settings panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("Performance Settings")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        
        perf_group = QGroupBox("Execution Settings")
        perf_layout = QFormLayout()
        
        self.max_instances_edit = QLineEdit("50")
        perf_layout.addRow("Max Instances Per Cell View:", self.max_instances_edit)
        
        max_jobs_layout = QHBoxLayout()
        self.max_jobs_edit = QLineEdit("100")
        check_license_btn = QPushButton("Check License")
        max_jobs_layout.addWidget(self.max_jobs_edit)
        max_jobs_layout.addWidget(check_license_btn)
        perf_layout.addRow("Max Jobs:", max_jobs_layout)
        
        self.retries_edit = QLineEdit("2")
        perf_layout.addRow("Max Retries:", self.retries_edit)
        
        options_layout = QHBoxLayout()
        self.save_express_cb = QCheckBox("Save .expressPCell")
        self.cleanup_cb = QCheckBox("Cleanup Output")
        self.save_express_cb.setChecked(True)
        options_layout.addWidget(self.save_express_cb)
        options_layout.addWidget(self.cleanup_cb)
        perf_layout.addRow("Options:", options_layout)
        
        perf_group.setLayout(perf_layout)
        
        layout.addWidget(title)
        layout.addWidget(perf_group)
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
        
    def show_panel(self, category_id):
        """Show panel based on category selection"""
        if category_id in self.panels:
            self.scroll_area.setWidget(self.panels[category_id])

class MainLayoutIdea3(QWidget):
    """Main layout with sidebar navigation and contextual panels"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        # Main horizontal splitter
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left sidebar
        self.category_list = SettingsCategoryList()
        self.category_list.category_changed.connect(self.on_category_changed)
        
        # Main content area
        self.content_area = MainContentArea()
        
        # Right sidebar
        self.quick_actions = QuickActionsPanel()
        
        main_splitter.addWidget(self.category_list)
        main_splitter.addWidget(self.content_area)
        main_splitter.addWidget(self.quick_actions)
        
        # Set proportions: sidebar(200) : content(600) : actions(180)
        main_splitter.setSizes([200, 600, 180])
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_splitter)
        
        self.setLayout(layout)
        
    def on_category_changed(self, category_id):
        """Handle category selection change"""
        self.content_area.show_panel(category_id)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setCentralWidget(MainLayoutIdea3())
    window.setWindowTitle("Layout Idea 3: Sidebar Navigation with Contextual Panels")
    window.setGeometry(100, 100, 1000, 700)
    window.show()
    sys.exit(app.exec_())
