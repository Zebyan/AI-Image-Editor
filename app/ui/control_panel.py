from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QFormLayout,
    QSpinBox,
    QCheckBox,
    QComboBox,
    QPushButton,
    QHBoxLayout,
)


class ControlPanel(QWidget):
    resize_requested = Signal(int, int, str)

    def __init__(self) -> None:
        super().__init__()

        self.current_module = "Edit"

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        self.title = QLabel("Controls")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.description = QLabel("Select a module to see tools.")
        self.description.setWordWrap(True)

        self.tool_list = QListWidget()
        self.tool_list.currentTextChanged.connect(self._on_tool_changed)

        self.stack = QStackedWidget()
        self.empty_page = self._build_empty_page()
        self.resize_page = self._build_resize_page()

        self.stack.addWidget(self.empty_page)
        self.stack.addWidget(self.resize_page)

        self.layout.addWidget(self.title)
        self.layout.addWidget(self.description)
        self.layout.addWidget(self.tool_list)
        self.layout.addWidget(self.stack)
        self.layout.addStretch()

        self.setLayout(self.layout)

        self._original_resize_width = None
        self._original_resize_height = None

    def _build_empty_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        label = QLabel("Select a tool to configure it.")
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch()
        page.setLayout(layout)
        return page

    def _build_resize_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        form = QFormLayout()

        self.resize_width_spin = QSpinBox()
        self.resize_width_spin.setRange(1, 10000)
        self.resize_width_spin.setValue(800)

        self.resize_height_spin = QSpinBox()
        self.resize_height_spin.setRange(1, 10000)
        self.resize_height_spin.setValue(600)

        self.keep_aspect_checkbox = QCheckBox("Keep aspect ratio")
        self.keep_aspect_checkbox.setChecked(True)

        self.interpolation_combo = QComboBox()
        self.interpolation_combo.addItems([
            "Nearest",
            "Bilinear",
            "Bicubic",
            "Area",
            "Lanczos",
        ])

        self.resize_width_spin.valueChanged.connect(self._on_width_changed)
        self.resize_height_spin.valueChanged.connect(self._on_height_changed)

        form.addRow("Width", self.resize_width_spin)
        form.addRow("Height", self.resize_height_spin)
        form.addRow("", self.keep_aspect_checkbox)
        form.addRow("Interpolation", self.interpolation_combo)

        button_row = QHBoxLayout()
        self.resize_apply_button = QPushButton("Apply Resize")
        self.resize_reset_button = QPushButton("Reset Fields")

        self.resize_apply_button.clicked.connect(self._emit_resize_requested)
        self.resize_reset_button.clicked.connect(self._reset_resize_fields)

        button_row.addWidget(self.resize_apply_button)
        button_row.addWidget(self.resize_reset_button)

        layout.addLayout(form)
        layout.addLayout(button_row)
        layout.addStretch()

        page.setLayout(layout)
        return page

    def show_module(self, module_name: str) -> None:
        self.current_module = module_name
        self.title.setText(module_name)
        self.tool_list.clear()
        self.stack.setCurrentIndex(0)

        if module_name == "Edit":
            self.description.setText("Core image editing tools will appear here.")
            tools = [
                "Resize",
                "Rotate",
                "Flip",
                "Crop",
                "Brightness / Contrast",
                "Blur",
                "Sharpen",
            ]
        elif module_name == "Analysis":
            self.description.setText("Image analysis and metadata tools.")
            tools = [
                "Histogram",
                "Color Palette",
                "EXIF Metadata",
                "Sharpness Score",
            ]
        elif module_name == "Classification":
            self.description.setText("Image classification tools.")
            tools = [
                "ResNet-50",
                "EfficientNet-B0",
                "MobileNet-V3",
            ]
        elif module_name == "Detection":
            self.description.setText("Detection and segmentation tools.")
            tools = [
                "Face Detection",
                "Object Detection",
                "Segmentation",
            ]
        elif module_name == "Style Transfer":
            self.description.setText("Style transfer tools.")
            tools = [
                "Fast Neural Style",
                "AdaIN",
                "Custom Style Image",
            ]
        elif module_name == "Generative AI":
            self.description.setText("Generative workflows.")
            tools = [
                "Text-to-Image",
                "Image-to-Image",
                "Inpainting",
                "Upscaling",
            ]
        elif module_name == "3D":
            self.description.setText("3D generation and export tools.")
            tools = [
                "Image to 3D Mesh",
                "Export Mesh",
            ]
        else:
            self.description.setText("Select a module to see tools.")
            tools = []

        for tool in tools:
            QListWidgetItem(tool, self.tool_list)

        if self.tool_list.count() > 0:
            self.tool_list.setCurrentRow(0)

    def set_resize_source_dimensions(self, width: int, height: int) -> None:
        self._original_resize_width = width
        self._original_resize_height = height

        self.resize_width_spin.blockSignals(True)
        self.resize_height_spin.blockSignals(True)

        self.resize_width_spin.setValue(width)
        self.resize_height_spin.setValue(height)

        self.resize_width_spin.blockSignals(False)
        self.resize_height_spin.blockSignals(False)

    def _on_tool_changed(self, tool_name: str) -> None:
        if self.current_module == "Edit" and tool_name == "Resize":
            self.stack.setCurrentIndex(1)
        else:
            self.stack.setCurrentIndex(0)

    def _on_width_changed(self, new_width: int) -> None:
        if not self.keep_aspect_checkbox.isChecked():
            return

        if not self._original_resize_width or not self._original_resize_height:
            return

        ratio = self._original_resize_height / self._original_resize_width
        new_height = max(1, round(new_width * ratio))

        self.resize_height_spin.blockSignals(True)
        self.resize_height_spin.setValue(new_height)
        self.resize_height_spin.blockSignals(False)

    def _on_height_changed(self, new_height: int) -> None:
        if not self.keep_aspect_checkbox.isChecked():
            return

        if not self._original_resize_width or not self._original_resize_height:
            return

        ratio = self._original_resize_width / self._original_resize_height
        new_width = max(1, round(new_height * ratio))

        self.resize_width_spin.blockSignals(True)
        self.resize_width_spin.setValue(new_width)
        self.resize_width_spin.blockSignals(False)

    def _emit_resize_requested(self) -> None:
        width = self.resize_width_spin.value()
        height = self.resize_height_spin.value()
        interpolation = self.interpolation_combo.currentText()
        self.resize_requested.emit(width, height, interpolation)

    def _reset_resize_fields(self) -> None:
        if self._original_resize_width and self._original_resize_height:
            self.set_resize_source_dimensions(
                self._original_resize_width,
                self._original_resize_height,
            )