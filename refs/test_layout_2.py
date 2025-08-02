import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QStatusBar, 
                             QProgressBar, QTableWidget, QTableWidgetItem,
                             QCheckBox, QComboBox, QSpinBox, QGroupBox, QFormLayout,
                             QFrame, QScrollArea, QTextEdit, QSlider, QLineEdit, 
                             QTreeWidget, QTreeWidgetItem, QSplitter, QStackedWidget,
                             QMessageBox, QFileDialog, QDialogButtonBox, QDialog)
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
        
        # Package Creator
        package_item = QTreeWidgetItem([" Package Creator"])
        package_item.setData(0, Qt.UserRole, ("package_creator", "main"))
        self.nav_tree.addTopLevelItem(package_item)
        
        # Compare Packages
        compare_item = QTreeWidgetItem([" Compare Packages"])
        compare_item.setData(0, Qt.UserRole, ("compare_packages", "main"))
        self.nav_tree.addTopLevelItem(compare_item)
        
        # Debug section with sub-items
        debug_item = QTreeWidgetItem([" Debug"])
        debug_item.setData(0, Qt.UserRole, ("debug", "main"))
        
        # Debug sub-items
        logs_item = QTreeWidgetItem([" Logs"])
        logs_item.setData(0, Qt.UserRole, ("debug", "logs"))
        debug_item.addChild(logs_item)
        
        errors_item = QTreeWidgetItem(["❌ Errors"])
        errors_item.setData(0, Qt.UserRole, ("debug", "errors"))
        debug_item.addChild(errors_item)
        
        data_item = QTreeWidgetItem([" Data"])
        data_item.setData(0, Qt.UserRole, ("debug", "data"))
        debug_item.addChild(data_item)
        
        analysis_item = QTreeWidgetItem([" Analysis"])
        analysis_item.setData(0, Qt.UserRole, ("debug", "analysis"))
        debug_item.addChild(analysis_item)
        
        self.nav_tree.addTopLevelItem(debug_item)
        debug_item.setExpanded(True)  # Expand Debug by default
        
        # # Settings
        # settings_item = QTreeWidgetItem(["⚙️ Settings"])
        # settings_item.setData(0, Qt.UserRole, ("settings", "main"))
        # self.nav_tree.addTopLevelItem(settings_item)
        
        # Select first item by default
        self.nav_tree.setCurrentItem(package_item)
    
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
        self.title_label = QLabel("Package Creator")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        
        self.subtitle_label = QLabel("Create and manage software packages")
        self.subtitle_label.setStyleSheet("color: #666; font-style: italic;")
        
        header_v_layout = QVBoxLayout()
        header_v_layout.addWidget(self.title_label)
        header_v_layout.addWidget(self.subtitle_label)
        header_v_layout.setSpacing(2)
        
        self.header_layout.addLayout(header_v_layout)
        self.header_layout.addStretch()
        
        # Content stack
        self.content_stack = QStackedWidget()
        
        # Move settings page to top
        self.create_settings_page()  # Index 0
        self.create_package_creator_page()  # Index 1
        self.create_compare_packages_page()  # Index 2
        self.create_debug_pages()  # Index 3-7
        
        self.layout.addLayout(self.header_layout)
        self.layout.addWidget(self.content_stack)
        
        self.setLayout(self.layout)
    
    def create_package_creator_page(self):
        """Create Package Creator interface"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Package details form
        form_group = QGroupBox("Package Details")
        form_layout = QFormLayout()
        
        self.package_name_edit = QLineEdit()
        self.package_name_edit.setPlaceholderText("Enter package name...")
        form_layout.addRow("Package Name:", self.package_name_edit)
        
        self.version_edit = QLineEdit()
        self.version_edit.setPlaceholderText("1.0.0")
        form_layout.addRow("Version:", self.version_edit)
        
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Select output directory...")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_output_dir)
        
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.output_dir_edit)
        dir_layout.addWidget(browse_btn)
        form_layout.addRow("Output Directory:", dir_layout)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["ZIP", "TAR.GZ", "7Z", "RAR"])
        form_layout.addRow("Format:", self.format_combo)
        
        form_group.setLayout(form_layout)
        
        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        self.include_source_cb = QCheckBox("Include source files")
        self.include_source_cb.setChecked(True)
        options_layout.addWidget(self.include_source_cb)
        
        self.validate_cb = QCheckBox("Validate package after creation")
        self.validate_cb.setChecked(True)
        options_layout.addWidget(self.validate_cb)
        
        self.compress_cb = QCheckBox("Use compression")
        options_layout.addWidget(self.compress_cb)
        
        options_group.setLayout(options_layout)
        
        # Action buttons
        action_layout = QHBoxLayout()
        create_btn = QPushButton(" Create Package")
        create_btn.setFixedHeight(40)
        create_btn.clicked.connect(self.create_package)
        
        preview_btn = QPushButton(" Preview")
        preview_btn.clicked.connect(self.preview_package)
        
        action_layout.addWidget(create_btn)
        action_layout.addWidget(preview_btn)
        action_layout.addStretch()
        
        layout.addWidget(form_group)
        layout.addWidget(options_group)
        layout.addLayout(action_layout)
        layout.addStretch()
        
        page.setLayout(layout)
        self.content_stack.addWidget(page)  # Index 1
    
    def create_compare_packages_page(self):
        """Create Package Comparison interface"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Comparison setup
        setup_group = QGroupBox("Package Selection")
        setup_layout = QFormLayout()
        
        self.package1_edit = QLineEdit()
        self.package1_edit.setPlaceholderText("Select first package...")
        browse1_btn = QPushButton("Browse...")
        pkg1_layout = QHBoxLayout()
        pkg1_layout.addWidget(self.package1_edit)
        pkg1_layout.addWidget(browse1_btn)
        setup_layout.addRow("Package 1:", pkg1_layout)
        
        self.package2_edit = QLineEdit()
        self.package2_edit.setPlaceholderText("Select second package...")
        browse2_btn = QPushButton("Browse...")
        pkg2_layout = QHBoxLayout()
        pkg2_layout.addWidget(self.package2_edit)
        pkg2_layout.addWidget(browse2_btn)
        setup_layout.addRow("Package 2:", pkg2_layout)
        
        setup_group.setLayout(setup_layout)
        
        # Comparison options
        options_group = QGroupBox("Comparison Options")
        options_layout = QVBoxLayout()
        
        self.compare_structure_cb = QCheckBox("Compare file structure")
        self.compare_structure_cb.setChecked(True)
        options_layout.addWidget(self.compare_structure_cb)
        
        self.compare_content_cb = QCheckBox("Compare file contents")
        options_layout.addWidget(self.compare_content_cb)
        
        self.ignore_timestamps_cb = QCheckBox("Ignore timestamps")
        options_layout.addWidget(self.ignore_timestamps_cb)
        
        options_group.setLayout(options_layout)
        
        # Results area
        results_group = QGroupBox("Comparison Results")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setPlaceholderText("Comparison results will appear here...")
        self.results_text.setMaximumHeight(200)
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        
        # Action buttons
        action_layout = QHBoxLayout()
        compare_btn = QPushButton(" Compare Packages")
        compare_btn.setFixedHeight(40)
        compare_btn.clicked.connect(self.compare_packages)
        
        export_btn = QPushButton(" Export Report")
        export_btn.clicked.connect(self.export_comparison)
        
        action_layout.addWidget(compare_btn)
        action_layout.addWidget(export_btn)
        action_layout.addStretch()
        
        layout.addWidget(setup_group)
        layout.addWidget(options_group)
        layout.addWidget(results_group)
        layout.addLayout(action_layout)
        
        page.setLayout(layout)
        self.content_stack.addWidget(page)  # Index 2
    
    def create_debug_pages(self):
        """Create Debug pages (Logs, Errors, Data, Analysis)"""
        # Debug Main Page (Index 3)
        debug_main = QWidget()
        debug_layout = QVBoxLayout()
        debug_layout.addWidget(QLabel("Select a debug category from the left panel"))
        debug_main.setLayout(debug_layout)
        self.content_stack.addWidget(debug_main)
        
        # Logs Page (Index 4)
        logs_page = QWidget()
        logs_layout = QVBoxLayout()
        
        # Log controls
        log_controls = QHBoxLayout()
        log_level_combo = QComboBox()
        log_level_combo.addItems(["All", "ERROR", "WARNING", "INFO", "DEBUG"])
        log_controls.addWidget(QLabel("Level:"))
        log_controls.addWidget(log_level_combo)
        
        clear_logs_btn = QPushButton("Clear Logs")
        log_controls.addWidget(clear_logs_btn)
        log_controls.addStretch()
        
        # Log display
        self.logs_text = QTextEdit()
        self.populate_sample_logs()
        
        logs_layout.addLayout(log_controls)
        logs_layout.addWidget(self.logs_text)
        logs_page.setLayout(logs_layout)
        self.content_stack.addWidget(logs_page)  # Index 4
        
        # Errors Page (Index 5)
        errors_page = QWidget()
        errors_layout = QVBoxLayout()
        
        error_table = QTableWidget(5, 4)
        error_table.setHorizontalHeaderLabels(["Time", "Level", "Component", "Message"])
        
        sample_errors = [
            ("10:15:23", "ERROR", "PackageCreator", "Failed to create package: Permission denied"),
            ("10:14:12", "WARNING", "Validator", "Package size exceeds recommended limit"),
            ("10:12:45", "ERROR", "FileManager", "Cannot access file: /tmp/package.zip"),
            ("10:11:30", "WARNING", "Compressor", "Low compression ratio detected"),
            ("10:10:15", "ERROR", "Network", "Connection timeout")
        ]
        
        for i, (time, level, comp, msg) in enumerate(sample_errors):
            error_table.setItem(i, 0, QTableWidgetItem(time))
            error_table.setItem(i, 1, QTableWidgetItem(level))
            error_table.setItem(i, 2, QTableWidgetItem(comp))
            error_table.setItem(i, 3, QTableWidgetItem(msg))
        
        errors_layout.addWidget(error_table)
        errors_page.setLayout(errors_layout)
        self.content_stack.addWidget(errors_page)  # Index 5
        
        # Data Page (Index 6)
        data_page = QWidget()
        data_layout = QVBoxLayout()
        
        data_table = QTableWidget(10, 5)
        data_table.setHorizontalHeaderLabels(["ID", "Package", "Size (MB)", "Files", "Status"])
        
        # Populate with sample data
        for i in range(10):
            data_table.setItem(i, 0, QTableWidgetItem(f"PKG_{i:03d}"))
            data_table.setItem(i, 1, QTableWidgetItem(f"Package_{i}"))
            data_table.setItem(i, 2, QTableWidgetItem(f"{(i+1)*2.5:.1f}"))
            data_table.setItem(i, 3, QTableWidgetItem(f"{(i+1)*15}"))
            status = "Active" if i % 3 != 0 else "Inactive"
            data_table.setItem(i, 4, QTableWidgetItem(status))
        
        data_layout.addWidget(data_table)
        data_page.setLayout(data_layout)
        self.content_stack.addWidget(data_page)  # Index 6
        
        # Analysis Page (Index 7)
        analysis_page = QWidget()
        analysis_layout = QVBoxLayout()
        
        analysis_text = QTextEdit()
        analysis_text.setHtml("""
        <h3>Package Analysis Report</h3>
        <p><strong>Total Packages Processed:</strong> 156</p>
        <p><strong>Success Rate:</strong> 94.2%</p>
        <p><strong>Average Package Size:</strong> 12.4 MB</p>
        <p><strong>Most Common Errors:</strong></p>
        <ul>
            <li>Permission denied (23 occurrences)</li>
            <li>File not found (18 occurrences)</li>
            <li>Network timeout (12 occurrences)</li>
        </ul>
        <p><strong>Performance Metrics:</strong></p>
        <ul>
            <li>Average creation time: 2.3 seconds</li>
            <li>Peak memory usage: 245 MB</li>
            <li>CPU utilization: 45%</li>
        </ul>
        """)
        
        analysis_layout.addWidget(analysis_text)
        analysis_page.setLayout(analysis_layout)
        self.content_stack.addWidget(analysis_page)  # Index 7
    
    def create_settings_page(self):
        """Create Settings page (now with common settings fields)"""
        page = QWidget()
        layout = QVBoxLayout()
        form_group = QGroupBox("Application Settings")
        form_layout = QFormLayout()
        # Add common settings fields
        self.run_dir_edit = QLineEdit("./output_qa")
        self.run_dir_edit.setPlaceholderText("Enter run directory path")
        form_layout.addRow("Run Directory:", self.run_dir_edit)
        self.max_instances_edit = QSpinBox()
        self.max_instances_edit.setRange(1, 1000)
        self.max_instances_edit.setValue(50)
        form_layout.addRow("Max Instances:", self.max_instances_edit)
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText("INFO")
        form_layout.addRow("Log Level:", self.log_level_combo)
        self.max_jobs_edit = QSpinBox()
        self.max_jobs_edit.setRange(1, 1000)
        self.max_jobs_edit.setValue(100)
        form_layout.addRow("Max Jobs:", self.max_jobs_edit)
        self.retries_edit = QSpinBox()
        self.retries_edit.setRange(0, 10)
        self.retries_edit.setValue(2)
        form_layout.addRow("Retries:", self.retries_edit)
        self.cdsinit_edit = QLineEdit("")
        self.cdsinit_edit.setPlaceholderText("Enter path to cdsinit local file")
        form_layout.addRow(".cdsinit:", self.cdsinit_edit)
        self.save_express_pcells_cb = QCheckBox("Save .expressPcells")
        self.save_express_pcells_cb.setChecked(True)
        self.cleanup_run_dir_cb = QCheckBox("Cleanup Run Directory")
        self.cleanup_run_dir_cb.setChecked(False)
        options_row = QHBoxLayout()
        options_row.addWidget(self.save_express_pcells_cb)
        options_row.addWidget(self.cleanup_run_dir_cb)
        form_layout.addRow("Options:", options_row)
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        layout.addStretch()
        page.setLayout(layout)
        self.content_stack.addWidget(page)  # Index 0
    
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
        """Show content based on left panel selection"""
        content_map = {
            ("settings", "main"): (0, "Settings", "Application settings"),
            ("package_creator", "main"): (1, " Package Creator", "Create and manage software packages"),
            ("compare_packages", "main"): (2, " Compare Packages", "Compare two packages side by side"),
            ("debug", "main"): (3, " Debug", "Debug tools and information"),
            ("debug", "logs"): (4, " Debug Logs", "Application logs and system messages"),
            ("debug", "errors"): (5, "❌ Error Reports", "Error tracking and analysis"),
            ("debug", "data"): (6, " Data Tables", "Raw data and statistics"),
            ("debug", "analysis"): (7, " Analysis", "Performance analysis and reports")
        }
        
        if (section, subsection) in content_map:
            index, title, subtitle = content_map[(section, subsection)]
            self.content_stack.setCurrentIndex(index)
            self.title_label.setText(title)
            self.subtitle_label.setText(subtitle)
        # ...existing code...

    def show_settings_dialog(self):
        pass  # No longer used
    
    def browse_output_dir(self):
        """Browse for output directory"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            self.output_dir_edit.setText(dir_path)
    
    def create_package(self):
        """Create package"""
        if self.parent_widget:
            self.parent_widget.simulate_operation("Creating package...", "Package created successfully")
    
    def preview_package(self):
        """Preview package"""
        QMessageBox.information(self, "Package Preview", "Package preview functionality would be implemented here.")
    
    def compare_packages(self):
        """Compare packages"""
        if self.parent_widget:
            self.parent_widget.simulate_operation("Comparing packages...", "Package comparison completed")
            self.results_text.setText("Comparison completed:\n\n✓ File structure: Identical\n✗ File contents: 3 differences found\n✓ Metadata: Match")
    
    def export_comparison(self):
        """Export comparison report"""
        QMessageBox.information(self, "Export Report", "Comparison report export functionality would be implemented here.")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QA MRVL Techlib Tool - Side Panel Navigation")
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
        self.section_label = QLabel("Current: Package Creator")
        self.status_bar.addPermanentWidget(self.section_label)
    
    def on_navigation_changed(self, section, subsection):
        """Handle navigation panel selection change"""
        self.content_area.show_content(section, subsection)
        
        # Update status bar
        section_names = {
            "package_creator": "Package Creator",
            "compare_packages": "Compare Packages", 
            "debug": "Debug",
            "settings": "Settings"
        }
        
        current_section = section_names.get(section, section)
        if subsection != "main":
            current_section += f" > {subsection.title()}"
        
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