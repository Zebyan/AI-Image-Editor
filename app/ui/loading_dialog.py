from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar


class LoadingDialog(QDialog):
    def __init__(self, message: str = "Processing...", parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Please wait")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setFixedSize(320, 120)

        layout = QVBoxLayout()

        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)

        layout.addWidget(self.message_label)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def set_message(self, message: str) -> None:
        self.message_label.setText(message)