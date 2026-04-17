from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QObject, Signal


class TaskWorker(QObject):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, fn: Callable[..., Any], *args, **kwargs) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))