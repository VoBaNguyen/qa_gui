"""
Layout Idea 2: Wizard-Style Progressive Layout
- Settings được chia thành các bước (steps)
- Mỗi bước chỉ hiện những settings cần thiết
- Create/Compare được tích hợp vào wizard flow
- Có breadcrumb navigation để track progress
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QGroupBox, QFormLayout,
                             QComboBox, QLineEdit, QCheckBox, QStackedWidget,
                             QProgressBar, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class BreadcrumbWidget(QWidget):
    """Breadcrumb navigation for wizard steps"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        steps = ["Basic Config", "QA Types", "Paths", "Action"]
        
        for i, step in enumerate(steps):
            if i > 0:
                arrow = QLabel("→")
                arrow.setStyleSheet("color: #666; font-weight: bold;")
                layout.addWidget(arrow)
                
            step_label = QLabel(step)
            if i == 0:  # Current step
                step_label.setStyleSheet("""
                    background-color: #0078d4; 
                    color: white; 
                    padding: 5px 10px; 
                    border-radius: 3px;
                    font-weight: bold;
                """)
            else:
                step_label.setStyleSheet("""
                    color: #666; 
                    padding: 5px 10px;
                """)
            layout.addWidget(step_label)
            
        layout.addStretch()
        self.setLayout(layout)

class WizardStep1(QWidget):
    """Step 1: Basic Configuration"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Basic Configuration")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        
        form_group = QGroupBox("Essential Settings")
        form_layout = QFormLayout()
        
        self.techlib_combo = QComboBox()
        self.techlib_combo.addItems(["gf12lpp", "gf22fdx", "gf28hpk", "gf12lp", "gf14lpp"])
        form_layout.addRow("Technology Library:", self.techlib_combo)
        
        self.virtuoso_cmd_edit = QLineEdit()
        self.virtuoso_cmd_edit.setPlaceholderText("Enter Virtuoso command")
        form_layout.addRow("Virtuoso Command:", self.virtuoso_cmd_edit)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        form_layout.addRow("Log Level:", self.log_level_combo)
        
        form_group.setLayout(form_layout)
        
        layout.addWidget(title)
        layout.addWidget(form_group)
        layout.addStretch()
        
        self.setLayout(layout)

class WizardStep2(QWidget):
    """Step 2: QA Types Selection"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("QA Types & Settings")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        
        qa_group = QGroupBox("Select QA Types to Enable")
        qa_layout = QVBoxLayout()
        
        # QA Type checkboxes with descriptions
        self.cdf_cb = QCheckBox("CDF (Circuit Design Framework)")
        self.cdf_cb.setChecked(True)
        desc1 = QLabel("   • Validates circuit design and connectivity")
        desc1.setStyleSheet("color: #666; font-size: 11px;")
        
        self.drc_cb = QCheckBox("DRC (Design Rule Check)")
        desc2 = QLabel("   • Verifies layout design rules compliance")
        desc2.setStyleSheet("color: #666; font-size: 11px;")
        
        self.ta_cb = QCheckBox("TA (Timing Analysis)")
        desc3 = QLabel("   • Performs timing analysis validation")
        desc3.setStyleSheet("color: #666; font-size: 11px;")
        
        qa_layout.addWidget(self.cdf_cb)
        qa_layout.addWidget(desc1)
        qa_layout.addWidget(self.drc_cb)
        qa_layout.addWidget(desc2)
        qa_layout.addWidget(self.ta_cb)
        qa_layout.addWidget(desc3)
        
        qa_group.setLayout(qa_layout)
        
        # DRC specific settings (conditionally shown)
        self.drc_group = QGroupBox("DRC Specific Settings")
        drc_layout = QFormLayout()
        
        self.proj_mpv_edit = QLineEdit()
        drc_layout.addRow("Project MPV:", self.proj_mpv_edit)
        
        self.runcalx_edit = QLineEdit()
        drc_layout.addRow("Runcalx Version:", self.runcalx_edit)
        
        self.drc_group.setLayout(drc_layout)
        self.drc_group.setEnabled(False)
        
        # Connect DRC checkbox
        self.drc_cb.toggled.connect(self.drc_group.setEnabled)
        
        layout.addWidget(title)
        layout.addWidget(qa_group)
        layout.addWidget(self.drc_group)
        layout.addStretch()
        
        self.setLayout(layout)

class WizardStep3(QWidget):
    """Step 3: File Paths Configuration"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("File Paths & Configuration")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        
        paths_group = QGroupBox("Required File Paths")
        paths_layout = QFormLayout()
        
        # QA Settings file
        qa_layout = QHBoxLayout()
        self.qa_setting_edit = QLineEdit()
        self.qa_setting_edit.setPlaceholderText("Path to QA setting file")
        browse_qa_btn = QPushButton("Browse")
        qa_layout.addWidget(self.qa_setting_edit)
        qa_layout.addWidget(browse_qa_btn)
        paths_layout.addRow("QA Settings:", qa_layout)
        
        # CDS lib
        cds_layout = QHBoxLayout()
        self.cds_lib_edit = QLineEdit()
        self.cds_lib_edit.setPlaceholderText("Path to cds.lib file")
        browse_cds_btn = QPushButton("Browse")
        cds_layout.addWidget(self.cds_lib_edit)
        cds_layout.addWidget(browse_cds_btn)
        paths_layout.addRow("cds.lib:", cds_layout)
        
        # cdsinit
        cdsinit_layout = QHBoxLayout()
        self.cdsinit_edit = QLineEdit()
        self.cdsinit_edit.setPlaceholderText("Path to cdsinit file")
        browse_cdsinit_btn = QPushButton("Browse")
        cdsinit_layout.addWidget(self.cdsinit_edit)
        cdsinit_layout.addWidget(browse_cdsinit_btn)
        paths_layout.addRow(".cdsinit:", cdsinit_layout)
        
        paths_group.setLayout(paths_layout)
        
        # Run Directory
        run_group = QGroupBox("Output Configuration")
        run_layout = QFormLayout()
        
        self.run_dir_edit = QLineEdit("./output_qa")
        run_layout.addRow("Run Directory:", self.run_dir_edit)
        
        options_layout = QHBoxLayout()
        self.cleanup_cb = QCheckBox("Cleanup Output")
        self.save_express_cb = QCheckBox("Save .expressPCell")
        self.save_express_cb.setChecked(True)
        options_layout.addWidget(self.cleanup_cb)
        options_layout.addWidget(self.save_express_cb)
        run_layout.addRow("Options:", options_layout)
        
        run_group.setLayout(run_layout)
        
        layout.addWidget(title)
        layout.addWidget(paths_group)
        layout.addWidget(run_group)
        layout.addStretch()
        
        self.setLayout(layout)

class WizardStep4(QWidget):
    """Step 4: Action Selection"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Choose Action")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        
        action_group = QGroupBox("What would you like to do?")
        action_layout = QVBoxLayout()
        
        # Action cards
        create_card = self.create_action_card(
            "📦 Create Package", 
            "Create a new QA package with current settings",
            ["Verify configuration", "Generate package structure", "Run QA tests"]
        )
        
        compare_card = self.create_action_card(
            "🔍 Compare Packages",
            "Compare two package versions",
            ["Load golden package", "Load alpha package", "Generate comparison report"]
        )
        
        action_layout.addWidget(create_card)
        action_layout.addWidget(compare_card)
        action_group.setLayout(action_layout)
        
        layout.addWidget(title)
        layout.addWidget(action_group)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def create_action_card(self, title, description, features):
        """Create an action card widget"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet("""
            QFrame {
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                background-color: #f9f9f9;
            }
            QFrame:hover {
                border-color: #0078d4;
                background-color: #f0f8ff;
            }
        """)
        
        card_layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        
        for feature in features:
            feature_label = QLabel(f"• {feature}")
            feature_label.setStyleSheet("color: #333; font-size: 11px;")
            card_layout.addWidget(feature_label)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        select_btn = QPushButton("Select")
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        button_layout.addWidget(select_btn)
        
        card_layout.addWidget(title_label)
        card_layout.addWidget(desc_label)
        card_layout.addLayout(button_layout)
        
        card.setLayout(card_layout)
        return card

class WizardProgressWidget(QWidget):
    """Progress indicator for wizard"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(4)
        self.progress_bar.setValue(1)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Step %v of %m")
        
        layout.addWidget(QLabel("Progress:"))
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        
    def update_progress(self, step):
        self.progress_bar.setValue(step)

class MainLayoutIdea2(QWidget):
    """Main wizard-style layout"""
    def __init__(self):
        super().__init__()
        self.current_step = 1
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header with breadcrumb
        header_layout = QVBoxLayout()
        
        main_title = QLabel("QA MRVL Tool Configuration Wizard")
        main_title.setFont(QFont("Arial", 16, QFont.Bold))
        main_title.setAlignment(Qt.AlignCenter)
        
        self.breadcrumb = BreadcrumbWidget()
        self.progress = WizardProgressWidget()
        
        header_layout.addWidget(main_title)
        header_layout.addWidget(self.breadcrumb)
        header_layout.addWidget(self.progress)
        
        # Content stack
        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(WizardStep1())  # 0
        self.content_stack.addWidget(WizardStep2())  # 1
        self.content_stack.addWidget(WizardStep3())  # 2
        self.content_stack.addWidget(WizardStep4())  # 3
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("← Previous")
        self.next_btn = QPushButton("Next →")
        self.finish_btn = QPushButton("Finish")
        
        self.prev_btn.setEnabled(False)
        self.finish_btn.setVisible(False)
        
        self.prev_btn.clicked.connect(self.prev_step)
        self.next_btn.clicked.connect(self.next_step)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.finish_btn)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.content_stack)
        layout.addLayout(nav_layout)
        
        self.setLayout(layout)
        
    def prev_step(self):
        if self.current_step > 1:
            self.current_step -= 1
            self.update_step()
            
    def next_step(self):
        if self.current_step < 4:
            self.current_step += 1
            self.update_step()
            
    def update_step(self):
        self.content_stack.setCurrentIndex(self.current_step - 1)
        self.progress.update_progress(self.current_step)
        
        self.prev_btn.setEnabled(self.current_step > 1)
        self.next_btn.setVisible(self.current_step < 4)
        self.finish_btn.setVisible(self.current_step == 4)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setCentralWidget(MainLayoutIdea2())
    window.setWindowTitle("Layout Idea 2: Wizard-Style Progressive Layout")
    window.setGeometry(100, 100, 900, 700)
    window.show()
    sys.exit(app.exec_())
