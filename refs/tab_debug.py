"""
Module for job status monitoring and debug tab in QA MRVL Techlib Tool.
Provides widgets and workers for displaying and updating job status from the database.
"""

import sys
import os
import json
import logging
import threading
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QTextEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QDialog, QDesktopWidget, QSizePolicy, QHeaderView,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QFileDialog, QFormLayout, QSplitter
)
from PyQt5.QtCore import QFileSystemWatcher, QTimer, Qt, QThread, pyqtSignal, QObject, pyqtSlot
from PyQt5.QtGui import QFont
from utils import file_utils as utils, enum

# Temporary enum for STEPS (replace with your actual enum.FE.STEPS)
CREATE_STEPS = enum.FE.CREATE_STEPS
XOR_STEPS = enum.FE.XOR_STEPS

logger = logging.getLogger(__name__)
file_lock = threading.Lock()

# Worker class for fetching job status
class JobStatusWorker(QObject):
    """
    Worker for fetching job status from the database and emitting jobs_ready signal.
    """
    jobs_ready = pyqtSignal(list)

    def __init__(self, db_path: str, parent: QObject = None) -> None:
        """
        Initialize the JobStatusWorker.

        Args:
            db_path (str): Path to the SQLite database file.
            parent (QObject, optional): Parent QObject.
        """
        super().__init__(parent)
        self.db_path = db_path
        self._is_running = True

    def stop(self) -> None:
        """Stop the worker thread."""
        self._is_running = False

    def run(self) -> None:
        """
        Periodically fetch job status from the database and emit jobs_ready signal.
        Uses only standard Python (sqlite3), no Qt objects.
        """
        import time
        import sqlite3
        while self._is_running:
            jobs = []
            try:
                if self.db_path and os.path.exists(self.db_path):
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM jobs')
                    columns = [desc[0] for desc in cursor.description]
                    for row in cursor.fetchall():
                        jobs.append(dict(zip(columns, row)))
                    conn.close()
            except Exception as exc:
                logger.error(f"Error fetching jobs from database: {exc}")
            self.jobs_ready.emit(jobs)
            time.sleep(2)

# StatusMonitor class (updated to handle db_path=None internally)
class StatusMonitor(QWidget):
    """
    Widget to monitor and display job status from the jobs table in the database.
    Shows an empty table with jobs columns if db_path is None or invalid.
    start_time and end_time are formatted as '%Y-%m-%d %H:%M:%S'.
    """
    JOBS_COLUMNS = [
        "id", "mode", "base", "cell", "step", "start_time", "end_time", "duration",
        "log_path", "script_path", "status", "reason"
    ]

    def __init__(self, db_path: str = None) -> None:
        """
        Initialize the StatusMonitor widget.

        Parameters
        ----------
        db_path : str, optional
            Path to the SQLite database file. If None, table is empty.
        """
        super().__init__()
        self.db_path: str | None = db_path
        self.worker_thread: QThread | None = None
        self.worker: QObject | None = None
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.table: QTableWidget | None = None
        self.placeholder: QLabel | None = None
        logger.debug(f"[StatusMonitor] __init__ with db_path={db_path}")
        self.init_ui()

    def init_ui(self) -> None:
        """
        Initialize the UI for the status monitor. Always shows a table with jobs columns if db_path is valid, otherwise a placeholder.
        """
        logger.debug(f"[StatusMonitor] init_ui called. db_path={self.db_path}")
        # Remove all widgets from layout
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.table = None
        self.placeholder = None
        if not self.db_path:
            # Show placeholder label if db_path is None
            self.placeholder = QLabel("No database selected. Table is empty.")
            self.placeholder.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(self.placeholder)
            return
        # Always show the table with jobs columns
        self.table = QTableWidget(0, len(self.JOBS_COLUMNS))
        self.table.setHorizontalHeaderLabels([col.replace('_', ' ').title() for col in self.JOBS_COLUMNS])
        self.table.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.table.setFont(QFont("Arial", 10))
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setMinimumSectionSize(50)
        for i in range(len(self.JOBS_COLUMNS)):
            self.table.setColumnWidth(i, 110)
        header.setStretchLastSection(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.layout.addWidget(self.table)

    def setup_monitoring(self) -> None:
        """
        Set up periodic monitoring using a worker thread if db_path is valid.
        """
        logger.debug(f"[StatusMonitor] setup_monitoring called. db_path={self.db_path}")
        self._stop_worker()
        if not self.db_path or not os.path.exists(self.db_path):
            logger.info("[StatusMonitor] Monitoring not started: invalid db_path.")
            return
        self.worker_thread = QThread(self)
        self.worker = JobStatusWorker(self.db_path)
        self.worker.moveToThread(self.worker_thread)
        self.worker.jobs_ready.connect(self.on_jobs_ready, type=Qt.QueuedConnection)
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()
        logger.info("[StatusMonitor] Monitoring started in worker thread.")

    def _stop_worker(self) -> None:
        """
        Stop and clean up the worker thread if running.
        """
        if hasattr(self, 'worker') and self.worker:
            self.worker.stop()
        if hasattr(self, 'worker_thread') and self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
        self.worker = None
        self.worker_thread = None

    @pyqtSlot(list)
    def on_jobs_ready(self, jobs: list) -> None:
        """
        Slot to update the job status table from the worker thread signal.
        """
        self._update_table_with_jobs(jobs)
        # logger.debug("[StatusMonitor] Job status table refreshed.")

    def update_table(self) -> None:
        """
        Synchronously update the job status table from the database. Used for testing or direct calls.
        """
        jobs = []
        if self.db_path and os.path.exists(self.db_path):
            try:
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM jobs')
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    jobs.append(dict(zip(columns, row)))
                conn.close()
            except Exception:
                pass
        self._update_table_with_jobs(jobs)

    def _update_table_with_jobs(self, jobs: list) -> None:
        """
        Update the table widget by appending new jobs or replacing existing ones by job ID.
        Existing jobs in the table are preserved in their order unless replaced.

        Parameters
        ----------
        jobs : list
            List of job dictionaries to display in the table.
        """
        if not self.table:
            return
        # Collect existing job IDs and their row indices from the table
        existing_id_to_row = {}
        id_col_idx = self.JOBS_COLUMNS.index("id")
        for row in range(self.table.rowCount()):
            item = self.table.item(row, id_col_idx)
            if item is not None:
                existing_id_to_row[item.text()] = row
        # Update or append jobs
        for job in jobs:
            job_id = str(job.get("id", ""))
            if job_id in existing_id_to_row:
                row_idx = existing_id_to_row[job_id]
                # Update all columns in the existing row
                for col_idx, col in enumerate(self.JOBS_COLUMNS):
                    if col == "log_path":
                        log_path = job.get("log_path", None)
                        btn = QPushButton("View")
                        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                        if log_path and os.path.exists(log_path):
                            btn.clicked.connect(lambda _, path=log_path: self.open_log(path))
                        else:
                            btn.setEnabled(False)
                        self.table.setCellWidget(row_idx, col_idx, btn)
                    else:
                        value = job[col] if col in job.keys() else None
                        item = QTableWidgetItem(str(value) if value is not None else "")
                        item.setData(Qt.DisplayRole, value)
                        item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row_idx, col_idx, item)
            else:
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)
                for col_idx, col in enumerate(self.JOBS_COLUMNS):
                    if col == "log_path":
                        log_path = job.get("log_path", None)
                        btn = QPushButton("View")
                        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                        if log_path and os.path.exists(log_path):
                            btn.clicked.connect(lambda _, path=log_path: self.open_log(path))
                        else:
                            btn.setEnabled(False)
                        self.table.setCellWidget(row_idx, col_idx, btn)
                    else:
                        value = job[col] if col in job.keys() else None
                        item = QTableWidgetItem(str(value) if value is not None else "")
                        item.setData(Qt.DisplayRole, value)
                        item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row_idx, col_idx, item)
        # Hide the 'Id' column
        self.table.setColumnHidden(id_col_idx, True)

    def showEvent(self, event) -> None:
        logger.info("[StatusMonitor] showEvent called. Widget is now visible.")
        self.setup_monitoring()  # Start timer only when widget is shown
        super().showEvent(event)

    def open_log(self, path: str) -> None:
        """
        Open a dialog to display the contents of a log file.

        Parameters
        ----------
        path : str
            Path to the log file.
        """
        logger.debug(f"[StatusMonitor] open_log called for path: {path}")
        if not os.path.exists(path):
            logger.warning(f"[StatusMonitor] Log file does not exist: {path}")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Log: {os.path.basename(path)}")
        te = QTextEdit()
        te.setReadOnly(True)
        content = None
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError as e:
            logger.warning(f"[StatusMonitor] UTF-8 decode error for log file {path}: {e}. Trying latin-1.")
            try:
                with open(path, encoding="latin-1") as f:
                    content = f.read()
            except Exception as e2:
                logger.error(f"[StatusMonitor] Could not decode log file {path} as latin-1: {e2}")
                try:
                    with open(path, "rb") as f:
                        content = f.read().decode("utf-8", errors="replace")
                except Exception as e3:
                    logger.error(f"[StatusMonitor] Could not read log file {path} as binary: {e3}", exc_info=True)
                    content = f"Error: Could not decode log file.\nUTF-8 error: {e}\nlatin-1 error: {e2}\nBinary error: {e3}"
        except Exception as e:
            logger.error(f"[StatusMonitor] Error opening log file {path}: {e}", exc_info=True)
            content = f"Error: Could not open log file.\n{e}"
        if content is not None:
            te.setPlainText(content)
        layout = QVBoxLayout(dlg)
        layout.addWidget(te)
        dlg.resize(1200, 600)
        dlg.exec_()

    def closeEvent(self, event) -> None:
        logger.info("[StatusMonitor] closeEvent called. Stopping worker if active.")
        self._stop_worker()
        super().closeEvent(event)

    def update_db_path(self, db_path: str) -> None:
        """
        Update the db_path and refresh the UI accordingly.

        Parameters
        ----------
        db_path : str
            Path to the new database file.
        """
        logger.info(f"[StatusMonitor] update_db_path called. New db_path={db_path}")
        self.db_path = db_path
        self.init_ui()
        self.setup_monitoring()

# SummaryTab class (unchanged)
class SummaryTab(QWidget):
    def __init__(self, status_dir_getter=None):
        super().__init__()
        self.status_dir_getter = status_dir_getter
        self.widgets = {}  # Store widgets for paths
        self.is_running = False
        self.db_path = None
        self.init_ui()
        self.summary_timer = QTimer(self)
        self.summary_timer.timeout.connect(self.update_summary_from_db)
        self.summary_timer.start(10000)  # 10 seconds

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Job: New Package
        new_package_group = QGroupBox("New Package")
        new_package_layout = QVBoxLayout()

        # Test cases table
        self.new_package_table = QTableWidget()
        self.new_package_table.setRowCount(3)
        self.new_package_table.setColumnCount(5)
        self.new_package_table.setHorizontalHeaderLabels(["Test Case", "RUNNING", "PASS", "FAILED", "ERROR"])
        self.new_package_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.new_package_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        self.new_package_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.new_package_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        new_package_layout.addWidget(self.new_package_table)

        new_package_group.setLayout(new_package_layout)
        main_layout.addWidget(new_package_group)

        # Job: Compare Packages
        compare_packages_group = QGroupBox("Compare Packages")
        compare_packages_layout = QHBoxLayout()

        # Golden Package
        golden_group = QGroupBox("Golden Package")
        golden_layout = QVBoxLayout()
        self.golden_table = QTableWidget()
        self.golden_table.setRowCount(4)
        self.golden_table.setColumnCount(5)
        self.golden_table.setHorizontalHeaderLabels(["Test Case", "RUNNING", "PASS", "FAILED", "ERROR"])
        self.golden_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.golden_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        self.golden_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.golden_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        golden_layout.addWidget(self.golden_table)
        golden_group.setLayout(golden_layout)
        compare_packages_layout.addWidget(golden_group)

        # Alpha Package
        alpha_group = QGroupBox("Alpha Package")
        alpha_layout = QVBoxLayout()
        self.alpha_table = QTableWidget()
        self.alpha_table.setRowCount(4)
        self.alpha_table.setColumnCount(5)
        self.alpha_table.setHorizontalHeaderLabels(["Test Case", "RUNNING", "PASS", "FAILED", "ERROR"])
        self.alpha_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.alpha_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        self.alpha_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.alpha_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        alpha_layout.addWidget(self.alpha_table)
        alpha_group.setLayout(alpha_layout)
        compare_packages_layout.addWidget(alpha_group)

        # Comparison Result
        comparison_group = QGroupBox("Comparison Result")
        comparison_layout = QVBoxLayout()
        self.comparison_table = QTableWidget()
        self.comparison_table.setRowCount(3)
        self.comparison_table.setColumnCount(5)
        self.comparison_table.setHorizontalHeaderLabels(["Test Case", "RUNNING", "PASS", "FAILED", "ERROR"])
        self.comparison_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.comparison_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        self.comparison_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.comparison_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        comparison_layout.addWidget(self.comparison_table)
        comparison_group.setLayout(comparison_layout)
        compare_packages_layout.addWidget(comparison_group)

        compare_packages_group.setLayout(compare_packages_layout)
        main_layout.addWidget(compare_packages_group)

        # View Reports and Alpha DRC Group
        reports_and_drc_group = QGroupBox("View Reports and DRC")
        reports_and_drc_layout = QFormLayout()


        # View Reports
        report_fields = [
            ("New DRC Failed Rules:", enum.SUMMARY.NEW_DRC_FAILED_RULES, ""),
            ("Alpha DRC Failed Rules:", enum.SUMMARY.ALPHA_DRC_FAILED_RULES, ""),
            ("CDF Mismatches:", enum.SUMMARY.CDF_MISMATCH_ASC, ""),
            ("TA Mismatches:", enum.SUMMARY.TA_MISMATCH_ASC, ""),
            ("DRC Report HTML:", enum.SUMMARY.DRC_REPORT_HTML, ""),
        ]

        for label_text, field_key, _ in report_fields:
            self.widgets[field_key] = QLineEdit("")
            self.widgets[field_key].setPlaceholderText(f"Enter {field_key.replace('_', ' ').title()} path")
            self.widgets[field_key].setObjectName(field_key)
            self.widgets[field_key].setReadOnly(True)

            report_row = QHBoxLayout()
            report_row.addWidget(self.widgets[field_key])
            report_row.addWidget(self.add_open_button(field_key, self.widgets[field_key]))

            reports_and_drc_layout.addRow(label_text, report_row)

        reports_and_drc_group.setLayout(reports_and_drc_layout)
        main_layout.addWidget(reports_and_drc_group)

        main_layout.addStretch()
        self.setLayout(main_layout)

        # Initial data load from DB only
        self.update_summary_from_db()

    def setup_monitoring(self):
        # No monitoring setup, only DB update
        pass

    def update_summary_from_db(self) -> None:
        """
        Query the jobs table in the database and update the summary tables with counts.
        Also refresh View Reports widgets with latest file paths from the files table.
        - 'new', 'golden', 'alpha' modes use CREATE_STEPS.
        - 'comparison' mode uses XOR_STEPS for the Comparison Result table.
        Always show all steps with default stats 0.
        """
        import sqlite3
        conn = None
        try:
            if not self.db_path or not os.path.exists(self.db_path):
                return
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Update summary tables from jobs table
            cursor.execute('SELECT step, status, mode FROM jobs')
            rows = cursor.fetchall()
            # Get all possible steps
            create_steps = [str(step) for step in CREATE_STEPS]
            xor_steps = [str(step) for step in XOR_STEPS]
            # Initialize summary dicts
            summary_by_mode = {
                'new': {step: {'RUNNING': 0, 'PASS': 0, 'FAILED': 0, 'ERROR': 0} for step in create_steps},
                'golden': {step: {'RUNNING': 0, 'PASS': 0, 'FAILED': 0, 'ERROR': 0} for step in create_steps},
                'alpha': {step: {'RUNNING': 0, 'PASS': 0, 'FAILED': 0, 'ERROR': 0} for step in create_steps},
                'compare': {step: {'RUNNING': 0, 'PASS': 0, 'FAILED': 0, 'ERROR': 0} for step in xor_steps},
            }
            for step, status, mode in rows:
                if mode in summary_by_mode and step in summary_by_mode[mode]:
                    if status in summary_by_mode[mode][step]:
                        summary_by_mode[mode][step][status] += 1
            # Update CREATE_STEPS tables
            for table, mode in [
                (self.new_package_table, 'new'),
                (self.golden_table, 'golden'),
                (self.alpha_table, 'alpha'),
            ]:
                step_counts = summary_by_mode[mode]
                table.setRowCount(len(create_steps))
                for row_idx, step in enumerate(create_steps):
                    counts = step_counts[step]
                    table.setItem(row_idx, 0, QTableWidgetItem(str(step)))
                    table.setItem(row_idx, 1, QTableWidgetItem(str(counts.get('RUNNING', 0))))
                    table.setItem(row_idx, 2, QTableWidgetItem(str(counts.get('PASS', 0))))
                    table.setItem(row_idx, 3, QTableWidgetItem(str(counts.get('FAILED', 0))))
                    table.setItem(row_idx, 4, QTableWidgetItem(str(counts.get('ERROR', 0))))
                table.resizeColumnsToContents()
                table.setFixedSize(table.sizeHint())
            # Update XOR_STEPS table for Comparison Result
            step_counts = summary_by_mode['compare']
            self.comparison_table.setRowCount(len(xor_steps))
            for row_idx, step in enumerate(xor_steps):
                counts = step_counts[step]
                self.comparison_table.setItem(row_idx, 0, QTableWidgetItem(str(step)))
                self.comparison_table.setItem(row_idx, 1, QTableWidgetItem(str(counts.get('RUNNING', 0))))
                self.comparison_table.setItem(row_idx, 2, QTableWidgetItem(str(counts.get('PASS', 0))))
                self.comparison_table.setItem(row_idx, 3, QTableWidgetItem(str(counts.get('FAILED', 0))))
                self.comparison_table.setItem(row_idx, 4, QTableWidgetItem(str(counts.get('ERROR', 0))))
            self.comparison_table.resizeColumnsToContents()
            self.comparison_table.setFixedSize(self.comparison_table.sizeHint())

            # --- Update View Reports widgets from files table ---
            # For each field_key in self.widgets, query files table for latest file_path
            for field_key in enum.SUMMARY.REPORT_FILEDS:
                widget = self.widgets.get(field_key)
                try:
                    cursor.execute('SELECT file_path FROM files WHERE file_type = ? ORDER BY created_at DESC LIMIT 1', (field_key,))
                    result = cursor.fetchone()
                    if result and result[0]:
                        widget.setText(result[0])
                    else:
                        widget.setText("")
                except Exception as e:
                    logger.warning(f"Could not update report field {field_key}: {e}")
        except Exception as e:
            logger.error(f"Error updating summary from jobs/files table: {e}", exc_info=True)
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Summary Error", f"Error updating summary from jobs/files table:\n{e}")
            if hasattr(self.parent(), "update_log"):
                self.parent().update_log(f"Error updating summary from jobs/files table: {e}", "debug_log")
        finally:
            if conn:
                conn.close()

    def closeEvent(self, event):
        if hasattr(self, 'summary_timer') and self.summary_timer:
            self.summary_timer.stop()
            self.summary_timer.deleteLater()
        super().closeEvent(event)

    def add_open_button(self, field_key, line_edit):
        """
        Create and return a QPushButton that opens the file specified in the line_edit.
        Parameters
        ----------
        field_key : str
            The key for the field (used to determine open behavior).
        line_edit : QLineEdit
            The line edit widget containing the file path.
        Returns
        -------
        QPushButton
            The button configured to open the file.
        """
        button = QPushButton("Open")
        button.clicked.connect(lambda: utils.open_file(line_edit.text(), logger=logger))
        return button

    def update_db_path(self, db_path: str) -> None:
        """
        Update the database path and refresh the summary tables.

        Parameters
        ----------
        db_path : str
            Path to the new database file.
        """
        self.db_path = db_path
        self.update_summary_from_db()

# DebugTab class (updated to simplify set_db_path)
class ResultTab(QWidget):
    """
    Tab for displaying master-detail reports table.
    """
    def __init__(self, parent=None, db_path: str = None):
        super().__init__(parent)
        self.setWindowTitle("Reports")
        self.resize(800, 600)
        self.main_table = QTableWidget()
        self.detail_table = QTableWidget()
        self.detail_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.refresh_btn = QPushButton("Refresh")  # Add Refresh button
        self.refresh_btn.setToolTip("Reload data and refresh tables")
        self.refresh_btn.clicked.connect(self._populate_main_table)
        self.db_path = db_path  # Ensure db_path is set before setup_ui
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        # Add Refresh button below label
        layout.addWidget(self.refresh_btn, alignment=Qt.AlignLeft)
        # Add label for main table
        main_label = QLabel("Summary Report")
        main_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(main_label, alignment=Qt.AlignTop)
        # Top table in its own widget for sizing
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setAlignment(Qt.AlignTop)
        top_layout.addWidget(self.main_table, alignment=Qt.AlignTop)
        layout.addWidget(top_widget, alignment=Qt.AlignTop)
        # Stretch main_table horizontally but allow resizing
        self.main_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.main_table.setSortingEnabled(True)  # Enable sorting for main_table
        # Add label for detail table
        detail_label = QLabel("Detail Report")
        detail_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(detail_label, alignment=Qt.AlignTop)
        layout.addWidget(self.detail_table)
        layout.setStretchFactor(self.detail_table, 1)
        # Stretch detail_table horizontally but allow resizing
        self.detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.detail_table.setSortingEnabled(True)  # Enable sorting for detail_table
        self._populate_main_table()
        self._populate_detail_table([])
        # Fit top table to contents
        self.main_table.resizeRowsToContents()
        self.main_table.resizeColumnsToContents()
        self.main_table.setFixedHeight(self.main_table.verticalHeader().length() + self.main_table.horizontalHeader().height() + 10)

    def update_db_path(self, db_path: str) -> None:
        """
        Update the database path and refresh the summary tables.
        """
        self.db_path = db_path
        self._populate_main_table()

    def _populate_main_table(self):
        """
        Query data from table report_dashboard and populate main_table.
        Columns: id, qa_type, total, pass, fail, file_asc, file_asc_cto
        """
        import sqlite3
        logger.info("[ResultTab] Refresh triggered: populating main table.")
        data = []
        self.db_path = "/mrvl2g/dc5prengvs04_s_cad_0033/techtsmc002p/techtsmc002p/wa/nguyenv/techtsmc002p/git/demo_qa/samples/output_compare_tsmcN2_mrvl/.cache.db"
        if not self.db_path:
            logger.warning("[ResultTab] db_path is not set. Table will be empty.")
        elif not os.path.exists(self.db_path):
            logger.warning(f"[ResultTab] db_path '{self.db_path}' does not exist. Table will be empty.")
        else:
            try:
                logger.info(f"[ResultTab] Connecting to database: {self.db_path}")
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT id, qa_type, total, pass, fail, file_asc, file_asc_cto FROM report_dashboard')
                rows = cursor.fetchall()
                logger.info(f"[ResultTab] Retrieved {len(rows)} rows from report_dashboard.")
                for row in rows:
                    id_, qa_type, total, passed, failed, file_asc, file_asc_cto = row
                    data.append({
                        "id": str(id_),
                        "qa_type": str(qa_type),
                        "total": str(total),
                        "pass": str(passed),
                        "fail": str(failed),
                        "file_asc": str(file_asc) if file_asc else "",
                        "file_asc_cto": str(file_asc_cto) if file_asc_cto else ""
                    })
                conn.close()
            except Exception as e:
                logger.error(f"[ResultTab] Error querying report_dashboard: {e}")
        self._data = data
        # Remove 'id' column from headers
        main_header = ["qa_type", "total", "pass", "fail", "file_asc", "file_asc_cto", "Detail"]
        beautified_header = [h.replace('_', ' ').title() for h in main_header]
        self.main_table.setRowCount(len(data))
        self.main_table.setColumnCount(len(beautified_header))
        self.main_table.setHorizontalHeaderLabels(beautified_header)
        # Prevent row stretching: set fixed row height
        self.main_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        logger.info(f"[ResultTab] Populating table with {len(data)} rows.")
        for row_idx, item in enumerate(data):
            self.main_table.setItem(row_idx, 0, QTableWidgetItem(item["qa_type"]))
            self.main_table.setItem(row_idx, 1, QTableWidgetItem(item["total"]))
            self.main_table.setItem(row_idx, 2, QTableWidgetItem(item["pass"]))
            self.main_table.setItem(row_idx, 3, QTableWidgetItem(item["fail"]))
            # ASC File button or text
            asc_path = item["file_asc"]
            if asc_path and os.path.exists(asc_path):
                btn_asc = QPushButton("Copy Path")
                btn_asc.setToolTip(asc_path)
                btn_asc.clicked.connect(lambda _, path=asc_path: QApplication.clipboard().setText(path))
                self.main_table.setCellWidget(row_idx, 4, btn_asc)
            else:
                self.main_table.setItem(row_idx, 4, QTableWidgetItem(asc_path if asc_path else "N/A"))
            # CTO ASC File button or text
            cto_path = item["file_asc_cto"]
            if cto_path and os.path.exists(cto_path):
                btn_cto = QPushButton("Copy Path")
                btn_cto.setToolTip(cto_path)
                btn_cto.clicked.connect(lambda _, path=cto_path: QApplication.clipboard().setText(path))
                self.main_table.setCellWidget(row_idx, 5, btn_cto)
            else:
                self.main_table.setItem(row_idx, 5, QTableWidgetItem(cto_path if cto_path else "N/A"))
            # Detail button
            btn_detail = QPushButton("View Detail")
            btn_detail.setToolTip(f"View details for {item['qa_type']}")
            btn_detail.clicked.connect(self._make_detail_callback(item["id"], item["qa_type"]))
            self.main_table.setCellWidget(row_idx, 6, btn_detail)
        logger.info("[ResultTab] Table update complete.")

    def _populate_detail_table(self, detail_data):
        if not detail_data:
            self.detail_table.setRowCount(0)
            self.detail_table.setColumnCount(0)
            return
        header = detail_data[0]
        rows = detail_data[1:]
        # Remove 'id' column from header and rows if present
        if 'id' in header:
            id_idx = header.index('id')
            header = [h for h in header if h != 'id']
            rows = [[v for i, v in enumerate(row) if i != id_idx] for row in rows]
        # Beautify headers: replace underscores, title case
        beautified_header = [h.replace('_', ' ').title() for h in header]
        # Add 'Detail' column
        beautified_header.append('Detail')
        self.detail_table.setColumnCount(len(beautified_header))
        self.detail_table.setRowCount(len(rows))
        self.detail_table.setHorizontalHeaderLabels(beautified_header)
        for row_idx, row in enumerate(rows):
            for col_idx, value in enumerate(row):
                self.detail_table.setItem(row_idx, col_idx, QTableWidgetItem(value))
            # Add 'Open RVE' button in last column
            btn_rve = QPushButton('Open RVE')
            btn_rve.setToolTip('Open RVE for this row')
            btn_rve.clicked.connect(lambda _, r=row: self._on_open_rve(r))
            self.detail_table.setCellWidget(row_idx, len(beautified_header) - 1, btn_rve)

    def _on_open_rve(self, row_data):
        """
        Callback for 'Open RVE' button in detail table.
        You can implement the actual RVE opening logic here.
        """
        logger.info(f"[ResultTab] Open RVE clicked for row: {row_data}")
        # TODO: Implement RVE opening logic here
        # Example: show a message box
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Open RVE", f"Open RVE for row: {row_data}")

    def _on_row_click(self, row, column):
        item = self._data[row]
        self._populate_detail_table(item["details"])

    def closeEvent(self, event):
        super().closeEvent(event)

    def _make_detail_callback(self, id_, qa_type):
        def callback():
            import sqlite3
            detail_data = []
            table_map = {
                "CDF": "report_cdf",
                "TA": "report_ta",
                "DRC": "report_drc",
                "XOR": "report_xor"
            }
            table_name = table_map.get(qa_type.upper(), None)
            if not table_name:
                logger.warning(f"No detail table for qa_type: {qa_type}")
                self._populate_detail_table([])
                return
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                # For CDF and TA, show all rows (or filter by base/cell if you want)
                if table_name in ("report_cdf", "report_ta"):
                    cursor.execute(f'SELECT id, base, cell, status, message, file_asc, file_asc_cto FROM {table_name}')
                else:
                    # For DRC/XOR, fallback to all rows (customize if you have a relationship)
                    cursor.execute(f'SELECT * FROM {table_name}')
                rows = cursor.fetchall()
                header = [desc[0] for desc in cursor.description]
                detail_data = [header] + [list(map(str, row)) for row in rows]
                conn.close()
            except Exception as e:
                logger.error(f"Error querying {table_name} for detail: {e}")
                detail_data = []
            self._populate_detail_table(detail_data)
        return callback

# DebugTab class (updated to simplify set_db_path)
class DebugTab(QWidget):
    def __init__(self, parent=None, db_path: str = None):
        super().__init__(parent)
        self.db_path = db_path
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        self.debug_tabs = QTabWidget()
        self.debug_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.debug_log = QWidget()
        self.debug_log_layout = QVBoxLayout(self.debug_log)
        self.debug_log_layout.setContentsMargins(0, 0, 0, 0)
        self.debug_log_text = QTextEdit()
        self.debug_log_text.setReadOnly(True)
        self.debug_log_text.setFont(QFont("Courier New", 10))
        self.debug_log_layout.addWidget(self.debug_log_text)
        self.debug_tabs.addTab(self.debug_log, "Debug Log")
        # Job Status tab
        self.debug_status = StatusMonitor(db_path=self.db_path)
        self.debug_tabs.addTab(self.debug_status, "Job Status")
        self.summary_tab = SummaryTab()
        self.debug_tabs.addTab(self.summary_tab, "Summary")
        # Add Result tab
        self.result_tab = ResultTab()
        self.debug_tabs.addTab(self.result_tab, "Result")
        layout.addWidget(self.debug_tabs)
        self.setLayout(layout)

    def set_db_path(self, db_path: str):
        """
        Set a new db_path and reload the Job Status and Summary tabs in place.

        Parameters
        ----------
        db_path : str
            Path to the new database file.
        """
        self.db_path = db_path
        self.debug_status.update_db_path(db_path)
        self.summary_tab.update_db_path(db_path)
        self.result_tab.update_db_path(db_path)

    def update_log(self, log_text, tab_name):
        if tab_name == "debug_log":
            scrollbar = self.debug_log_text.verticalScrollBar()
            at_bottom = scrollbar.value() == scrollbar.maximum()
            self.debug_log_text.append(log_text)
            if at_bottom:
                scrollbar.setValue(scrollbar.maximum())
        elif tab_name == "debug_status":
            pass
        elif tab_name == "summary":
            pass

    def closeEvent(self, event):
        super().closeEvent(event)
