import sys
import cv2
import qtawesome as qta

from PySide6.QtCore import Qt, QTimer, QSize, Signal
from PySide6.QtGui import QPixmap, QImage, QFont
from PySide6.QtWidgets import (
	QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
	QMessageBox, QFileDialog, QSpacerItem, QSizePolicy
)
from components.header import Header

try:
	from picamera2 import Picamera2
	PICAMERA_AVAILABLE = True
except ImportError:
	PICAMERA_AVAILABLE = False

class ImageCapturePage(QWidget):
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
		self.capture = None
		self.picam = None
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.update_frame_generic)
		self.init_ui()
		self.connect_signals()

	def init_ui(self):
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

		# Tambahkan video display
		camera_col.addWidget(self.video_display)

		# Spacer untuk jarak konsisten
		spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Fixed)
		camera_col.addItem(spacer)

		# Tambahkan tombol
		camera_col.addLayout(button_layout)

		# Guide Box
		guide_box = QWidget()
		guide_box.setObjectName("guideBox")
		guide_layout = QVBoxLayout(guide_box)
		guide_box.setMaximumWidth(400)
		self.guide_title = QLabel("Panduan Pengambilan Gambar")
		self.guide_title.setFont(QFont("Segoe UI", 18, QFont.Bold))
		self.guide_text = QLabel(
			"• Pencahayaan cukup dan merata.\n\n"
			"• Kamera stabil dan fokus pada subjek.\n\n"
			"• Subjek terlihat jelas dan sesuai area panduan."
		)
		self.guide_text.setObjectName("p")
		self.guide_text.setWordWrap(True)
		self.guide_text.setStyleSheet("font-size: 15px; line-height: 1.5;")
		guide_layout.addWidget(self.guide_title)
		guide_layout.addSpacing(15)
		guide_layout.addWidget(self.guide_text)
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
		self.back_button.clicked.connect(self.on_back_clicked)
		self.next_button.clicked.connect(self.on_next_clicked)
		self.capture_button.clicked.connect(self.on_capture_clicked)
		self.upload_button.clicked.connect(self.on_upload_clicked)

	def start_camera(self, screening_type):
		self.subtitle_guide.setText(self.guides.get(screening_type, "..."))
		self.captured_pixmap = None
		self.video_display.setText("Menyalakan Kamera...")

		camera_index = 1 if screening_type == "diabetic_retinopathy" else 0

		if PICAMERA_AVAILABLE:
			try:
				self.picam = Picamera2(camera_num=camera_index)
				config = self.picam.create_preview_configuration(main={"size": (640, 480)})
				self.picam.configure(config)
				self.picam.start()
				self.capture_button.setEnabled(True)
				self.timer.timeout.connect(self.update_frame_picam)
				self.timer.start(30)
			except Exception as e:
				self.video_display.setText(f"Gagal membuka kamera: {e}")
				self.capture_button.setEnabled(False)
		else:
			self.capture = cv2.VideoCapture(camera_index)
			if not self.capture.isOpened():
				self.video_display.setText("Error: Gagal membuka kamera.")
				self.capture_button.setEnabled(False)
				return
			self.capture_button.setEnabled(True)
			self.timer.timeout.connect(self.update_frame)
			self.timer.start(30)

	def stop_camera(self):
		self.timer.stop()
		if self.capture:
			self.capture.release()
			self.capture = None
		if self.picam:
			self.picam.close()
			self.picam = None

	def update_frame_generic(self):
		if PICAMERA_AVAILABLE and self.picam:
			self.update_frame_picam()
		elif self.capture:
			self.update_frame()

	def update_frame(self):
		if not self.capture:
			return
		ret, frame = self.capture.read()
		if ret:
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
			frame = cv2.flip(frame, 1)
			h, w, ch = frame.shape
			bytes_per_line = ch * w
			q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
			pixmap = QPixmap.fromImage(q_image)
			self.video_display.setPixmap(pixmap.scaled(
				self.video_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
			))

	def update_frame_picam(self):
		if not self.picam:
			return
		frame = self.picam.capture_array()
		frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		h, w, ch = frame.shape
		bytes_per_line = ch * w
		q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
		pixmap = QPixmap.fromImage(q_image)
		self.video_display.setPixmap(pixmap.scaled(
			self.video_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
		))

	def on_capture_clicked(self):
		if PICAMERA_AVAILABLE and self.picam:
			frame = self.picam.capture_array()
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		elif self.capture and self.capture.isOpened():
			ret, frame = self.capture.read()
			if not ret:
				QMessageBox.warning(self, "Kamera Error", "Gagal mengambil gambar dari kamera.")
				return
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
			frame = cv2.flip(frame, 1)
		else:
			QMessageBox.warning(self, "Kamera Error", "Kamera tidak aktif.")
			return

		h, w, ch = frame.shape
		bytes_per_line = ch * w
		q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
		self.captured_pixmap = QPixmap.fromImage(q_image)
		self.video_display.setPixmap(self.captured_pixmap.scaled(
			self.video_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
		))
		self.stop_camera()

	def on_upload_clicked(self):
		file_path, _ = QFileDialog.getOpenFileName(self, "Pilih Gambar", "", "Image Files (*.png *.jpg *.bmp)")
		if file_path:
			self.stop_camera()
			self.captured_pixmap = QPixmap(file_path)
			if self.captured_pixmap.isNull():
				QMessageBox.warning(self, "Error", "Gagal membaca file gambar.")
				return
			self.video_display.setPixmap(self.captured_pixmap.scaled(
				self.video_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
			))

	def on_next_clicked(self):
		if not self.captured_pixmap or self.captured_pixmap.isNull():
			QMessageBox.warning(self, "Tidak Ada Gambar", "Silakan ambil atau upload gambar terlebih dahulu.")
			return
		self.imageReady.emit(self.captured_pixmap)

	def on_back_clicked(self):
		self.stop_camera()
		self.backClicked.emit()