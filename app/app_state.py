from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from PySide6.QtGui import QPixmap


@dataclass
class AppState:
    original_pixmap: Optional[QPixmap] = None
    current_pixmap: Optional[QPixmap] = None
    preview_pixmap: Optional[QPixmap] = None
    current_image_path: Optional[str] = None

    undo_stack: list[QPixmap] = field(default_factory=list)
    redo_stack: list[QPixmap] = field(default_factory=list)

    max_history: int = 20

    def has_image(self) -> bool:
        return self.current_pixmap is not None and not self.current_pixmap.isNull()

    def clear(self) -> None:
        self.original_pixmap = None
        self.current_pixmap = None
        self.preview_pixmap = None
        self.current_image_path = None
        self.undo_stack.clear()
        self.redo_stack.clear()

    def set_image(self, pixmap: QPixmap, image_path: Optional[str] = None) -> None:
        copied = pixmap.copy()
        self.original_pixmap = copied.copy()
        self.current_pixmap = copied
        self.preview_pixmap = None
        self.current_image_path = image_path
        self.undo_stack.clear()
        self.redo_stack.clear()

    def set_preview(self, pixmap: QPixmap) -> None:
        self.preview_pixmap = pixmap.copy()

    def clear_preview(self) -> None:
        self.preview_pixmap = None

    def get_display_pixmap(self) -> Optional[QPixmap]:
        if self.preview_pixmap is not None and not self.preview_pixmap.isNull():
            return self.preview_pixmap
        return self.current_pixmap

    def push_undo(self) -> None:
        if self.current_pixmap is None or self.current_pixmap.isNull():
            return

        self.undo_stack.append(self.current_pixmap.copy())

        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

        self.redo_stack.clear()

    def apply_new_current(self, pixmap: QPixmap) -> None:
        if pixmap.isNull():
            return

        self.push_undo()
        self.current_pixmap = pixmap.copy()
        self.preview_pixmap = None

    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

    def undo(self) -> Optional[QPixmap]:
        if not self.can_undo() or self.current_pixmap is None:
            return None

        self.redo_stack.append(self.current_pixmap.copy())
        self.current_pixmap = self.undo_stack.pop()
        self.preview_pixmap = None
        return self.current_pixmap

    def redo(self) -> Optional[QPixmap]:
        if not self.can_redo() or self.current_pixmap is None:
            return None

        self.undo_stack.append(self.current_pixmap.copy())
        self.current_pixmap = self.redo_stack.pop()
        self.preview_pixmap = None
        return self.current_pixmap

    def reset_to_original(self) -> Optional[QPixmap]:
        if self.original_pixmap is None or self.original_pixmap.isNull():
            return None

        if self.current_pixmap is not None and not self.current_pixmap.isNull():
            self.push_undo()

        self.current_pixmap = self.original_pixmap.copy()
        self.preview_pixmap = None
        return self.current_pixmap