from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGraphicsDropShadowEffect,
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt, Signal
import qtawesome as qta

class Header(QWidget):
    historyClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("headerCard")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        logo_layout = QHBoxLayout()
        logo_icon = QLabel()
        logo_pixmap = qta.icon("fa5s.heartbeat", color="#10B981").pixmap(28, 28)
        logo_icon.setPixmap(logo_pixmap)

        title = QLabel("MedScan")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color: #1F2937;")

        logo_layout.addWidget(logo_icon)
        logo_layout.addSpacing(10)
        logo_layout.addWidget(title)

        self.history_button = QPushButton("Riwayat")
        self.history_button.setIcon(qta.icon("fa5s.history", color="#047857"))
        self.history_button.clicked.connect(self.historyClicked.emit)
        self.history_button.setStyleSheet("""
            background-color: #ECFDF5;
            color: #047857;
            border: none;
            padding: 10px 16px;
        """)

        layout.addLayout(logo_layout)
        layout.addStretch()
        layout.addWidget(self.history_button)

        self.setStyleSheet("""
            QWidget#headerCard {
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 20px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)