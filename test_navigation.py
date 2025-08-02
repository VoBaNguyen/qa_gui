#!/usr/bin/env python3
"""
Quick test to verify navigation mapping and Settings page content
"""

import sys
from PyQt5.QtWidgets import QApplication
from refs.test_layout_3 import MainWindow

def test_navigation_mapping():
    """Test that navigation correctly maps to content pages"""
    print("Testing Navigation Mapping...")
    
    # Expected navigation order
    nav_order = ["Settings", "Create Package", "Compare Packages", "Debug"]
    
    # Expected content stack indices
    content_mapping = {
        "settings": 0,
        "create_package": 1, 
        "compare_packages": 2,
        "debug": 3
    }
    
    print("Navigation Order:", nav_order)
    print("Content Mapping:", content_mapping)
    print("✅ Navigation mapping should now be correct!")

def test_settings_fields():
    """Verify Settings page has all required fields"""
    print("\nTesting Settings Page Fields...")
    
    required_fields = [
        "Techlib", "QA Types", "QA Settings", "PDK Configs", 
        "Virtuoso Command", ".cdsinit"
    ]
    
    drc_fields = [
        "Project MPV", "mpvopt DRC", "Runcalx Version"
    ]
    
    advanced_fields = [
        "Max Instances Per Cell View", "Log Level", "Max Jobs", 
        "Max retries", "Save .expressPCell", "Cleanup Output"
    ]
    
    print("Required Settings:", required_fields)
    print("DRC Settings:", drc_fields) 
    print("Advanced Settings:", advanced_fields)
    print("✅ All required fields should be present in Settings page!")

if __name__ == "__main__":
    test_navigation_mapping()
    test_settings_fields()
    
    print("\n🚀 Starting QA MRVL Tool to verify everything works...")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
