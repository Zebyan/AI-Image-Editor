from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class ControlPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        self.title = QLabel("Controls")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.content = QLabel("Select a module to see tools.")
        self.content.setWordWrap(True)

        layout.addWidget(self.title)
        layout.addWidget(self.content)
        layout.addStretch()

        self.setLayout(layout)