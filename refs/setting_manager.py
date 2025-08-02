"""
Module for managing settings in QA MRVL Techlib Tool.
Provides functions to save and load settings to/from JSON files.
"""

import os
import json
import logging
import traceback
from typing import Tuple
import sys

# Add source code to PYTHONPATH
QA_MRVL_TECH = os.getenv("QA_MRVL_TECH", os.getcwd())
if QA_MRVL_TECH and f"{QA_MRVL_TECH}" not in sys.path:
    sys.path.append(f"{QA_MRVL_TECH}")

from config import SUPPORTED_TECHLIBS


logger = logging.getLogger(__name__)

class SettingsManager:
    """
    Manager for saving and loading settings for QA MRVL Techlib Tool.
    """
    @staticmethod
    def save_settings(window: object, file_name: str) -> Tuple[bool, str]:
        """
        Save current settings to a JSON file.

        Args:
            window (object): Main window object containing tabs.
            file_name (str): Path to the JSON file to save.

        Returns:
            Tuple[bool, str]: Success status and message.
        """
        settings = {
            'create_package_settings': window.tab_create_package.get_settings(),
            'compare_settings': {
                'golden': window.tab_compare.get_settings()['golden'],
                'alpha': window.tab_compare.get_settings()['alpha'],
                'qa_settings': window.tab_compare.get_settings()['qa_settings']
            }
        }
        try:
            with open(file_name, 'w') as f:
                json.dump(settings, f, indent=4)
            logger.info(f"Settings saved to {file_name}")
            return True, "Settings saved successfully"
        except Exception as e:
            message = f"Failed to save settings: {str(e)}. Traceback: {traceback.format_exc()}"
            logger.error(message)
            return False, message

    @staticmethod
    def load_settings(window: object, file_name: str) -> Tuple[bool, str]:
        """
        Load settings from a JSON file.

        Args:
            window (object): Main window object containing tabs.
            file_name (str): Path to the JSON file to load.

        Returns:
            Tuple[bool, str]: Success status and message.
        """
        try:
            if not os.path.isfile(file_name):
                logger.error(f"Settings file not found: {file_name}")
                return False, f"Settings file not found: {file_name}"
            with open(file_name, 'r') as f:
                settings = json.load(f)
            
            # Load create package settings
            create_package_settings = settings.get('create_package_settings', {})
            if not create_package_settings:
                logger.warning("No create_package_settings found in JSON")
            
            # Validate required fields
            required_settings = create_package_settings.get('required_settings', {})
            if 'techlib' in required_settings:
                tech_combo = window.tab_create_package.widgets['tech_combo']
                valid_techs = [tech_combo.itemText(i) for i in range(tech_combo.count())]
                if required_settings['techlib'] not in valid_techs:
                    logger.warning(f"Invalid techlib value: {required_settings['techlib']}. Defaulting to {SUPPORTED_TECHLIBS[0]}")
                    required_settings['techlib'] = SUPPORTED_TECHLIBS[0]
            window.tab_create_package.set_settings(create_package_settings)
            
            # Load compare settings
            compare_settings = settings.get('compare_settings', {})
            window.tab_compare.set_settings({
                'golden': compare_settings.get('golden', {}),
                'alpha': compare_settings.get('alpha', {}),
                'qa_settings': compare_settings.get('qa_settings', {})
            })
            
            # Resolve paths after loading
            window.resolve_paths()
            
            logger.info(f"Settings loaded successfully from {file_name}")
            return True, "Settings loaded successfully"
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in {file_name}: {str(e)}")
            return False, f"Failed to load settings: Invalid JSON format: {str(e)}"
        except Exception as e:
            message = f"Failed to load settings from {file_name}: {str(e)}. Traceback: {traceback.format_exc()}"
            logger.error(message)
            return False, message
