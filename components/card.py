from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QGraphicsDropShadowEffect,
    QSizePolicy,
)
import qtawesome as qta

class ScreeningChoiceCard(QWidget):
    screeningSelected = Signal(str)

    def __init__(self, icon_name, title, description, type_str, color, parent=None):
        super().__init__(parent)
        self.type = type_str
        self.color = color
        self.icon_name = icon_name

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("card")
        self.setFixedSize(300, 350)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(72, 72)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet(f"background-color: {self.color}; border-radius: 16px;")
        icon = qta.icon(self.icon_name, color="white").pixmap(QSize(36, 36))
        self.icon_label.setPixmap(icon)

        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))

        self.description_label = QLabel(description)
        self.description_label.setFont(QFont("Segoe UI", 11))
        self.description_label.setWordWrap(True)

        r = int(self.color[1:3], 16)
        g = int(self.color[3:5], 16)
        b = int(self.color[5:7], 16)

        self.button = QPushButton("Mulai Screening")
        self.button.clicked.connect(lambda: self.screeningSelected.emit(self.type))
        self.button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color};
                color: white;
                border: none;
            }}
            QPushButton:hover {{
                background-color: rgba({r}, {g}, {b}, 0.8);
            }}
        """)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)
        layout.addStretch()
        layout.addWidget(self.button)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)