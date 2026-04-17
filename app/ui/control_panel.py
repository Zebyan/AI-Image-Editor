from PySide6.QtCore import Signal, Qt
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
    QDoubleSpinBox,
    QSlider,
)


class ControlPanel(QWidget):
    resize_requested = Signal(int, int, str)
    rotate_requested = Signal(float, str, bool)
    flip_requested = Signal(str)
    crop_apply_requested = Signal()
    crop_cancel_requested = Signal()
    brightness_contrast_requested = Signal(int, int)

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
        self.rotate_page = self._build_rotate_page()
        self.flip_page = self._build_flip_page()
        self.crop_page = self._build_crop_page()
        self.brightness_contrast_page = self._build_brightness_contrast_page()

        self.stack.addWidget(self.empty_page)                 # 0
        self.stack.addWidget(self.resize_page)                # 1
        self.stack.addWidget(self.rotate_page)                # 2
        self.stack.addWidget(self.flip_page)                  # 3
        self.stack.addWidget(self.crop_page)                  # 4
        self.stack.addWidget(self.brightness_contrast_page)   # 5

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

        self.resize_interpolation_combo = QComboBox()
        self.resize_interpolation_combo.addItems([
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
        form.addRow("Interpolation", self.resize_interpolation_combo)

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

    def _build_rotate_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        form = QFormLayout()

        self.rotate_angle_spin = QDoubleSpinBox()
        self.rotate_angle_spin.setRange(-360.0, 360.0)
        self.rotate_angle_spin.setDecimals(1)
        self.rotate_angle_spin.setSingleStep(1.0)
        self.rotate_angle_spin.setValue(0.0)

        self.rotate_interpolation_combo = QComboBox()
        self.rotate_interpolation_combo.addItems([
            "Nearest",
            "Bilinear",
            "Bicubic",
            "Lanczos",
        ])

        self.expand_canvas_checkbox = QCheckBox("Expand canvas to fit rotated image")
        self.expand_canvas_checkbox.setChecked(True)

        form.addRow("Angle (degrees)", self.rotate_angle_spin)
        form.addRow("Interpolation", self.rotate_interpolation_combo)
        form.addRow("", self.expand_canvas_checkbox)

        quick_row = QHBoxLayout()
        self.rotate_minus_90_button = QPushButton("-90°")
        self.rotate_plus_90_button = QPushButton("+90°")
        self.rotate_180_button = QPushButton("180°")

        self.rotate_minus_90_button.clicked.connect(
            lambda: self.rotate_angle_spin.setValue(-90.0)
        )
        self.rotate_plus_90_button.clicked.connect(
            lambda: self.rotate_angle_spin.setValue(90.0)
        )
        self.rotate_180_button.clicked.connect(
            lambda: self.rotate_angle_spin.setValue(180.0)
        )

        quick_row.addWidget(self.rotate_minus_90_button)
        quick_row.addWidget(self.rotate_plus_90_button)
        quick_row.addWidget(self.rotate_180_button)

        action_row = QHBoxLayout()
        self.rotate_apply_button = QPushButton("Apply Rotation")
        self.rotate_reset_button = QPushButton("Reset Fields")

        self.rotate_apply_button.clicked.connect(self._emit_rotate_requested)
        self.rotate_reset_button.clicked.connect(self._reset_rotate_fields)

        action_row.addWidget(self.rotate_apply_button)
        action_row.addWidget(self.rotate_reset_button)

        layout.addLayout(form)
        layout.addLayout(quick_row)
        layout.addLayout(action_row)
        layout.addStretch()

        page.setLayout(layout)
        return page

    def _build_flip_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()

        description = QLabel(
            "Flip mirrors the image across an axis. "
            "Choose horizontal, vertical, or both."
        )
        description.setWordWrap(True)

        self.flip_horizontal_button = QPushButton("Flip Horizontal")
        self.flip_vertical_button = QPushButton("Flip Vertical")
        self.flip_both_button = QPushButton("Flip Both")

        self.flip_horizontal_button.clicked.connect(
            lambda: self.flip_requested.emit("horizontal")
        )
        self.flip_vertical_button.clicked.connect(
            lambda: self.flip_requested.emit("vertical")
        )
        self.flip_both_button.clicked.connect(
            lambda: self.flip_requested.emit("both")
        )

        layout.addWidget(description)
        layout.addWidget(self.flip_horizontal_button)
        layout.addWidget(self.flip_vertical_button)
        layout.addWidget(self.flip_both_button)
        layout.addStretch()

        page.setLayout(layout)
        return page

    def _build_crop_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()

        self.crop_status_label = QLabel(
            "Drag a rectangle on the image to choose the crop area."
        )
        self.crop_status_label.setWordWrap(True)

        self.crop_selection_info = QLabel("No crop selected")
        self.crop_selection_info.setWordWrap(True)

        action_row = QHBoxLayout()
        self.crop_apply_button = QPushButton("Apply Crop")
        self.crop_cancel_button = QPushButton("Cancel Crop")

        self.crop_apply_button.setEnabled(False)

        self.crop_apply_button.clicked.connect(self.crop_apply_requested.emit)
        self.crop_cancel_button.clicked.connect(self.crop_cancel_requested.emit)

        action_row.addWidget(self.crop_apply_button)
        action_row.addWidget(self.crop_cancel_button)

        layout.addWidget(self.crop_status_label)
        layout.addWidget(self.crop_selection_info)
        layout.addLayout(action_row)
        layout.addStretch()

        page.setLayout(layout)
        return page

    def _build_brightness_contrast_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()

        description = QLabel(
            "Adjust brightness and contrast of the image. "
            "Brightness shifts pixel values. Contrast scales them."
        )
        description.setWordWrap(True)

        brightness_label = QLabel("Brightness")
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_value_label = QLabel("0")

        contrast_label = QLabel("Contrast")
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)
        self.contrast_value_label = QLabel("0")

        self.brightness_slider.valueChanged.connect(
            lambda value: self.brightness_value_label.setText(str(value))
        )
        self.contrast_slider.valueChanged.connect(
            lambda value: self.contrast_value_label.setText(str(value))
        )

        brightness_row = QHBoxLayout()
        brightness_row.addWidget(self.brightness_slider)
        brightness_row.addWidget(self.brightness_value_label)

        contrast_row = QHBoxLayout()
        contrast_row.addWidget(self.contrast_slider)
        contrast_row.addWidget(self.contrast_value_label)

        button_row = QHBoxLayout()
        self.brightness_contrast_apply_button = QPushButton("Apply Adjustment")
        self.brightness_contrast_reset_button = QPushButton("Reset Fields")

        self.brightness_contrast_apply_button.clicked.connect(
            self._emit_brightness_contrast_requested
        )
        self.brightness_contrast_reset_button.clicked.connect(
            self._reset_brightness_contrast_fields
        )

        button_row.addWidget(self.brightness_contrast_apply_button)
        button_row.addWidget(self.brightness_contrast_reset_button)

        layout.addWidget(description)
        layout.addWidget(brightness_label)
        layout.addLayout(brightness_row)
        layout.addWidget(contrast_label)
        layout.addLayout(contrast_row)
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

    def set_crop_selection_info(
        self,
        has_selection: bool,
        x: int = 0,
        y: int = 0,
        width: int = 0,
        height: int = 0,
    ) -> None:
        if has_selection:
            self.crop_selection_info.setText(
                f"Crop: x={x}, y={y}, width={width}, height={height}"
            )
            self.crop_apply_button.setEnabled(True)
        else:
            self.crop_selection_info.setText("No crop selected")
            self.crop_apply_button.setEnabled(False)

    def current_tool_name(self) -> str:
        item = self.tool_list.currentItem()
        return item.text() if item else ""

    def _on_tool_changed(self, tool_name: str) -> None:
        if self.current_module != "Edit":
            self.stack.setCurrentIndex(0)
            return

        if tool_name == "Resize":
            self.stack.setCurrentIndex(1)
        elif tool_name == "Rotate":
            self.stack.setCurrentIndex(2)
        elif tool_name == "Flip":
            self.stack.setCurrentIndex(3)
        elif tool_name == "Crop":
            self.stack.setCurrentIndex(4)
        elif tool_name == "Brightness / Contrast":
            self.stack.setCurrentIndex(5)
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
        interpolation = self.resize_interpolation_combo.currentText()
        self.resize_requested.emit(width, height, interpolation)

    def _reset_resize_fields(self) -> None:
        if self._original_resize_width and self._original_resize_height:
            self.set_resize_source_dimensions(
                self._original_resize_width,
                self._original_resize_height,
            )

    def _emit_rotate_requested(self) -> None:
        angle = self.rotate_angle_spin.value()
        interpolation = self.rotate_interpolation_combo.currentText()
        expand_canvas = self.expand_canvas_checkbox.isChecked()
        self.rotate_requested.emit(angle, interpolation, expand_canvas)

    def _reset_rotate_fields(self) -> None:
        self.rotate_angle_spin.setValue(0.0)
        self.rotate_interpolation_combo.setCurrentText("Bilinear")
        self.expand_canvas_checkbox.setChecked(True)

    def _emit_brightness_contrast_requested(self) -> None:
        brightness = self.brightness_slider.value()
        contrast = self.contrast_slider.value()
        self.brightness_contrast_requested.emit(brightness, contrast)

    def _reset_brightness_contrast_fields(self) -> None:
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(0)