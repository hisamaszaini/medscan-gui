import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QFormLayout, QLineEdit, QSpinBox,
    QButtonGroup, QRadioButton
)
from components.header import Header

class InputDataPage(QWidget):
    dataSubmitted = Signal(dict)
    backClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 20, 40, 40)
        main_layout.setSpacing(20)

        self.header = Header(self)
        self.header.history_button.setVisible(False)

        title_layout = QVBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)

        step_label = QLabel("Langkah 2 dari 4")
        step_label.setObjectName("stepLabel")
        step_label.setAlignment(Qt.AlignCenter)

        title = QLabel("Input Data Pasien")
        title.setObjectName("h2")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Masukkan informasi dasar pasien untuk melanjutkan proses screening.")
        subtitle.setObjectName("p")
        subtitle.setAlignment(Qt.AlignCenter)

        title_layout.addWidget(step_label, alignment=Qt.AlignCenter)
        title_layout.addSpacing(10)
        title_layout.addWidget(title, alignment=Qt.AlignCenter)
        title_layout.addWidget(subtitle, alignment=Qt.AlignCenter)

        form_card = QWidget()
        form_card.setObjectName("formCard")
        form_card.setMaximumWidth(700)

        form_layout = QFormLayout(form_card)
        form_layout.setSpacing(20)
        form_layout.setContentsMargins(32, 32, 32, 32)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Contoh: Budi Santoso")

        self.age_input = QSpinBox()
        self.age_input.setRange(1, 150)
        self.age_input.setValue(30)

        # Gunakan QButtonGroup untuk radio button
        self.gender_group = QButtonGroup()
        self.gender_male = QRadioButton("Pria")
        self.gender_female = QRadioButton("Wanita")
        self.gender_group.addButton(self.gender_male, 0)
        self.gender_group.addButton(self.gender_female, 1)

        gender_box = QWidget()
        gender_layout = QHBoxLayout(gender_box)
        gender_layout.setContentsMargins(0, 0, 0, 0)
        gender_layout.addWidget(self.gender_male)
        gender_layout.addWidget(self.gender_female)
        gender_box.setStyleSheet("border: none;")

        form_layout.addRow(QLabel("Nama Lengkap:", self), self.name_input)
        form_layout.addRow(QLabel("Umur:", self), self.age_input)
        form_layout.addRow(QLabel("Jenis Kelamin:", self), gender_box)

        nav_layout = QHBoxLayout()
        self.back_button = QPushButton("Kembali")
        self.back_button.setObjectName("secondaryButton")
        self.back_button.setIcon(qta.icon("fa5s.chevron-left"))

        self.next_button = QPushButton("Lanjutkan")
        self.next_button.setObjectName("primaryButton")
        self.next_button.setIcon(qta.icon("fa5s.arrow-right", color="white"))

        nav_layout.addWidget(self.back_button)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_button)

        main_layout.addWidget(self.header, 0, Qt.AlignTop | Qt.AlignHCenter)
        main_layout.addLayout(title_layout)
        main_layout.addSpacing(20)
        main_layout.addWidget(form_card, 0, Qt.AlignCenter)
        main_layout.addSpacing(20)
        main_layout.addLayout(nav_layout)
        main_layout.addStretch()

    def connect_signals(self):
        self.back_button.clicked.connect(self.backClicked.emit)
        self.next_button.clicked.connect(self.on_next_clicked)

    def on_next_clicked(self):
        name = self.name_input.text().strip()
        age = self.age_input.value()
        gender = ""

        if self.gender_male.isChecked():
            gender = "male"
        elif self.gender_female.isChecked():
            gender = "female"

        # Validasi data
        if not name:
            QMessageBox.warning(self, "Data Tidak Lengkap", "Nama pasien tidak boleh kosong.")
            return
        if len(name) < 3:
            QMessageBox.warning(self, "Data Tidak Valid", "Nama pasien minimal 3 karakter.")
            return
        if age <= 0:
            QMessageBox.warning(self, "Data Tidak Valid", "Umur harus lebih dari 0.")
            return
        if not gender:
            QMessageBox.warning(self, "Data Tidak Lengkap", "Mohon pilih jenis kelamin.")
            return

        patient_data = {"name": name, "age": age, "gender": gender}
        self.dataSubmitted.emit(patient_data)

    def reset_form(self):
        self.name_input.clear()
        self.age_input.setValue(30)
        self.gender_group.setExclusive(False)
        self.gender_male.setChecked(False)
        self.gender_female.setChecked(False)
        self.gender_group.setExclusive(True)
