import requests
from PySide6.QtCore import QObject, Signal, QBuffer, QByteArray, QIODevice
from config import API_BASE_URL, API_TIMEOUT

class ApiWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, screening_type, patient_data, image_pixmap):
        super().__init__()
        self.screening_type = screening_type
        self.patient_data = patient_data
        self.image_pixmap = image_pixmap

    def run(self):
        try:
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.WriteOnly)

            if not self.image_pixmap.save(buffer, "PNG"):
                self.error.emit("Gagal mengkonversi gambar ke format PNG.")
                return

            api_url = f"{API_BASE_URL}/api/{self.screening_type}"
            form_data = self.patient_data.copy()
            files = {'image': ('screening.png', byte_array.data(), 'image/png')}

            response = requests.post(api_url, data=form_data, files=files, timeout=API_TIMEOUT)
            response.raise_for_status()

            result = response.json()
            self.finished.emit(result)

        except requests.exceptions.Timeout:
            self.error.emit("Permintaan timeout. Pastikan server API sedang berjalan dan jaringan stabil.")
        except requests.exceptions.ConnectionError:
            self.error.emit(f"Gagal terhubung ke server. Periksa URL API: {API_BASE_URL}")
        except requests.exceptions.HTTPError as e:
            self.error.emit(f"Server error (HTTP {e.response.status_code}): {e.response.text}")
        except ValueError:
            self.error.emit("Respons server bukan JSON yang valid.")
        except Exception as e:
            self.error.emit(f"Terjadi error: {str(e)}")