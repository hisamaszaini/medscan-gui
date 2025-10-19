from PySide6.QtWidgets import QMainWindow, QStackedWidget
from PySide6.QtCore import Slot
from PySide6.QtGui import QPixmap

# Import halaman
from pages.home_page import HomePage
from pages.screening_menu_page import ScreeningMenuPage
from pages.input_data_page import InputDataPage
from pages.image_capture_page import ImageCapturePage
from pages.screening_result_page import ScreeningResultPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MedScan AI Screening")
        self.setGeometry(100, 100, 1280, 900)

        # State Aplikasi
        self.current_screening_type = None
        self.current_patient_data = None

        # Router
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.init_pages()
        self.connect_signals()

        self.stacked_widget.setCurrentIndex(0)

    def init_pages(self):
        self.home_page = HomePage()
        self.menu_page = ScreeningMenuPage()
        self.input_page = InputDataPage()
        self.capture_page = ImageCapturePage()
        self.result_page = ScreeningResultPage()

        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.menu_page)
        self.stacked_widget.addWidget(self.input_page)
        self.stacked_widget.addWidget(self.capture_page)
        self.stacked_widget.addWidget(self.result_page)

    def connect_signals(self):
        self.home_page.startClicked.connect(self.navigate_to_menu)
        self.menu_page.startScreening.connect(self.on_screening_selected)
        self.menu_page.goBack.connect(self.navigate_to_home)
        self.input_page.dataSubmitted.connect(self.on_data_submitted)
        self.input_page.backClicked.connect(self.navigate_to_menu)
        self.capture_page.imageReady.connect(self.on_image_ready)
        self.capture_page.backClicked.connect(self.on_capture_back)
        self.result_page.goHomeClicked.connect(self.navigate_to_home_and_reset)

    @Slot()
    def navigate_to_home(self):
        self.stacked_widget.setCurrentIndex(0)

    @Slot()
    def navigate_to_home_and_reset(self):
        self.input_page.reset_form()
        self.stacked_widget.setCurrentIndex(0)

    @Slot()
    def navigate_to_menu(self):
        self.capture_page.stop_camera()
        self.stacked_widget.setCurrentIndex(1)

    @Slot(str)
    def on_screening_selected(self, screening_type: str):
        self.current_screening_type = screening_type
        self.stacked_widget.setCurrentIndex(2)

    @Slot(dict)
    def on_data_submitted(self, patient_data: dict):
        self.current_patient_data = patient_data
        self.stacked_widget.setCurrentIndex(3)
        self.capture_page.start_camera(self.current_screening_type)

    @Slot()
    def on_capture_back(self):
        self.stacked_widget.setCurrentIndex(2)

    @Slot(QPixmap)
    def on_image_ready(self, captured_pixmap: QPixmap):
        self.stacked_widget.setCurrentIndex(4)
        self.result_page.start_analysis(
            self.current_screening_type,
            self.current_patient_data,
            captured_pixmap
        )

    def closeEvent(self, event):
        """Memastikan resource dibersihkan saat aplikasi ditutup."""
        self.capture_page.stop_camera()
        if self.result_page.api_thread and self.result_page.api_thread.isRunning():
            self.result_page.api_thread.quit()
            self.result_page.api_thread.wait()
        event.accept()
