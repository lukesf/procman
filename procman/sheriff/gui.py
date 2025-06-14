from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel, QInputDialog,
    QFileDialog, QMessageBox, QGroupBox, QMenu
)
from PyQt5.QtCore import QTimer, Qt
from typing import Optional
import sys
from .sheriff import Sheriff
from ..common.process_info import ProcessInfo
from .process_dialog import ProcessDialog


class SheriffGUI(QMainWindow):
    """GUI interface for the Sheriff process manager."""
    
    def __init__(self):
        super().__init__()
        self.sheriff = Sheriff()
        self.current_config_file = None
        self.init_ui()
        self.start_update_timer()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('Sheriff Process Manager')
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create button toolbar
        toolbar = QHBoxLayout()
        
        # Add Deputy button
        add_deputy_btn = QPushButton('Add Deputy')
        add_deputy_btn.clicked.connect(self.add_deputy)
        toolbar.addWidget(add_deputy_btn)
        
        # Add Process button
        add_process_btn = QPushButton('Add Process')
        add_process_btn.clicked.connect(self.add_process)
        toolbar.addWidget(add_process_btn)
        
        # Load Config button
        load_config_btn = QPushButton('Load Config')
        load_config_btn.clicked.connect(self.load_config)
        toolbar.addWidget(load_config_btn)
        
        # Save Config button
        save_config_btn = QPushButton('Save Config')
        save_config_btn.clicked.connect(self.save_config)
        toolbar.addWidget(save_config_btn)
        
        # Add stretch to push buttons to the left
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Create Deputy status group
        deputy_group = QGroupBox("Deputy Status")
        deputy_layout = QVBoxLayout()
        
        # Create deputy table
        self.deputy_table = QTableWidget()
        self.deputy_table.setColumnCount(5)
        self.deputy_table.setHorizontalHeaderLabels([
            'Hostname', 'URL', 'Status', 'CPU %', 'Memory %'
        ])
        self.deputy_table.horizontalHeader().setStretchLastSection(True)
        deputy_layout.addWidget(self.deputy_table)
        
        deputy_group.setLayout(deputy_layout)
        layout.addWidget(deputy_group)
        
        # Create Process status group
        process_group = QGroupBox("Process Status")
        process_layout = QVBoxLayout()
        
        # Create process table
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(8)
        self.process_table.setHorizontalHeaderLabels([
            'Name', 'Host', 'Status', 'PID', 'CPU %', 'Memory %',
            'Uptime', 'Actions'
        ])
        self.process_table.horizontalHeader().setStretchLastSection(True)
        self.process_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.process_table.customContextMenuRequested.connect(self.show_process_context_menu)
        process_layout.addWidget(self.process_table)
        
        process_group.setLayout(process_layout)
        layout.addWidget(process_group)
        
        # Create status bar
        self.statusBar().showMessage('Ready')
    
    def start_update_timer(self):
        """Start timer to update process information."""
        self.sheriff.start_update_thread()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_tables)
        self.update_timer.start(1000)  # Update every second
    
    def add_deputy(self):
        """Add a new Deputy server."""
        url, ok = QInputDialog.getText(
            self, 'Add Deputy',
            'Enter Deputy URL (e.g., http://localhost:8000):'
        )
        if ok and url:
            if self.sheriff.add_deputy(url):
                self.statusBar().showMessage(f'Successfully added Deputy at {url}')
            else:
                QMessageBox.warning(
                    self, 'Error',
                    f'Failed to add Deputy at {url}'
                )
    
    def add_process(self):
        """Add a new process."""
        dialog = ProcessDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            process_info = dialog.get_process_info()
            if self.sheriff.start_process(process_info):
                self.statusBar().showMessage(f'Successfully added process {process_info.name}')
            else:
                QMessageBox.warning(
                    self, 'Error',
                    f'Failed to add process {process_info.name}'
                )
    
    def edit_process(self, name: str):
        """Edit an existing process."""
        process = self.sheriff.get_process_info(name)
        if not process:
            return
            
        dialog = ProcessDialog(process, parent=self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            # Update process
            new_info = dialog.get_process_info()
            # Stop the old process
            self.sheriff.stop_process(name)
            # Start with new settings
            if self.sheriff.start_process(new_info):
                self.statusBar().showMessage(f'Successfully updated process {name}')
            else:
                QMessageBox.warning(
                    self, 'Error',
                    f'Failed to update process {name}'
                )
        elif result == 2:  # Delete
            if self.sheriff.delete_process(name):
                self.statusBar().showMessage(f'Successfully deleted process {name}')
            else:
                QMessageBox.warning(
                    self, 'Error',
                    f'Failed to delete process {name}'
                )
    
    def show_process_context_menu(self, pos):
        """Show context menu for process table."""
        row = self.process_table.rowAt(pos.y())
        if row >= 0:
            name = self.process_table.item(row, 0).text()
            menu = QMenu(self)
            edit_action = menu.addAction("Edit")
            edit_action.triggered.connect(lambda: self.edit_process(name))
            menu.exec_(self.process_table.viewport().mapToGlobal(pos))
    
    def load_config(self):
        """Load configuration from a JSON file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, 'Load Config File',
            '', 'JSON Files (*.json)'
        )
        if file_name:
            try:
                self.sheriff.load_config(file_name)
                self.current_config_file = file_name
                self.statusBar().showMessage(f'Loaded config from {file_name}')
            except Exception as e:
                QMessageBox.warning(
                    self, 'Error',
                    f'Failed to load config: {str(e)}'
                )
    
    def save_config(self):
        """Save configuration to a JSON file."""
        if not self.current_config_file:
            self.current_config_file, _ = QFileDialog.getSaveFileName(
                self, 'Save Config File',
                '', 'JSON Files (*.json)'
            )
        
        if self.current_config_file:
            if self.sheriff.save_config(self.current_config_file):
                self.statusBar().showMessage(f'Saved config to {self.current_config_file}')
            else:
                QMessageBox.warning(
                    self, 'Error',
                    f'Failed to save config'
                )
    
    def create_action_button(self, process: ProcessInfo) -> QWidget:
        """Create action buttons for a process."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if process.status == "running":
            # Stop button
            stop_btn = QPushButton('Stop')
            stop_btn.clicked.connect(
                lambda: self.sheriff.stop_process(process.name)
            )
            layout.addWidget(stop_btn)
            
            # Restart button
            restart_btn = QPushButton('Restart')
            restart_btn.clicked.connect(
                lambda: self.sheriff.restart_process(process.name)
            )
            layout.addWidget(restart_btn)
        else:
            # Start button
            start_btn = QPushButton('Start')
            start_btn.clicked.connect(
                lambda: self.sheriff.start_process(process)
            )
            layout.addWidget(start_btn)
        
        return widget
    
    def update_deputy_table(self):
        """Update the deputy table with current information."""
        deputies = self.sheriff.get_deputy_status()
        self.deputy_table.setRowCount(len(deputies))
        
        for i, deputy in enumerate(deputies):
            # Hostname
            self.deputy_table.setItem(
                i, 0, QTableWidgetItem(deputy["hostname"])
            )
            # URL
            self.deputy_table.setItem(
                i, 1, QTableWidgetItem(deputy["url"])
            )
            # Status
            status_item = QTableWidgetItem(deputy["status"])
            if deputy["status"] == "healthy":
                status_item.setForeground(Qt.green)
            else:
                status_item.setForeground(Qt.red)
            self.deputy_table.setItem(i, 2, status_item)
            # CPU %
            self.deputy_table.setItem(
                i, 3, QTableWidgetItem(f'{deputy.get("cpu_percent", 0):.1f}')
            )
            # Memory %
            self.deputy_table.setItem(
                i, 4, QTableWidgetItem(f'{deputy.get("memory_percent", 0):.1f}')
            )
    
    def update_process_table(self):
        """Update the process table with current information."""
        processes = self.sheriff.get_all_processes()
        self.process_table.setRowCount(len(processes))
        
        for i, process in enumerate(processes):
            # Name
            self.process_table.setItem(
                i, 0, QTableWidgetItem(process.name)
            )
            # Host
            self.process_table.setItem(
                i, 1, QTableWidgetItem(process.host)
            )
            # Status
            status_item = QTableWidgetItem(process.status)
            if process.status == "running":
                status_item.setForeground(Qt.green)
            else:
                status_item.setForeground(Qt.red)
            self.process_table.setItem(i, 2, status_item)
            # PID
            self.process_table.setItem(
                i, 3, QTableWidgetItem(str(process.pid or ''))
            )
            # CPU %
            self.process_table.setItem(
                i, 4, QTableWidgetItem(f'{process.cpu_percent:.1f}')
            )
            # Memory %
            self.process_table.setItem(
                i, 5, QTableWidgetItem(f'{process.memory_percent:.1f}')
            )
            # Uptime
            uptime = ''
            if process.start_time:
                uptime_secs = int(process.to_dict()["uptime"])
                uptime = f'{uptime_secs // 3600}h {(uptime_secs % 3600) // 60}m {uptime_secs % 60}s'
            self.process_table.setItem(
                i, 6, QTableWidgetItem(uptime)
            )
            # Actions
            self.process_table.setCellWidget(
                i, 7, self.create_action_button(process)
            )
    
    def update_tables(self):
        """Update all tables."""
        self.update_deputy_table()
        self.update_process_table()
    
    def closeEvent(self, event):
        """Handle application shutdown."""
        self.sheriff.stop_update_thread()
        event.accept()


def main():
    """Start the Sheriff GUI application."""
    app = QApplication(sys.argv)
    window = SheriffGUI()
    window.show()
    sys.exit(app.exec_()) 