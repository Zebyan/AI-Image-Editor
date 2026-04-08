import sys

from PySide6.QtWidgets import QApplication

from app.logger import setup_logger
from app.ui.main_window import MainWindow


def main() -> int:
    logger = setup_logger()
    logger.info("Starting application")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())