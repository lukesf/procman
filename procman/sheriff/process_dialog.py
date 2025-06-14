from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QTextEdit,
    QFormLayout, QMessageBox
)
from ..common.process_info import ProcessInfo


class ProcessDialog(QDialog):
    """Dialog for editing process information."""
    
    def __init__(self, process: ProcessInfo = None, parent=None):
        super().__init__(parent)
        self.process = process
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('Edit Process' if self.process else 'Add Process')
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Name field
        self.name_edit = QLineEdit()
        if self.process:
            self.name_edit.setText(self.process.name)
            self.name_edit.setReadOnly(True)
        form_layout.addRow('Name:', self.name_edit)
        
        # Command field
        self.command_edit = QLineEdit()
        if self.process:
            self.command_edit.setText(self.process.command)
        form_layout.addRow('Command:', self.command_edit)
        
        # Working directory field
        self.working_dir_edit = QLineEdit()
        if self.process:
            self.working_dir_edit.setText(self.process.working_dir)
        form_layout.addRow('Working Directory:', self.working_dir_edit)
        
        # Host field
        self.host_edit = QLineEdit()
        if self.process:
            self.host_edit.setText(self.process.host)
        form_layout.addRow('Host:', self.host_edit)
        
        # Checkboxes layout
        checkbox_layout = QHBoxLayout()
        
        # Autostart checkbox
        self.autostart_check = QCheckBox('Auto-start process')
        if self.process:
            self.autostart_check.setChecked(self.process.autostart)
        checkbox_layout.addWidget(self.autostart_check)
        
        # Auto-restart checkbox
        self.auto_restart_check = QCheckBox('Auto-restart on failure')
        if self.process:
            self.auto_restart_check.setChecked(self.process.auto_restart)
        checkbox_layout.addWidget(self.auto_restart_check)
        
        form_layout.addRow('', checkbox_layout)
        
        layout.addLayout(form_layout)
        
        # Output display if editing
        if self.process:
            # Stdout display
            layout.addWidget(QLabel('Standard Output:'))
            self.stdout_text = QTextEdit()
            self.stdout_text.setReadOnly(True)
            self.stdout_text.setPlainText('\n'.join(self.process.stdout_buffer))
            layout.addWidget(self.stdout_text)
            
            # Stderr display
            layout.addWidget(QLabel('Standard Error:'))
            self.stderr_text = QTextEdit()
            self.stderr_text.setReadOnly(True)
            self.stderr_text.setPlainText('\n'.join(self.process.stderr_buffer))
            layout.addWidget(self.stderr_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton('Save')
        save_btn.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        if self.process:
            delete_btn = QPushButton('Delete')
            delete_btn.clicked.connect(self.delete_process)
            button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def validate_and_accept(self):
        """Validate form before accepting."""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, 'Validation Error', 'Process name is required')
            return
            
        if not self.command_edit.text().strip():
            QMessageBox.warning(self, 'Validation Error', 'Command is required')
            return
            
        if not self.working_dir_edit.text().strip():
            QMessageBox.warning(self, 'Validation Error', 'Working directory is required')
            return
            
        if not self.host_edit.text().strip():
            QMessageBox.warning(self, 'Validation Error', 'Host is required')
            return
            
        self.accept()
    
    def get_process_info(self) -> ProcessInfo:
        """Get the process information from the dialog."""
        return ProcessInfo(
            name=self.name_edit.text().strip(),
            command=self.command_edit.text().strip(),
            working_dir=self.working_dir_edit.text().strip(),
            host=self.host_edit.text().strip(),
            autostart=self.autostart_check.isChecked(),
            auto_restart=self.auto_restart_check.isChecked()
        )
    
    def delete_process(self):
        """Set dialog result to indicate deletion."""
        reply = QMessageBox.question(
            self, 'Delete Process',
            f'Are you sure you want to delete process {self.process.name}?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.done(2)  # Use custom result code for deletion 