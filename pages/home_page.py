from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton
)
from components.header import Header

class HomePage(QWidget):
    startClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 20, 40, 40)
        main_layout.setSpacing(20)

        self.header = Header(self)

        hero_layout = QVBoxLayout()
        hero_layout.setAlignment(Qt.AlignCenter)
        hero_layout.setSpacing(16)

        step_label = QLabel("AI-Powered Medical Screening")
        step_label.setObjectName("stepLabel")
        step_label.setAlignment(Qt.AlignCenter)

        title = QLabel("Deteksi Dini Penyakit\ndengan AI Terdepan")
        title.setObjectName("h1")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 52px;")

        subtitle = QLabel(
            "Screening cepat, akurat, dan terpercaya untuk berbagai kondisi kesehatan\n"
            "langsung dari genggaman Anda."
        )
        subtitle.setObjectName("p")
        subtitle.setAlignment(Qt.AlignCenter)

        hero_layout.addSpacing(40)
        hero_layout.addWidget(step_label, alignment=Qt.AlignCenter)
        hero_layout.addSpacing(10)
        hero_layout.addWidget(title, alignment=Qt.AlignCenter)
        hero_layout.addWidget(subtitle, alignment=Qt.AlignCenter)
        hero_layout.addSpacing(20)

        self.start_button = QPushButton("Mulai Screening Sekarang")
        self.start_button.setObjectName("primaryButton")
        self.start_button.clicked.connect(self.startClicked.emit)
        hero_layout.addWidget(self.start_button, 0, Qt.AlignCenter)

        main_layout.addWidget(self.header, 0, Qt.AlignTop | Qt.AlignHCenter)
        main_layout.addStretch()
        main_layout.addLayout(hero_layout)
        main_layout.addStretch()