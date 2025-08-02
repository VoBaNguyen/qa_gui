"""
Layout Idea 1: Collapsible Accordion Layout
- Settings ở top dạng accordion có thể thu gọn/mở rộng
- Create Package và Compare Packages ở bottom dạng tabs
- Mỗi section trong Settings có thể collapse để tiết kiệm không gian
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QGroupBox, QFormLayout,
                             QComboBox, QLineEdit, QCheckBox, QSplitter, QTabWidget,
                             QScrollArea, QCollapsibleGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class CollapsibleGroupBox(QGroupBox):
    """Custom collapsible group box"""
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(True)
        self.toggled.connect(self.on_toggled)
        
    def on_toggled(self, checked):
        # Hide/show content when toggled
        for child in self.children():
            if hasattr(child, 'setVisible'):
                child.setVisible(checked)

class AccordionSettingsWidget(QWidget):
    """Settings with collapsible sections"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Required Settings (Always expanded)
        required_group = CollapsibleGroupBox("📋 Required Settings")
        required_layout = QFormLayout()
        
        self.techlib_combo = QComboBox()
        self.techlib_combo.addItems(["gf12lpp", "gf22fdx", "gf28hpk"])
        required_layout.addRow("Techlib:", self.techlib_combo)
        
        qa_types_layout = QHBoxLayout()
        self.cdf_cb = QCheckBox("CDF")
        self.drc_cb = QCheckBox("DRC")
        self.ta_cb = QCheckBox("TA")
        qa_types_layout.addWidget(self.cdf_cb)
        qa_types_layout.addWidget(self.drc_cb)
        qa_types_layout.addWidget(self.ta_cb)
        required_layout.addRow("QA Types:", qa_types_layout)
        
        required_group.setLayout(required_layout)
        
        # DRC Settings (Collapsible)
        drc_group = CollapsibleGroupBox("🔧 DRC Settings")
        drc_group.setChecked(False)  # Initially collapsed
        drc_layout = QFormLayout()
        
        self.proj_mpv_edit = QLineEdit()
        drc_layout.addRow("Project MPV:", self.proj_mpv_edit)
        
        self.runcalx_edit = QLineEdit()
        drc_layout.addRow("Runcalx Version:", self.runcalx_edit)
        
        drc_group.setLayout(drc_layout)
        
        # Advanced Settings (Collapsible)
        advanced_group = CollapsibleGroupBox("⚙️ Advanced Settings")
        advanced_group.setChecked(False)  # Initially collapsed
        advanced_layout = QFormLayout()
        
        self.max_jobs_edit = QLineEdit("100")
        advanced_layout.addRow("Max Jobs:", self.max_jobs_edit)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        advanced_layout.addRow("Log Level:", self.log_level_combo)
        
        advanced_group.setLayout(advanced_layout)
        
        layout.addWidget(required_group)
        layout.addWidget(drc_group)
        layout.addWidget(advanced_group)
        layout.addStretch()
        
        self.setLayout(layout)

class ActionTabsWidget(QTabWidget):
    """Bottom tabs for Create Package and Compare Packages"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        # Create Package Tab
        create_tab = QWidget()
        create_layout = QVBoxLayout()
        
        create_group = QGroupBox("Package Creation")
        create_form = QFormLayout()
        
        self.cds_lib_edit = QLineEdit()
        create_form.addRow("cds.lib:", self.cds_lib_edit)
        
        self.run_dir_edit = QLineEdit("./output_qa")
        create_form.addRow("Run Directory:", self.run_dir_edit)
        
        create_group.setLayout(create_form)
        
        create_buttons = QHBoxLayout()
        create_buttons.addStretch()
        create_buttons.addWidget(QPushButton("Verify"))
        create_buttons.addWidget(QPushButton("Create"))
        
        create_layout.addWidget(create_group)
        create_layout.addLayout(create_buttons)
        create_layout.addStretch()
        create_tab.setLayout(create_layout)
        
        # Compare Package Tab
        compare_tab = QWidget()
        compare_layout = QVBoxLayout()
        
        compare_group = QGroupBox("Package Comparison")
        compare_form = QFormLayout()
        
        self.golden_path_edit = QLineEdit("./package_golden")
        compare_form.addRow("Golden Path:", self.golden_path_edit)
        
        self.alpha_path_edit = QLineEdit("./package_alpha")
        compare_form.addRow("Alpha Path:", self.alpha_path_edit)
        
        compare_group.setLayout(compare_form)
        
        compare_buttons = QHBoxLayout()
        compare_buttons.addStretch()
        compare_buttons.addWidget(QPushButton("Verify"))
        compare_buttons.addWidget(QPushButton("Compare"))
        
        compare_layout.addWidget(compare_group)
        compare_layout.addLayout(compare_buttons)
        compare_layout.addStretch()
        compare_tab.setLayout(compare_layout)
        
        self.addTab(create_tab, "📦 Create Package")
        self.addTab(compare_tab, "🔍 Compare Packages")

class MainLayoutIdea1(QWidget):
    """Main layout combining accordion settings with action tabs"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        # Main vertical splitter
        splitter = QSplitter(Qt.Vertical)
        
        # Top: Settings (Accordion)
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setMaximumHeight(400)  # Limit height
        
        self.settings_widget = AccordionSettingsWidget()
        settings_scroll.setWidget(self.settings_widget)
        
        # Bottom: Action Tabs
        self.action_tabs = ActionTabsWidget()
        
        splitter.addWidget(settings_scroll)
        splitter.addWidget(self.action_tabs)
        splitter.setSizes([300, 500])  # Settings smaller, actions larger
        
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setCentralWidget(MainLayoutIdea1())
    window.setWindowTitle("Layout Idea 1: Accordion Settings + Action Tabs")
    window.setGeometry(100, 100, 800, 900)
    window.show()
    sys.exit(app.exec_())
