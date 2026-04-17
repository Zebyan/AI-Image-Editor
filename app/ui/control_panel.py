from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor
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
    QFrame,
    QTextEdit,
    QColorDialog,
)


class ControlPanel(QWidget):
    resize_requested = Signal(int, int, str)
    rotate_requested = Signal(float, str, bool)
    flip_requested = Signal(str)
    crop_apply_requested = Signal()
    crop_cancel_requested = Signal()
    brightness_contrast_requested = Signal(int, int)
    blur_requested = Signal(int)

    draw_mode_toggled = Signal(bool)
    draw_brush_changed = Signal(int, QColor)
    draw_apply_requested = Signal()
    draw_cancel_requested = Signal()

    gif_generate_requested = Signal(str, int, float, int, int, int)
    gif_save_requested = Signal()

    style_preset_requested = Signal(str, int)
    style_custom_image_requested = Signal()
    style_custom_requested = Signal(int)

    text_to_image_requested = Signal(str, int, int, int, float, int)

    def __init__(self) -> None:
        super().__init__()

        self.current_module = "Edit"
        self._draw_color = QColor("#ff0000")

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
        self.blur_page = self._build_blur_page()
        self.draw_page = self._build_draw_page()

        self.gif_page = self._build_gif_page()
        self.style_transfer_page = self._build_style_transfer_page()
        self.generative_ai_page = self._build_generative_ai_page()

        self.stack.addWidget(self.empty_page)                 # 0
        self.stack.addWidget(self.resize_page)                # 1
        self.stack.addWidget(self.rotate_page)                # 2
        self.stack.addWidget(self.flip_page)                  # 3
        self.stack.addWidget(self.crop_page)                  # 4
        self.stack.addWidget(self.brightness_contrast_page)   # 5
        self.stack.addWidget(self.blur_page)                  # 6
        self.stack.addWidget(self.draw_page)                  # 7
        self.stack.addWidget(self.gif_page)                   # 8
        self.stack.addWidget(self.style_transfer_page)        # 9
        self.stack.addWidget(self.generative_ai_page)         # 10

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

    def _build_placeholder_page(self, text: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        label = QLabel(text)
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
            "Flip mirrors the image across an axis. Choose horizontal, vertical, or both."
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
            "Adjust brightness and contrast of the image. Brightness shifts pixel values. Contrast scales them."
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

    def _build_blur_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()

        description = QLabel(
            "Gaussian blur softens detail by averaging nearby pixels with distance-based weights."
        )
        description.setWordWrap(True)

        strength_label = QLabel("Blur Strength")
        self.blur_slider = QSlider(Qt.Orientation.Horizontal)
        self.blur_slider.setRange(0, 20)
        self.blur_slider.setValue(0)
        self.blur_value_label = QLabel("0")

        self.blur_slider.valueChanged.connect(
            lambda value: self.blur_value_label.setText(str(value))
        )

        blur_row = QHBoxLayout()
        blur_row.addWidget(self.blur_slider)
        blur_row.addWidget(self.blur_value_label)

        button_row = QHBoxLayout()
        self.blur_apply_button = QPushButton("Apply Blur")
        self.blur_reset_button = QPushButton("Reset Fields")

        self.blur_apply_button.clicked.connect(self._emit_blur_requested)
        self.blur_reset_button.clicked.connect(self._reset_blur_fields)

        button_row.addWidget(self.blur_apply_button)
        button_row.addWidget(self.blur_reset_button)

        layout.addWidget(description)
        layout.addWidget(strength_label)
        layout.addLayout(blur_row)
        layout.addLayout(button_row)
        layout.addStretch()

        page.setLayout(layout)
        return page

    def _build_draw_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()

        description = QLabel(
            "Draw directly on the image using a brush. Choose size and color, then start drawing."
        )
        description.setWordWrap(True)

        brush_size_label = QLabel("Brush Size")
        self.draw_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.draw_size_slider.setRange(1, 100)
        self.draw_size_slider.setValue(8)
        self.draw_size_value_label = QLabel("8")
        self.draw_size_slider.valueChanged.connect(
            lambda value: self.draw_size_value_label.setText(str(value))
        )
        self.draw_size_slider.valueChanged.connect(self._emit_draw_brush_changed)

        draw_size_row = QHBoxLayout()
        draw_size_row.addWidget(self.draw_size_slider)
        draw_size_row.addWidget(self.draw_size_value_label)

        color_label = QLabel("Brush Color")
        self.draw_color_preview = QFrame()
        self.draw_color_preview.setFixedHeight(28)
        self.draw_color_preview.setStyleSheet(
            "background-color: #ff0000; border: 1px solid #888;"
        )

        self.draw_color_button = QPushButton("Choose Color")
        self.draw_color_button.clicked.connect(self._choose_draw_color)

        color_row = QHBoxLayout()
        color_row.addWidget(self.draw_color_preview)
        color_row.addWidget(self.draw_color_button)

        self.draw_toggle_button = QPushButton("Start Drawing")
        self.draw_toggle_button.setCheckable(True)
        self.draw_toggle_button.toggled.connect(self._on_draw_toggled)

        action_row = QHBoxLayout()
        self.draw_apply_button = QPushButton("Apply Drawing")
        self.draw_cancel_button = QPushButton("Cancel Drawing")

        self.draw_apply_button.clicked.connect(self.draw_apply_requested.emit)
        self.draw_cancel_button.clicked.connect(self.draw_cancel_requested.emit)

        action_row.addWidget(self.draw_apply_button)
        action_row.addWidget(self.draw_cancel_button)

        layout.addWidget(description)
        layout.addWidget(brush_size_label)
        layout.addLayout(draw_size_row)
        layout.addWidget(color_label)
        layout.addLayout(color_row)
        layout.addWidget(self.draw_toggle_button)
        layout.addLayout(action_row)
        layout.addStretch()

        page.setLayout(layout)
        return page

    def _build_gif_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        form = QFormLayout()

        self.gif_effect_combo = QComboBox()
        self.gif_effect_combo.addItems([
            "Zoom Loop",
            "Pan Loop",
            "Blur Pulse",
        ])

        self.gif_frame_count_spin = QSpinBox()
        self.gif_frame_count_spin.setRange(2, 60)
        self.gif_frame_count_spin.setValue(12)

        self.gif_max_zoom_spin = QDoubleSpinBox()
        self.gif_max_zoom_spin.setRange(1.0, 2.0)
        self.gif_max_zoom_spin.setSingleStep(0.01)
        self.gif_max_zoom_spin.setDecimals(2)
        self.gif_max_zoom_spin.setValue(1.15)

        self.gif_pan_pixels_spin = QSpinBox()
        self.gif_pan_pixels_spin.setRange(0, 300)
        self.gif_pan_pixels_spin.setValue(30)

        self.gif_blur_strength_spin = QSpinBox()
        self.gif_blur_strength_spin.setRange(0, 20)
        self.gif_blur_strength_spin.setValue(4)

        self.gif_duration_spin = QSpinBox()
        self.gif_duration_spin.setRange(20, 1000)
        self.gif_duration_spin.setValue(80)

        form.addRow("Effect", self.gif_effect_combo)
        form.addRow("Frame Count", self.gif_frame_count_spin)
        form.addRow("Max Zoom", self.gif_max_zoom_spin)
        form.addRow("Pan Pixels", self.gif_pan_pixels_spin)
        form.addRow("Blur Strength", self.gif_blur_strength_spin)
        form.addRow("Frame Duration (ms)", self.gif_duration_spin)

        button_row = QHBoxLayout()
        self.gif_generate_button = QPushButton("Generate GIF")
        self.gif_save_button = QPushButton("Save GIF")
        self.gif_save_button.setEnabled(False)

        self.gif_generate_button.clicked.connect(self._emit_gif_generate_requested)
        self.gif_save_button.clicked.connect(self.gif_save_requested.emit)

        button_row.addWidget(self.gif_generate_button)
        button_row.addWidget(self.gif_save_button)

        self.gif_status_label = QLabel("No GIF generated yet.")
        self.gif_status_label.setWordWrap(True)

        layout.addLayout(form)
        layout.addLayout(button_row)
        layout.addWidget(self.gif_status_label)
        layout.addStretch()

        page.setLayout(layout)
        return page

    def _build_style_transfer_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()

        self.style_transfer_tool_list = QListWidget()
        self.style_transfer_tool_list.addItems([
            "Preset Styles",
            "Custom Style",
        ])

        self.style_transfer_stack = QStackedWidget()

        preset_page = QWidget()
        preset_layout = QVBoxLayout()

        preset_description = QLabel(
            "Choose a predefined artistic style and apply it to the current image."
        )
        preset_description.setWordWrap(True)

        preset_form = QFormLayout()

        self.style_preset_combo = QComboBox()
        self.style_preset_combo.addItems([
            "Van Gogh",
            "Mosaic",
            "Sketch",
        ])

        self.style_preset_strength_slider = QSlider(Qt.Orientation.Horizontal)
        self.style_preset_strength_slider.setRange(0, 100)
        self.style_preset_strength_slider.setValue(50)

        self.style_preset_strength_label = QLabel("50")
        self.style_preset_strength_slider.valueChanged.connect(
            lambda value: self.style_preset_strength_label.setText(str(value))
        )

        strength_row = QHBoxLayout()
        strength_row.addWidget(self.style_preset_strength_slider)
        strength_row.addWidget(self.style_preset_strength_label)

        preset_form.addRow("Preset", self.style_preset_combo)
        preset_form.addRow("Style Strength", strength_row)

        self.style_preset_apply_button = QPushButton("Apply Preset Style")
        self.style_preset_apply_button.clicked.connect(self._emit_style_preset_requested)

        preset_layout.addWidget(preset_description)
        preset_layout.addLayout(preset_form)
        preset_layout.addWidget(self.style_preset_apply_button)
        preset_layout.addStretch()
        preset_page.setLayout(preset_layout)

        custom_page = QWidget()
        custom_layout = QVBoxLayout()

        custom_description = QLabel(
            "Load another image and use it as the style source for the current image."
        )
        custom_description.setWordWrap(True)

        self.style_custom_path_label = QLabel("No style image selected")
        self.style_custom_path_label.setWordWrap(True)

        self.style_custom_load_button = QPushButton("Load Style Image")
        self.style_custom_load_button.clicked.connect(self.style_custom_image_requested.emit)

        custom_form = QFormLayout()

        self.style_custom_strength_slider = QSlider(Qt.Orientation.Horizontal)
        self.style_custom_strength_slider.setRange(0, 100)
        self.style_custom_strength_slider.setValue(50)

        self.style_custom_strength_label = QLabel("50")
        self.style_custom_strength_slider.valueChanged.connect(
            lambda value: self.style_custom_strength_label.setText(str(value))
        )

        custom_strength_row = QHBoxLayout()
        custom_strength_row.addWidget(self.style_custom_strength_slider)
        custom_strength_row.addWidget(self.style_custom_strength_label)

        custom_form.addRow("Style Strength", custom_strength_row)

        self.style_custom_apply_button = QPushButton("Apply Custom Style")
        self.style_custom_apply_button.clicked.connect(self._emit_style_custom_requested)
        self.style_custom_apply_button.setEnabled(False)

        custom_layout.addWidget(custom_description)
        custom_layout.addWidget(self.style_custom_load_button)
        custom_layout.addWidget(self.style_custom_path_label)
        custom_layout.addLayout(custom_form)
        custom_layout.addWidget(self.style_custom_apply_button)
        custom_layout.addStretch()
        custom_page.setLayout(custom_layout)

        self.style_transfer_stack.addWidget(preset_page)
        self.style_transfer_stack.addWidget(custom_page)

        self.style_transfer_tool_list.currentRowChanged.connect(
            self.style_transfer_stack.setCurrentIndex
        )
        self.style_transfer_tool_list.setCurrentRow(0)

        layout.addWidget(self.style_transfer_tool_list)
        layout.addWidget(self.style_transfer_stack)
        page.setLayout(layout)
        return page

    def _build_generative_ai_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()

        description = QLabel(
            "Generate an image from a text description using AI. "
            "The first generation may take longer as the model loads."
        )
        description.setWordWrap(True)

        form_layout = QFormLayout()

        self.text_prompt_edit = QTextEdit()
        self.text_prompt_edit.setPlaceholderText(
            "Describe the image you want to generate...\n\n"
            "Examples:\n"
            "• A beautiful sunset over mountains\n"
            "• A cyberpunk city at night\n"
            "• A serene lake with cherry blossoms\n"
            "• A futuristic robot in a garden"
        )
        self.text_prompt_edit.setMaximumHeight(120)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(256, 1024)
        self.width_spin.setValue(512)
        self.width_spin.setSingleStep(64)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(256, 1024)
        self.height_spin.setValue(512)
        self.height_spin.setSingleStep(64)

        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(10, 50)
        self.steps_spin.setValue(20)
        self.steps_spin.setToolTip("More steps = higher quality but slower generation")

        self.guidance_spin = QDoubleSpinBox()
        self.guidance_spin.setRange(1.0, 20.0)
        self.guidance_spin.setValue(7.5)
        self.guidance_spin.setSingleStep(0.5)
        self.guidance_spin.setToolTip("Higher values follow the prompt more closely")

        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 999999)
        self.seed_spin.setValue(0)
        self.seed_spin.setSpecialValueText("Random")
        self.seed_spin.setToolTip("Set a seed for reproducible results")

        form_layout.addRow("Prompt", self.text_prompt_edit)
        form_layout.addRow("Width", self.width_spin)
        form_layout.addRow("Height", self.height_spin)
        form_layout.addRow("Steps", self.steps_spin)
        form_layout.addRow("Guidance", self.guidance_spin)
        form_layout.addRow("Seed", self.seed_spin)

        self.generate_button = QPushButton("Generate Image")
        self.generate_button.setStyleSheet("font-weight: bold; padding: 10px;")
        self.generate_button.clicked.connect(self._emit_text_to_image_requested)

        layout.addWidget(description)
        layout.addLayout(form_layout)
        layout.addWidget(self.generate_button)
        layout.addStretch()

        page.setLayout(layout)
        return page

    def show_module(self, module_name: str) -> None:
        self.current_module = module_name
        self.title.setText(module_name)
        self.tool_list.clear()
        self.stack.setCurrentIndex(0)

        if module_name == "Edit":
            self.description.setText("Core image editing tools.")
            tools = [
                "Resize",
                "Rotate",
                "Flip",
                "Crop",
                "Brightness / Contrast",
                "Blur",
                "Draw",
            ]
        elif module_name == "GIF":
            self.description.setText("Create an animated GIF from the current image.")
            tools = [
                "Animation Builder",
            ]
        elif module_name == "Style Transfer":
            self.description.setText("Apply the style of another image to the current image.")
            tools = [
                "Style Transfer",
            ]
        elif module_name == "Generative AI":
            self.description.setText("Generate an image from text.")
            tools = [
                "Text to Image",
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

    def set_draw_mode_state(self, enabled: bool) -> None:
        self.draw_toggle_button.blockSignals(True)
        self.draw_toggle_button.setChecked(enabled)
        self.draw_toggle_button.setText("Stop Drawing" if enabled else "Start Drawing")
        self.draw_toggle_button.blockSignals(False)

    def set_gif_ready(self, ready: bool, message: str) -> None:
        self.gif_save_button.setEnabled(ready)
        self.gif_status_label.setText(message)

    def set_style_custom_image_path(self, path: str | None) -> None:
        if path:
            self.style_custom_path_label.setText(path)
            self.style_custom_apply_button.setEnabled(True)
        else:
            self.style_custom_path_label.setText("No style image selected")
            self.style_custom_apply_button.setEnabled(False)

    def current_tool_name(self) -> str:
        item = self.tool_list.currentItem()
        return item.text() if item else ""

    def _on_tool_changed(self, tool_name: str) -> None:
        if self.current_module == "Edit":
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
            elif tool_name == "Blur":
                self.stack.setCurrentIndex(6)
            elif tool_name == "Draw":
                self.stack.setCurrentIndex(7)
            else:
                self.stack.setCurrentIndex(0)
        elif self.current_module == "GIF":
            self.stack.setCurrentIndex(8)
        elif self.current_module == "Style Transfer":
            self.stack.setCurrentIndex(9)
        elif self.current_module == "Generative AI":
            self.stack.setCurrentIndex(10)
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
        self.resize_requested.emit(
            self.resize_width_spin.value(),
            self.resize_height_spin.value(),
            self.resize_interpolation_combo.currentText(),
        )

    def _reset_resize_fields(self) -> None:
        if self._original_resize_width and self._original_resize_height:
            self.set_resize_source_dimensions(
                self._original_resize_width,
                self._original_resize_height,
            )

    def _emit_rotate_requested(self) -> None:
        self.rotate_requested.emit(
            self.rotate_angle_spin.value(),
            self.rotate_interpolation_combo.currentText(),
            self.expand_canvas_checkbox.isChecked(),
        )

    def _reset_rotate_fields(self) -> None:
        self.rotate_angle_spin.setValue(0.0)
        self.rotate_interpolation_combo.setCurrentText("Bilinear")
        self.expand_canvas_checkbox.setChecked(True)

    def _emit_brightness_contrast_requested(self) -> None:
        self.brightness_contrast_requested.emit(
            self.brightness_slider.value(),
            self.contrast_slider.value(),
        )

    def _reset_brightness_contrast_fields(self) -> None:
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(0)

    def _emit_blur_requested(self) -> None:
        self.blur_requested.emit(self.blur_slider.value())

    def _reset_blur_fields(self) -> None:
        self.blur_slider.setValue(0)

    def _choose_draw_color(self) -> None:
        color = QColorDialog.getColor(self._draw_color, self, "Select Brush Color")
        if not color.isValid():
            return

        self._draw_color = color
        self.draw_color_preview.setStyleSheet(
            f"background-color: {color.name()}; border: 1px solid #888;"
        )
        self._emit_draw_brush_changed()

    def _emit_draw_brush_changed(self) -> None:
        self.draw_brush_changed.emit(self.draw_size_slider.value(), self._draw_color)

    def _on_draw_toggled(self, checked: bool) -> None:
        self.draw_toggle_button.setText("Stop Drawing" if checked else "Start Drawing")
        self.draw_mode_toggled.emit(checked)

    def _emit_gif_generate_requested(self) -> None:
        self.gif_generate_requested.emit(
            self.gif_effect_combo.currentText(),
            self.gif_frame_count_spin.value(),
            self.gif_max_zoom_spin.value(),
            self.gif_pan_pixels_spin.value(),
            self.gif_blur_strength_spin.value(),
            self.gif_duration_spin.value(),
        )

    def _emit_style_preset_requested(self) -> None:
        self.style_preset_requested.emit(
            self.style_preset_combo.currentText(),
            self.style_preset_strength_slider.value(),
        )

    def _emit_style_custom_requested(self) -> None:
        self.style_custom_requested.emit(
            self.style_custom_strength_slider.value(),
        )

    def _emit_text_to_image_requested(self) -> None:
        prompt = self.text_prompt_edit.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "No Prompt", "Please enter a text prompt.")
            return

        width = self.width_spin.value()
        height = self.height_spin.value()
        steps = self.steps_spin.value()
        guidance = self.guidance_spin.value()
        seed = self.seed_spin.value() if self.seed_spin.value() != 0 else None

        self.text_to_image_requested.emit(prompt, width, height, steps, guidance, seed)