import qtawesome as qta
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QUrl, QSize, QThread
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QScrollArea
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from api_woker import ApiWorker
from config import API_BASE_URL
from components.header import Header

class ScreeningResultPage(QWidget):
    goHomeClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_thread = None
        self.api_worker = None
        self.image_downloader = QNetworkAccessManager(self)
        self.image_downloader.finished.connect(self.on_image_downloaded)
        self.init_ui()
        self.connect_signals()
        
    def init_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll.setWidget(content)

        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(40, 20, 40, 40)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.header = Header(self)
        self.header.history_button.setVisible(False)
        main_layout.addWidget(self.header, 0, Qt.AlignTop | Qt.AlignHCenter)

        # Title layout
        title_layout = QVBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)
        self.title = QLabel("Hasil Screening Anda")
        self.title.setObjectName("h2")
        self.title.setAlignment(Qt.AlignCenter)
        self.date_label = QLabel("")
        self.date_label.setObjectName("p")
        self.date_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(self.title, alignment=Qt.AlignCenter)
        title_layout.addWidget(self.date_label, alignment=Qt.AlignCenter)
        main_layout.addLayout(title_layout)
        main_layout.addSpacing(20)

        # Result card
        result_card = QWidget()
        result_card.setObjectName("card")
        result_layout = QVBoxLayout(result_card)
        result_layout.setAlignment(Qt.AlignCenter)
        result_card.setMinimumWidth(700)
        result_layout.setSpacing(15)
        result_layout.setContentsMargins(32, 32, 32, 32)

        self.status_icon_label = QLabel()
        self.status_icon_label.setAlignment(Qt.AlignCenter)

        self.status_text_label = QLabel("Menganalisis...")
        self.status_text_label.setFont(QFont("Segoe UI", 32, QFont.Bold))
        self.status_text_label.setAlignment(Qt.AlignCenter)

        self.summary_label = QLabel("Mengirim data dan menunggu hasil...")
        self.summary_label.setObjectName("p")
        self.summary_label.setAlignment(Qt.AlignCenter)
        self.summary_label.setWordWrap(True)

        self.confidence_label = QLabel("")
        self.confidence_label.setObjectName("stepLabel")
        self.confidence_label.setVisible(False)

        self.result_image_label = QLabel()
        self.result_image_label.setAlignment(Qt.AlignCenter)
        self.result_image_label.setVisible(False)
        self.result_image_label.setStyleSheet("border: 1px solid #E5E7EB; border-radius: 16px;")

        self.patient_info_label = QLabel("")
        self.patient_info_label.setObjectName("p")
        self.patient_info_label.setAlignment(Qt.AlignCenter)

        result_layout.addWidget(self.status_icon_label)
        result_layout.addWidget(self.status_text_label)
        result_layout.addWidget(self.summary_label)
        result_layout.addWidget(self.confidence_label, alignment=Qt.AlignCenter)
        result_layout.addWidget(self.result_image_label)
        result_layout.addWidget(self.patient_info_label)

        main_layout.addWidget(result_card, 0, Qt.AlignCenter)
        main_layout.addSpacing(20)

        # Home button
        self.home_button = QPushButton("Kembali ke Menu Utama")
        self.home_button.setObjectName("primaryButton")
        self.home_button.setIcon(qta.icon("fa5s.home", color="white"))
        main_layout.addWidget(self.home_button, 0, Qt.AlignCenter)
        main_layout.addStretch()

        # Layout utama window
        window_layout = QVBoxLayout(self)
        window_layout.addWidget(scroll)

    def connect_signals(self):
        self.home_button.clicked.connect(self.goHomeClicked.emit)

    def start_analysis(self, screening_type, patient_data, image_pixmap):
        # Reset UI
        self.status_text_label.setText("Menganalisis...")
        self.status_text_label.setStyleSheet("")
        self.summary_label.setText("Mengirim data dan menunggu hasil...")
        self.result_image_label.setVisible(False)
        self.confidence_label.setVisible(False)
        self.patient_info_label.setText("")
        self.date_label.setText("")

        # Loading spinner
        loading_icon = qta.icon("fa5s.spinner", color="#10B981")
        self.status_icon_label.setPixmap(loading_icon.pixmap(QSize(64, 64)))

        # Stop worker lama
        if self.api_thread and self.api_thread.isRunning():
            self.api_thread.quit()
            self.api_thread.wait()

        # Start worker baru
        self.api_thread = QThread()
        self.api_worker = ApiWorker(screening_type, patient_data, image_pixmap)
        self.api_worker.moveToThread(self.api_thread)
        self.api_thread.started.connect(self.api_worker.run)
        self.api_worker.finished.connect(self.on_analysis_finished)
        self.api_worker.error.connect(self.on_analysis_error)
        self.api_worker.finished.connect(self.api_thread.quit)
        self.api_worker.error.connect(self.api_thread.quit)
        self.api_thread.start()
        
    def on_analysis_finished(self, result_data):
        try:
            detections = result_data.get("detections", [])
            user = result_data.get("user", {})

            # Default values
            confidence = 0
            if not detections:
                status = "Gagal Deteksi"
                summary = "AI gagal mendeteksi apapun dari gambar ini."
            else:
                detected_class = int(detections[0].get("class", -1))
                confidence = float(detections[0].get("conf", 0)) * 100

                if detected_class == 0:
                    status = "Normal"
                    summary = "Hasil normal, tidak ada abnormalitas."
                elif detected_class == 1:
                    status = result_data.get("category", "Terdeteksi")
                    summary = f"Terdeteksi {status} pada gambar."
                else:
                    status = result_data.get("category", "Terdeteksi")
                    summary = f"Terdeteksi {status} pada gambar."

            # Mapping warna & icon
            color_map = {
                "Normal": "#10B981",
                "Anemia": "#F59E0B",
                "Malnutrisi": "#EF4444",
                "Diabetic Retinopathy": "#EF4444",
                "Gagal Deteksi": "#6B7280"
            }
            icon_map = {
                "Normal": "fa5s.check-circle",
                "Anemia": "fa5s.exclamation-triangle",
                "Malnutrisi": "fa5s.exclamation-triangle",
                "Diabetic Retinopathy": "fa5s.exclamation-triangle",
                "Gagal Deteksi": "fa5s.times-circle"
            }

            result_color = color_map.get(status, "#4B5563")
            result_icon = qta.icon(icon_map.get(status, "fa5s.question-circle"), color=result_color)

            # Update UI
            self.status_icon_label.setPixmap(result_icon.pixmap(QSize(64, 64)))
            self.status_text_label.setText(status)
            self.status_text_label.setStyleSheet(f"color: {result_color};")
            self.summary_label.setText(summary)
            self.confidence_label.setText(f"Tingkat Keyakinan AI: {confidence:.2f}%")
            self.confidence_label.setVisible(True)

            self.patient_info_label.setText(
                f"Nama: {user.get('name', 'N/A')} | Umur: {user.get('age', 'N/A')} | "
                f"Jenis Kelamin: {user.get('gender', 'N/A')}"
            )
            self.date_label.setText(f"Dihasilkan pada {datetime.now().strftime('%d %b %Y, %H:%M')}")

            # Download gambar hasil
            image_path = result_data.get("image_path")
            if image_path:
                url = f"{API_BASE_URL}/api/{image_path}"
                self.image_downloader.get(QNetworkRequest(QUrl(url)))

        except Exception as e:
            self.on_analysis_error(f"Gagal mem-parsing data: {str(e)}")


    def on_analysis_error(self, error_msg):
        error_icon = qta.icon("fa5s.times-circle", color="#EF4444")
        self.status_icon_label.setPixmap(error_icon.pixmap(QSize(64, 64)))
        self.status_text_label.setText("Analisis Gagal")
        self.status_text_label.setStyleSheet("color: #EF4444;")
        self.summary_label.setText(error_msg)
        self.date_label.setText("")
        QMessageBox.critical(self, "Error API", error_msg)

    def on_image_downloaded(self, reply):
        try:
            if reply.error() == QNetworkReply.NoError:
                data = reply.readAll()
                pixmap = QPixmap()
                if pixmap.loadFromData(data):
                    self.result_image_label.setPixmap(pixmap.scaled(
                        640, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    ))
                    self.result_image_label.setVisible(True)
            else:
                print(f"Image download error: {reply.errorString()}")
        except Exception as e:
            print(f"Error processing image: {e}")
        finally:
            reply.deleteLater()
