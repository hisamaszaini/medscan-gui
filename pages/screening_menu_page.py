import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
)
from components.header import Header
from components.card import ScreeningChoiceCard

class ScreeningMenuPage(QWidget):
    startScreening = Signal(str)
    goBack = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 20, 40, 40)
        main_layout.setSpacing(20)

        self.header = Header(self)

        back_icon = qta.icon("fa5s.chevron-left", color="#374151")
        self.header.history_button.setText("Kembali")
        self.header.history_button.setIcon(back_icon)
        self.header.history_button.clicked.disconnect()
        self.header.history_button.clicked.connect(self.goBack.emit)

        title_layout = QVBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)

        step_label = QLabel("Langkah 1 dari 4")
        step_label.setObjectName("stepLabel")
        step_label.setAlignment(Qt.AlignCenter)

        title = QLabel("Pilih Jenis Screening")
        title.setObjectName("h2")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Pilih salah satu layanan di bawah ini untuk memulai proses deteksi dini.")
        subtitle.setObjectName("p")
        subtitle.setAlignment(Qt.AlignCenter)

        title_layout.addWidget(step_label, alignment=Qt.AlignCenter)
        title_layout.addSpacing(10)
        title_layout.addWidget(title, alignment=Qt.AlignCenter)
        title_layout.addWidget(subtitle, alignment=Qt.AlignCenter)

        card_layout = QHBoxLayout()
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(32)

        card1 = ScreeningChoiceCard(
            "fa5s.eye", "Diabetic Retinopathy",
            "Analisis citra retina untuk deteksi kerusakan mata akibat diabetes.",
            "diabetic_retinopathy", "#EF4444"
        )
        card2 = ScreeningChoiceCard(
            "fa5s.tint", "Anemia Detection",
            "Deteksi potensi anemia secara non-invasif melalui analisis warna kuku.",
            "anemia", "#EC4899"
        )
        card3 = ScreeningChoiceCard(
            "fa5s.user", "Malnutrition Screening",
            "Mendeteksi risiko malnutrisi pada anak-anak melalui analisis citra wajah.",
            "malnutrisi", "#0EA5E9"
        )

        card1.screeningSelected.connect(self.startScreening.emit)
        card2.screeningSelected.connect(self.startScreening.emit)
        card3.screeningSelected.connect(self.startScreening.emit)

        card_layout.addWidget(card1)
        card_layout.addWidget(card2)
        card_layout.addWidget(card3)

        main_layout.addWidget(self.header, 0, Qt.AlignTop | Qt.AlignHCenter)
        main_layout.addSpacing(30)
        main_layout.addLayout(title_layout)
        main_layout.addSpacing(30)
        main_layout.addLayout(card_layout)
        main_layout.addStretch()
