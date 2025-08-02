"""
Layout Idea 4: Dashboard Layout with Modular Cards
- Dashboard-style với các module cards có thể resize
- Mỗi card là một functional unit
- Drag & drop để reorganize layout
- Responsive grid layout
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QGroupBox, QFormLayout,
                             QComboBox, QLineEdit, QCheckBox, QGridLayout, QFrame,
                             QTextEdit, QScrollArea, QSizePolicy, QSplitter, QTabWidget)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
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
        self.techlib_combo.addItems(["gf12lpp", "gf22fdx", "gf28hpk", "gf12lp"])
        techlib_layout.addRow("Techlib:", self.techlib_combo)
        
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

class QATypesCard(ModularCard):
    """QA Types selection card"""
    def __init__(self):
        super().__init__("QA Types", "🔍")
        self.setup_content()
        
    def setup_content(self):
        qa_layout = QVBoxLayout()
        
        # QA type checkboxes
        self.cdf_cb = QCheckBox("CDF (Circuit Design Framework)")
        self.cdf_cb.setChecked(True)
        self.drc_cb = QCheckBox("DRC (Design Rule Check)")
        self.ta_cb = QCheckBox("TA (Timing Analysis)")
        
        qa_layout.addWidget(self.cdf_cb)
        qa_layout.addWidget(self.drc_cb)
        qa_layout.addWidget(self.ta_cb)
        
        # DRC specific settings (initially hidden)
        self.drc_group = QGroupBox("DRC Settings")
        drc_layout = QFormLayout()
        
        self.proj_mpv_edit = QLineEdit()
        drc_layout.addRow("Project MPV:", self.proj_mpv_edit)
        
        self.runcalx_edit = QLineEdit()
        drc_layout.addRow("Runcalx Version:", self.runcalx_edit)
        
        self.drc_group.setLayout(drc_layout)
        self.drc_group.setVisible(False)
        
        # Connect DRC checkbox
        self.drc_cb.toggled.connect(self.drc_group.setVisible)
        
        qa_layout.addWidget(self.drc_group)
        
        self.content_layout.addLayout(qa_layout)

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
        
        # CDS lib
        cds_layout = QHBoxLayout()
        self.cds_lib_edit = QLineEdit()
        self.cds_lib_edit.setPlaceholderText("cds.lib file")
        cds_browse_btn = QPushButton("📂")
        cds_browse_btn.setFixedSize(30, 25)
        cds_layout.addWidget(self.cds_lib_edit)
        cds_layout.addWidget(cds_browse_btn)
        paths_layout.addRow("cds.lib:", cds_layout)
        
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
        
        actions_layout.addWidget(save_btn)
        actions_layout.addWidget(load_btn)
        actions_layout.addWidget(reset_btn)
        actions_layout.addWidget(export_btn)
        
        self.content_layout.addLayout(actions_layout)

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
            QATypesCard(),         # (0, 1)
            FilePathsCard(),       # (1, 0)
            PerformanceCard(),     # (1, 1)
            PackageActionsCard(),  # (2, 0)
            CompareActionsCard(),  # (2, 1)
            SettingsActionsCard()  # (0, 2) - spans across
        ]
        
        # Add cards to grid
        self.grid_layout.addWidget(self.cards[0], 0, 0)  # Basic Config
        self.grid_layout.addWidget(self.cards[1], 0, 1)  # QA Types
        self.grid_layout.addWidget(self.cards[2], 1, 0)  # File Paths
        self.grid_layout.addWidget(self.cards[3], 1, 1)  # Performance
        self.grid_layout.addWidget(self.cards[4], 2, 0)  # Package Actions
        self.grid_layout.addWidget(self.cards[5], 2, 1)  # Compare Actions
        self.grid_layout.addWidget(self.cards[6], 0, 2, 3, 1)  # Settings Actions (spans 3 rows)
        
        container.setLayout(self.grid_layout)
        self.setWidget(container)

class MainLayoutIdea4(QWidget):
    """Main dashboard layout with modular cards"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(16, 16, 16, 8)
        
        title = QLabel("QA MRVL Tool Dashboard")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        
        subtitle = QLabel("Configure settings and manage packages using modular cards")
        subtitle.setStyleSheet("color: #666; font-style: italic;")
        
        header_v_layout = QVBoxLayout()
        header_v_layout.setSpacing(2)
        header_v_layout.addWidget(title)
        header_v_layout.addWidget(subtitle)
        
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
        
        header_layout.addLayout(header_v_layout)
        header_layout.addStretch()
        header_layout.addLayout(stats_layout)
        
        # Dashboard grid
        self.dashboard_grid = DashboardGrid()
        
        layout.addLayout(header_layout)
        layout.addWidget(self.dashboard_grid)
        
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setCentralWidget(MainLayoutIdea4())
    window.setWindowTitle("Layout Idea 4: Dashboard Layout with Modular Cards")
    window.setGeometry(100, 100, 1200, 800)
    window.show()
    sys.exit(app.exec_())
