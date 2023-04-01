from urllib import request
import locale
import sys
from turbojpeg import TurboJPEG, TJPF_GRAY, TJSAMP_GRAY, TJFLAG_PROGRESSIVE, TJFLAG_FASTUPSAMPLE, TJFLAG_FASTDCT
import numpy as np
import cv2
import requests
from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton
from PyQt6 import QtGui
from PyQt6.QtGui import QPixmap, QColor, QImage
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
# r = requests.get("http://212.26.235.210:80/axis-cgi/jpg/image.cgi?resolution=640x480")
# with open('file.jpg', 'wb') as f:
#     f.writelines(r)

class ImgThread(QThread):

    def __init__(self, ip):
        super().__init__()
        self.ip = ip
        self._run_flag = True


    def run(self):
        ...

    def stop(self):
        ...

    @pyqtSlot(str)
    def set_ip(self, ip):
        self.ip = ip

class TakeImgCV2Thread(ImgThread):
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self, ip: QLineEdit):
        super().__init__(ip)
        self.cap = None

    def run(self):
        self.cap = cv2.VideoCapture(f'http://{self.ip}/mjpg/video.mjpg')
        while self._run_flag:
            ret, frame = self.cap.read()
            if ret:
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                converted_img = QImage(img, img.shape[1], img.shape[0], QImage.Format.Format_RGB888)
                res_img = converted_img.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio)
                self.change_pixmap_signal.emit(res_img)

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.cap.release()
        self.wait()


class TakeImgThread(ImgThread):
    change_pixmap_signal = pyqtSignal(bytes)

    def __init__(self, ip):
        super().__init__(ip)

    def run(self):
        while self._run_flag:
            response = requests.get(f"http://{self.ip}/axis-cgi/jpg/image.cgi?resolution=640x480")
            self.change_pixmap_signal.emit(response.content)

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()


class App(QWidget):
    change_ip_signal1 = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Подключение к камерам")
        self.img_width = 640
        self.img_height = 480

        self.image_label = QLabel(self)
        self.image_label.resize(self.img_width, self.img_height)
        self.image_label.setPixmap(QPixmap.fromImage(QImage('noimg.jpg')))
        self.text_label1 = QLabel("Cam")
        self.ip_1 = QLineEdit()
        self.ip_1.setText('212.26.235.210')
        self.change_ip_b1 = QPushButton('Изменить')
        # self.change_ip_b1.setDisabled(True)
        self.start_b1 = QPushButton('Старт')
        self.stop_b1 = QPushButton('Стоп')
        self.stop_b1.setDisabled(True)
        self.change_ip_b1.clicked.connect(self.change_ip_b1_clicked)
        self.start_b1.clicked.connect(self.start_b1_clicked)
        self.stop_b1.clicked.connect(self.stop_b1_clicked)

        self.image_cv2_label = QLabel(self)
        self.image_cv2_label.resize(self.img_width, self.img_height)
        self.image_label.setPixmap(QPixmap.fromImage(QImage('noimg.jpg')))
        self.text_label2 = QLabel("Cam cv2")
        self.ip_2 = QLineEdit()
        self.ip_2.setText('212.26.235.210')
        # response = request.urlopen("http://212.26.235.210:80/axis-cgi/jpg/image.cgi?resolution=640x480").read()
        # response = requests.get("http://212.26.235.210:80/axis-cgi/jpg/image.cgi?resolution=640x480")

        hbox = QHBoxLayout()
        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.text_label1)
        vbox1.addWidget(self.ip_1)
        vbox1.addWidget(self.change_ip_b1)
        vbox1.addWidget(self.image_label)
        vbox1.addWidget(self.start_b1)
        vbox1.addWidget(self.stop_b1)

        vbox2 = QVBoxLayout()
        vbox2.addWidget(self.text_label2)
        vbox2.addWidget(self.ip_2)
        vbox2.addWidget(self.image_cv2_label)

        hbox.addLayout(vbox1)
        hbox.addLayout(vbox2)

        self.setLayout(hbox)

        self.thread = TakeImgThread(self.ip_1.text())
        self.thread.change_pixmap_signal.connect(self.update_img)
        self.change_ip_signal1.connect(self.thread.set_ip)

        self.thread_cv = TakeImgCV2Thread(self.ip_2.text())
        self.thread_cv.change_pixmap_signal.connect(self.update_img_cv2)
        self.thread_cv.start()

    @pyqtSlot(bytes)
    def update_img(self, img):
        px_map = QPixmap()
        px_map.loadFromData(img)
        self.image_label.setPixmap(px_map)

    @pyqtSlot(QImage)
    def update_img_cv2(self, cv_img):
        px_map = QPixmap.fromImage(cv_img)
        self.image_cv2_label.setPixmap(px_map)

    def start_b1_clicked(self):
        self.thread.start()
        self.stop_b1.setEnabled(True)
        self.change_ip_b1.setEnabled(True)
        self.start_b1.setDisabled(True)

    def stop_b1_clicked(self):
        self.thread.exit(0)
        self.start_b1.setEnabled(True)
        self.stop_b1.setDisabled(True)

    def change_ip_b1_clicked(self):
        # self.stop_b1_clicked()
        self.change_ip_signal1.emit(self.ip_1.text())
        self.start_b1_clicked()


if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')
    app = QApplication(sys.argv)
    main_window = App()
    main_window.show()
    sys.exit(app.exec())
