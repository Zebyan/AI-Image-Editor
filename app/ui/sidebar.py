from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton


class Sidebar(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.buttons = {}

        modules = [
            "Edit",
            "Analysis",
            "Classification",
            "Detection",
            "Style Transfer",
            "Generative AI",
            "3D",
        ]

        for name in modules:
            btn = QPushButton(name)
            btn.setCheckable(True)
            layout.addWidget(btn)
            self.buttons[name] = btn

        layout.addStretch()
        self.setLayout(layout)