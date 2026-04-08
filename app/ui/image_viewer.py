from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import (
    QPixmap,
    QDragEnterEvent,
    QDropEvent,
    QColor,
    QPainter,
)
from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QFrame,
    QGraphicsTextItem,
)


class ImageViewer(QGraphicsView):
    image_dropped = Signal(str)
    image_cleared = Signal()
    zoom_changed = Signal(float)
    image_loaded = Signal(int, int)

    def __init__(self) -> None:
        super().__init__()

        self._scene = QGraphicsScene(self)
        self._pixmap_item = QGraphicsPixmapItem()
        self._placeholder_text = QGraphicsTextItem("Drop an image here\nor use File → Open")

        self._scene.addItem(self._pixmap_item)
        self._scene.addItem(self._placeholder_text)
        self.setScene(self._scene)

        self._has_image = False
        self._zoom_factor = 1.0
        self._is_panning = False

        self.setRenderHints(QPainter.RenderHint.SmoothPixmapTransform)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.setAcceptDrops(True)
        self.setBackgroundBrush(QColor("#1e1e1e"))
        self.setMouseTracking(True)

        self._setup_placeholder()
        self._update_placeholder_position()

    def _setup_placeholder(self) -> None:
        self._placeholder_text.setDefaultTextColor(QColor("#cfcfcf"))
        font = self._placeholder_text.font()
        font.setPointSize(14)
        self._placeholder_text.setFont(font)

    def _update_placeholder_position(self) -> None:
        rect = self.viewport().rect()
        scene_pos = self.mapToScene(rect.center())
        text_rect = self._placeholder_text.boundingRect()
        self._placeholder_text.setPos(
            scene_pos.x() - text_rect.width() / 2,
            scene_pos.y() - text_rect.height() / 2,
        )

    def has_image(self) -> bool:
        return self._has_image

    def set_image(self, pixmap: QPixmap) -> None:
        if pixmap.isNull():
            self.clear_image()
            return

        self._pixmap_item.setPixmap(pixmap)
        self._scene.setSceneRect(QRectF(self._pixmap_item.boundingRect()))
        self._has_image = True
        self._placeholder_text.setVisible(False)

        self.fit_to_view()
        self.image_loaded.emit(pixmap.width(), pixmap.height())

    def clear_image(self) -> None:
        self._pixmap_item.setPixmap(QPixmap())
        self._scene.setSceneRect(QRectF())
        self._has_image = False
        self._zoom_factor = 1.0
        self.resetTransform()
        self._placeholder_text.setVisible(True)
        self._update_placeholder_position()

        self.image_cleared.emit()
        self.zoom_changed.emit(self._zoom_factor)

    def fit_to_view(self) -> None:
        if not self._has_image:
            return

        rect = self._pixmap_item.boundingRect()
        if rect.isNull():
            return

        self.setSceneRect(QRectF(rect))
        self.resetTransform()

        view_rect = self.viewport().rect()
        if view_rect.width() <= 0 or view_rect.height() <= 0:
            return

        factor = min(
            view_rect.width() / rect.width(),
            view_rect.height() / rect.height(),
        )

        self.scale(factor, factor)
        self._zoom_factor = factor
        self.zoom_changed.emit(self._zoom_factor)

    def zoom_in(self) -> None:
        if not self._has_image:
            return

        factor = 1.25
        self.scale(factor, factor)
        self._zoom_factor *= factor
        self.zoom_changed.emit(self._zoom_factor)

    def zoom_out(self) -> None:
        if not self._has_image:
            return

        factor = 0.8
        self.scale(factor, factor)
        self._zoom_factor *= factor
        self.zoom_changed.emit(self._zoom_factor)

    def reset_zoom(self) -> None:
        if not self._has_image:
            return

        self.resetTransform()
        self._zoom_factor = 1.0
        self.zoom_changed.emit(self._zoom_factor)

    def wheelEvent(self, event) -> None:
        if not self._has_image:
            return super().wheelEvent(event)

        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._has_image:
            self._is_panning = True
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._is_panning:
            self._is_panning = False
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if not self._has_image:
            self._update_placeholder_position()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if not urls:
            event.ignore()
            return

        local_file = urls[0].toLocalFile()
        if local_file:
            self.image_dropped.emit(local_file)
            event.acceptProposedAction()
            return

        event.ignore()