import sys
import cv2
import subprocess
import tempfile
import os
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QPixmap, QImage
import qtawesome as qta
from components.header import Header

class ImageCapturePage(QWidget):
    imageReady = Signal(QPixmap)
    backClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.captured_pixmap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.temp_file = os.path.join(tempfile.gettempdir(), "rpicam_temp.jpg")
        self.rpicam_proc = None
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.header = Header(self)
        self.header.history_button.setVisible(False)
        layout.addWidget(self.header)

        self.video_display = QLabel("Menyalakan Kamera...")
        self.video_display.setFixedSize(QSize(640, 480))
        self.video_display.setAlignment(Qt.AlignCenter)
        self.video_display.setStyleSheet("background-color: black; border-radius: 24px;")
        layout.addWidget(self.video_display)

        # Buttons
        btn_layout = QHBoxLayout()
        self.capture_button = QPushButton("Ambil Gambar")
        self.capture_button.setIcon(qta.icon("fa5s.camera", color="white"))
        self.upload_button = QPushButton("Upload Gambar")
        self.upload_button.setIcon(qta.icon("fa5s.upload"))
        btn_layout.addWidget(self.capture_button)
        btn_layout.addWidget(self.upload_button)
        layout.addLayout(btn_layout)

        # Navigation
        nav_layout = QHBoxLayout()
        self.back_button = QPushButton("Kembali")
        self.back_button.setIcon(qta.icon("fa5s.chevron-left"))
        self.next_button = QPushButton("Selesai & Lihat Hasil")
        self.next_button.setIcon(qta.icon("fa5s.arrow-right", color="white"))
        nav_layout.addWidget(self.back_button)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_button)
        layout.addLayout(nav_layout)

    def connect_signals(self):
        self.capture_button.clicked.connect(self.on_capture_clicked)
        self.upload_button.clicked.connect(self.on_upload_clicked)
        self.next_button.clicked.connect(self.on_next_clicked)
        self.back_button.clicked.connect(self.on_back_clicked)

    def start_camera(self, camera_num=0):
        # jalankan rpicam-hello di background
        if self.rpicam_proc:
            self.rpicam_proc.terminate()
        cmd = [
            "rpicam-hello",
            f"--camera={camera_num}",
            "--t=0",
            "--nopreview",
            f"--output={self.temp_file}"
        ]
        self.rpicam_proc = subprocess.Popen(cmd)
        self.timer.start(100)  # update preview setiap 100ms

    def stop_camera(self):
        self.timer.stop()
        if self.rpicam_proc:
            self.rpicam_proc.terminate()
            self.rpicam_proc = None

    def update_frame(self):
        if os.path.exists(self.temp_file):
            frame = cv2.imread(self.temp_file)
            if frame is not None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(q_image)
                self.video_display.setPixmap(pixmap.scaled(
                    self.video_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                ))

    def on_capture_clicked(self):
        if os.path.exists(self.temp_file):
            self.captured_pixmap = QPixmap(self.temp_file)
            self.stop_camera()
            self.video_display.setPixmap(self.captured_pixmap.scaled(
                self.video_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

    def on_upload_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Pilih Gambar", "", "Image Files (*.png *.jpg *.bmp)")
        if file_path:
            self.stop_camera()
            self.captured_pixmap = QPixmap(file_path)
            self.video_display.setPixmap(self.captured_pixmap.scaled(
                self.video_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

    def on_next_clicked(self):
        if self.captured_pixmap:
            self.imageReady.emit(self.captured_pixmap)
        else:
            QMessageBox.warning(self, "Tidak Ada Gambar", "Silakan ambil atau upload gambar terlebih dahulu.")

    def on_back_clicked(self):
        self.stop_camera()
        self.backClicked.emit()
