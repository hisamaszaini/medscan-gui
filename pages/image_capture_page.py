import sys
import cv2
import time  # Diperlukan untuk stabilisasi AE/AWB
import qtawesome as qta

from PySide6.QtCore import Qt, QTimer, QSize, Signal
from PySide6.QtGui import QPixmap, QImage, QFont, QCloseEvent
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QFileDialog, QSpacerItem, QSizePolicy
)

# Impor header Anda, sesuai permintaan
from components.header import Header

try:
    from picamera2 import Picamera2
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
except Exception as e:
    # Menangani error jika libcamera tidak terkonfigurasi
    print(f"Picamera2 import failed even if installed (libcamera issue?): {e}")
    PICAMERA_AVAILABLE = False


class ImageCapturePage(QWidget):
    """
    Widget halaman untuk mengambil atau mengupload gambar, 
    dioptimalkan untuk Picamera2 (kualitas tinggi) dan fallback ke OpenCV.
    """
    imageReady = Signal(QPixmap)
    backClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.guides = {
            "diabetic_retinopathy": "Pastikan retina terlihat jelas dan pencahayaan cukup.",
            "anemia": "Fokus pada kuku tangan. Pastikan pencahayaan merata.",
            "malnutrisi": "Fokus pada wajah subjek, terutama pipi dan dagu."
        }
        self.captured_pixmap = None
        self.capture = None  # Untuk cv2.VideoCapture
        self.picam = None    # Untuk Picamera2
        
        self.timer = QTimer(self)
        
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        """Inisialisasi semua komponen UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 20, 40, 40)
        main_layout.setSpacing(20)

        # Header
        self.header = Header(self)
        self.header.history_button.setVisible(False)

        # Title
        title_layout = QVBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)
        step_label = QLabel("Langkah 3 dari 4")
        step_label.setObjectName("stepLabel")
        step_label.setAlignment(Qt.AlignCenter)
        title = QLabel("Ambil atau Upload Gambar")
        title.setObjectName("h2")
        title.setAlignment(Qt.AlignCenter)
        self.subtitle_guide = QLabel("Posisikan subjek sesuai panduan...")
        self.subtitle_guide.setObjectName("p")
        self.subtitle_guide.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(step_label, alignment=Qt.AlignCenter)
        title_layout.addSpacing(10)
        title_layout.addWidget(title, alignment=Qt.AlignCenter)
        title_layout.addWidget(self.subtitle_guide, alignment=Qt.AlignCenter)

        # Content Layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)

        # Camera Column
        camera_col = QVBoxLayout()
        camera_col.setAlignment(Qt.AlignCenter)

        self.video_display = QLabel("Menyalakan Kamera...")
        self.video_display.setFixedSize(QSize(640, 480))
        self.video_display.setAlignment(Qt.AlignCenter)
        self.video_display.setScaledContents(True)
        self.video_display.setStyleSheet("background-color: black; border-radius: 24px;")

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        self.capture_button = QPushButton("Ambil Gambar")
        self.capture_button.setObjectName("primaryButton")
        self.capture_button.setIcon(qta.icon("fa5s.camera", color="white"))
        self.upload_button = QPushButton("Upload Gambar")
        self.upload_button.setObjectName("secondaryButton")
        self.upload_button.setIcon(qta.icon("fa5s.upload"))
        button_layout.addWidget(self.capture_button)
        button_layout.addWidget(self.upload_button)

        camera_col.addWidget(self.video_display)
        
        spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        camera_col.addItem(spacer)
        
        camera_col.addLayout(button_layout)

        # Guide Box
        guide_box = QWidget()
        guide_box.setObjectName("guideBox")
        guide_layout = QVBoxLayout(guide_box)
        guide_box.setMaximumWidth(400)
        guide_title = QLabel("Panduan Pengambilan Gambar")
        guide_title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        guide_text = QLabel(
            "• Pencahayaan cukup dan merata.\n\n"
            "• Kamera stabil dan fokus pada subjek.\n\n"
            "• Subjek terlihat jelas dan sesuai area panduan."
        )
        guide_text.setObjectName("p")
        guide_text.setWordWrap(True)
        guide_text.setStyleSheet("font-size: 15px; line-height: 1.5;")
        guide_layout.addWidget(guide_title)
        guide_layout.addSpacing(15)
        guide_layout.addWidget(guide_text)
        guide_layout.addStretch()

        content_layout.addLayout(camera_col, 2)
        content_layout.addWidget(guide_box, 1)

        # Navigation
        nav_layout = QHBoxLayout()
        self.back_button = QPushButton("Kembali")
        self.back_button.setObjectName("secondaryButton")
        self.back_button.setIcon(qta.icon("fa5s.chevron-left"))
        self.next_button = QPushButton("Selesai & Lihat Hasil")
        self.next_button.setObjectName("primaryButton")
        self.next_button.setIcon(qta.icon("fa5s.arrow-right", color="white"))
        nav_layout.addWidget(self.back_button)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_button)

        # Add all to main layout
        main_layout.addWidget(self.header, 0, Qt.AlignTop | Qt.AlignHCenter)
        main_layout.addLayout(title_layout)
        main_layout.addSpacing(20)
        main_layout.addLayout(content_layout)
        main_layout.addStretch()
        main_layout.addLayout(nav_layout)

    def connect_signals(self):
        """Menghubungkan sinyal tombol ke slot."""
        self.back_button.clicked.connect(self.on_back_clicked)
        self.next_button.clicked.connect(self.on_next_clicked)
        self.capture_button.clicked.connect(self.on_capture_clicked)
        self.upload_button.clicked.connect(self.on_upload_clicked)

    def start_camera(self, screening_type):
        """
        Inisialisasi dan mulai stream kamera.
        Menggunakan Picamera2 jika tersedia, jika tidak, fallback ke OpenCV.
        """
        self.subtitle_guide.setText(self.guides.get(screening_type, "..."))
        self.captured_pixmap = None
        self.video_display.setText("Menyalakan Kamera...")

        self.stop_camera()

        camera_num = 1 if screening_type == "diabetic_retinopathy" else 0

        if PICAMERA_AVAILABLE:
            try:
                self.picam = Picamera2(camera_num=camera_num)
                
                # Konfigurasi 2-stream untuk kualitas tinggi
                config = self.picam.create_still_configuration(
                    main={"size": (640, 480)},
                    lores={"size": (640, 480)},
                    display="lores"
                )
                self.picam.configure(config)
                
                print("Memulai Picamera2 dan stabilisasi AE/AWB...")
                self.picam.start()
                time.sleep(1.5) # Waktu untuk stabilisasi "auto-adjust"
                print("Picamera2 siap.")

                self.capture_button.setEnabled(True)
                self.timer.timeout.connect(self.update_frame_picam)
                self.timer.start(30) # ~33 FPS
                return
            except Exception as e:
                print(f"Gagal membuka Picamera2 (idx {camera_num}): {e}\nMencoba OpenCV...")
                if self.picam:
                    self.picam.close()
                    self.picam = None
                # Lanjutkan ke fallback OpenCV
        
        # Fallback atau default ke OpenCV
        print(f"Menggunakan fallback OpenCV untuk kamera {camera_num}...")
        self.capture = cv2.VideoCapture(camera_num)
        if not self.capture.isOpened():
            self.video_display.setText(f"Error: Gagal membuka kamera (idx {camera_num}).")
            self.capture_button.setEnabled(False)
            return
        
        print("Menunggu kamera OpenCV...")
        time.sleep(1.0) # Beri waktu stabilisasi juga untuk OpenCV
        print("Kamera OpenCV siap.")
        
        self.capture_button.setEnabled(True)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def stop_camera(self):
        """Hentikan timer dan lepaskan semua resource kamera dengan aman."""
        try:
            self.timer.timeout.disconnect()
        except (TypeError, RuntimeError):
            pass # Tidak ada yang terhubung
            
        self.timer.stop()

        if self.capture:
            self.capture.release()
            self.capture = None
            print("Kamera OpenCV dilepaskan.")
            
        if self.picam:
            try:
                if self.picam.started:
                    self.picam.stop()
                self.picam.close()
            except Exception as e:
                print(f"Error saat menutup Picamera2: {e}")
            self.picam = None
            print("Picamera2 dilepaskan.")

    def update_frame(self):
        """Update frame dari OpenCV (cv2.VideoCapture)."""
        if not self.capture or not self.capture.isOpened():
            return
            
        ret, frame = self.capture.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.flip(frame_rgb, 1) # Mirror view
            
            pixmap = self._convert_frame_to_pixmap(frame_rgb)
            self.video_display.setPixmap(pixmap.scaled(
                self.video_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

    def update_frame_picam(self):
        """Update frame dari Picamera2 (lores stream)."""
        if not self.picam:
            return
            
        try:
            # Ambil dari "lores" stream (640x480 RGB888)
            frame_rgb = self.picam.capture_array()
            
            pixmap = self._convert_frame_to_pixmap(frame_rgb)
            self.video_display.setPixmap(pixmap.scaled(
                self.video_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        except Exception as e:
            print(f"Error update frame picam: {e}")
            self.stop_camera()
            self.video_display.setText("Error stream kamera.")


    def _convert_frame_to_pixmap(self, frame_rgb) -> QPixmap:
        """Helper untuk konversi array numpy RGB 3-channel ke QPixmap."""
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(q_image)

    def on_capture_clicked(self):
        """Mengambil gambar diam dari stream yang aktif."""
        frame_rgb = None

        if self.picam:
            self.timer.stop() # Hentikan preview
            print("Mengambil foto resolusi penuh (3280x2464)...")
            try:
                # Ambil dari stream "lores" (warna seperti live preview)
                frame_rgb = self.picam.capture_array("lores")

                # Pastikan frame punya 3 channel
                if frame_rgb.ndim == 2:  # grayscale
                    frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_GRAY2RGB)
                elif frame_rgb.shape[2] == 4:  # kadang ada alpha
                    frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGRA2RGB)

                # Konversi ke pixmap
                self.captured_pixmap = self._convert_frame_to_pixmap(frame_rgb)
                self.video_display.setPixmap(self.captured_pixmap.scaled(
                    self.video_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                ))

                print("Foto Picamera2 berhasil diambil.")
            except Exception as e:
                QMessageBox.warning(self, "Kamera Error", f"Gagal mengambil foto: {e}")
                self.timer.start(30) # Mulai lagi preview jika gagal
                return

        elif self.capture and self.capture.isOpened():
            print("Mengambil foto dari OpenCV...")
            ret, frame = self.capture.read()
            if not ret:
                QMessageBox.warning(self, "Kamera Error", "Gagal mengambil gambar dari kamera.")
                return
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.flip(frame_rgb, 1)

            # Pastikan frame punya 3 channel (seharusnya sudah)
            if frame_rgb.ndim == 2:
                frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_GRAY2RGB)
            elif frame_rgb.shape[2] == 4:
                frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGRA2RGB)

            self.captured_pixmap = self._convert_frame_to_pixmap(frame_rgb)
            self.video_display.setPixmap(self.captured_pixmap.scaled(
                self.video_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
            print("Foto OpenCV berhasil diambil.")
        else:
            QMessageBox.warning(self, "Kamera Error", "Kamera tidak aktif.")
            return

        self.stop_camera()

    def on_upload_clicked(self):
        """Buka dialog file untuk memilih gambar."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Pilih Gambar", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.stop_camera()
            self.captured_pixmap = QPixmap(file_path)
            
            if self.captured_pixmap.isNull():
                QMessageBox.warning(self, "Error", "Gagal membaca file gambar.")
                self.captured_pixmap = None
                return
                
            self.video_display.setPixmap(self.captured_pixmap.scaled(
                self.video_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

    def on_next_clicked(self):
        """Kirim sinyal bahwa gambar siap jika valid."""
        if not self.captured_pixmap or self.captured_pixmap.isNull():
            QMessageBox.warning(self, "Tidak Ada Gambar", 
                                "Silakan ambil atau upload gambar terlebih dahulu.")
            return
        self.imageReady.emit(self.captured_pixmap)

    def on_back_clicked(self):
        """Hentikan kamera dan kirim sinyal kembali."""
        self.stop_camera()
        self.backClicked.emit()

    def closeEvent(self, event: QCloseEvent):
        """Memastikan kamera dilepaskan saat widget ditutup."""
        print("Menutup widget, menghentikan kamera...")
        self.stop_camera()
        super().closeEvent(event)