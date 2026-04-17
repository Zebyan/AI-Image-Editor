from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QButtonGroup


class Sidebar(QWidget):
    module_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.buttons = {}
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        modules = [
            "Edit",
            "GIF",
            "Style Transfer",
            "Generative AI",
        ]

        for index, name in enumerate(modules):
            btn = QPushButton(name)
            btn.setCheckable(True)

            self.button_group.addButton(btn, index)
            self.buttons[name] = btn
            layout.addWidget(btn)

            btn.clicked.connect(
                lambda checked, module=name: self._on_module_clicked(module)
            )

        layout.addStretch()
        self.setLayout(layout)

        self.select_module("Edit")

    def _on_module_clicked(self, module_name: str) -> None:
        self.module_selected.emit(module_name)

    def select_module(self, module_name: str) -> None:
        button = self.buttons.get(module_name)
        if button is None:
            return

        button.setChecked(True)
        self.module_selected.emit(module_name)