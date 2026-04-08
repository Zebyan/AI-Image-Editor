from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
)


class ControlPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        self.title = QLabel("Controls")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.description = QLabel("Select a module to see tools.")
        self.description.setWordWrap(True)

        self.tool_list = QListWidget()

        self.layout.addWidget(self.title)
        self.layout.addWidget(self.description)
        self.layout.addWidget(self.tool_list)
        self.layout.addStretch()

        self.setLayout(self.layout)

    def show_module(self, module_name: str) -> None:
        self.title.setText(module_name)
        self.tool_list.clear()

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