from PySide6.QtCore import Qt, Signal, QRectF, QRect, QPoint, QPointF
from PySide6.QtGui import (
    QPixmap,
    QDragEnterEvent,
    QDropEvent,
    QColor,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QFrame,
    QGraphicsTextItem,
    QRubberBand,
)


class ImageViewer(QGraphicsView):
    image_dropped = Signal(str)
    image_cleared = Signal()
    zoom_changed = Signal(float)
    image_loaded = Signal(int, int)
    crop_selection_changed = Signal(bool, int, int, int, int)
    draw_session_changed = Signal(bool)

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

        self._crop_mode = False
        self._crop_origin = QPoint()
        self._crop_rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self.viewport())
        self._crop_scene_rect = QRectF()

        self._draw_mode = False
        self._draw_brush_size = 8
        self._draw_color = QColor("#ff0000")
        self._draw_active = False
        self._draw_last_point = QPointF()
        self._draw_base_pixmap = QPixmap()
        self._draw_working_pixmap = QPixmap()

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
        self.clear_crop_selection()
        self.cancel_drawing()

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
        self.clear_crop_selection()
        self.cancel_drawing()

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

    def set_crop_mode(self, enabled: bool) -> None:
        self._crop_mode = enabled
        if not enabled:
            self.clear_crop_selection()
            if not self._draw_mode:
                self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.setCursor(Qt.CursorShape.CrossCursor)

    def clear_crop_selection(self) -> None:
        self._crop_rubber_band.hide()
        self._crop_scene_rect = QRectF()
        self.crop_selection_changed.emit(False, 0, 0, 0, 0)

    def has_crop_selection(self) -> bool:
        return (
            not self._crop_scene_rect.isNull()
            and self._crop_scene_rect.width() > 0
            and self._crop_scene_rect.height() > 0
        )

    def get_crop_rect(self) -> tuple[int, int, int, int] | None:
        if not self.has_crop_selection():
            return None

        rect = self._crop_scene_rect.intersected(self._pixmap_item.boundingRect())
        if rect.isNull() or rect.width() <= 0 or rect.height() <= 0:
            return None

        x = max(0, round(rect.x()))
        y = max(0, round(rect.y()))
        width = max(1, round(rect.width()))
        height = max(1, round(rect.height()))

        return x, y, width, height

    def set_draw_mode(self, enabled: bool) -> None:
        self._draw_mode = enabled
        self._draw_active = False

        if enabled and self._has_image:
            current_pixmap = self._pixmap_item.pixmap()
            self._draw_base_pixmap = current_pixmap.copy()
            self._draw_working_pixmap = current_pixmap.copy()
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self._draw_base_pixmap = QPixmap()
            self._draw_working_pixmap = QPixmap()
            if not self._crop_mode:
                self.setCursor(Qt.CursorShape.ArrowCursor)

        self.draw_session_changed.emit(enabled)

    def set_draw_brush(self, size: int, color: QColor) -> None:
        self._draw_brush_size = max(1, size)
        self._draw_color = color

    def is_draw_mode(self) -> bool:
        return self._draw_mode

    def has_drawing_session(self) -> bool:
        return self._draw_mode and not self._draw_working_pixmap.isNull()

    def get_drawn_pixmap(self) -> QPixmap | None:
        if self._draw_working_pixmap.isNull():
            return None
        return self._draw_working_pixmap.copy()

    def cancel_drawing(self) -> None:
        self._draw_active = False
        if not self._draw_mode:
            self._draw_base_pixmap = QPixmap()
            self._draw_working_pixmap = QPixmap()
            return

        if not self._draw_base_pixmap.isNull():
            self._draw_working_pixmap = self._draw_base_pixmap.copy()
            self._pixmap_item.setPixmap(self._draw_base_pixmap)

    def commit_drawing(self) -> QPixmap | None:
        if self._draw_working_pixmap.isNull():
            return None
        committed = self._draw_working_pixmap.copy()
        self._draw_base_pixmap = committed.copy()
        return committed

    def _scene_pos_to_image_point(self, scene_pos: QPointF) -> QPointF:
        rect = self._pixmap_item.boundingRect()
        x = min(max(scene_pos.x(), rect.left()), rect.right())
        y = min(max(scene_pos.y(), rect.top()), rect.bottom())
        return QPointF(x, y)

    def _draw_line_to(self, current_point: QPointF) -> None:
        if self._draw_working_pixmap.isNull():
            return

        painter = QPainter(self._draw_working_pixmap)
        pen = QPen(
            self._draw_color,
            self._draw_brush_size,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
        painter.setPen(pen)
        painter.drawLine(self._draw_last_point, current_point)
        painter.end()

        self._pixmap_item.setPixmap(self._draw_working_pixmap)
        self._draw_last_point = current_point

    def wheelEvent(self, event) -> None:
        if not self._has_image or self._crop_mode or self._draw_mode:
            return super().wheelEvent(event)

        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def mousePressEvent(self, event) -> None:
        if self._draw_mode and self._has_image and event.button() == Qt.MouseButton.LeftButton:
            scene_point = self.mapToScene(event.position().toPoint())
            image_point = self._scene_pos_to_image_point(scene_point)
            self._draw_active = True
            self._draw_last_point = image_point
            self._draw_line_to(image_point)
            return

        if self._crop_mode and self._has_image and event.button() == Qt.MouseButton.LeftButton:
            self._crop_origin = event.position().toPoint()
            self._crop_rubber_band.setGeometry(QRect(self._crop_origin, self._crop_origin))
            self._crop_rubber_band.show()
            return

        if event.button() == Qt.MouseButton.LeftButton and self._has_image:
            self._is_panning = True
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._draw_mode and self._draw_active:
            scene_point = self.mapToScene(event.position().toPoint())
            image_point = self._scene_pos_to_image_point(scene_point)
            self._draw_line_to(image_point)
            return

        if self._crop_mode and self._crop_rubber_band.isVisible():
            current_pos = event.position().toPoint()
            rect = QRect(self._crop_origin, current_pos).normalized()
            self._crop_rubber_band.setGeometry(rect)
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._draw_mode and event.button() == Qt.MouseButton.LeftButton:
            self._draw_active = False
            return

        if self._crop_mode and event.button() == Qt.MouseButton.LeftButton:
            rubber_rect = self._crop_rubber_band.geometry()
            if rubber_rect.width() > 1 and rubber_rect.height() > 1:
                top_left_scene = self.mapToScene(rubber_rect.topLeft())
                bottom_right_scene = self.mapToScene(rubber_rect.bottomRight())

                selection_rect = QRectF(top_left_scene, bottom_right_scene).normalized()
                selection_rect = selection_rect.intersected(self._pixmap_item.boundingRect())
                self._crop_scene_rect = selection_rect

                crop = self.get_crop_rect()
                if crop is not None:
                    self.crop_selection_changed.emit(True, *crop)
                else:
                    self.clear_crop_selection()
            else:
                self.clear_crop_selection()
            return

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