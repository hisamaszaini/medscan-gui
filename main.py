import sys
from PySide6.QtWidgets import QApplication
from main_window import MainWindow
from PySide6.QtGui import QFont

def load_stylesheet():
    with open("assets/style.qss", "r") as f:
        return f.read()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyleSheet(load_stylesheet())
    app.setFont(QFont("Segoe UI", 10))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
