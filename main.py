import locale
import sys
import os
import numpy as np
from typing import Generator, Iterable
import cv2
import requests
from PyQt6.QtWidgets import QWidget, QApplication, QLabel,\
    QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListWidget
from PyQt6.QtGui import QPixmap, QColor, QImage
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QThread

PATH_WITH_PLUGINS = 'plugins'


class TakeImgCV2Thread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self, ip, func):
        super().__init__()
        self.ip = ip
        self.func = func
        self._run_flag = True
        self.cap = None

    def run(self):
        self.cap = cv2.VideoCapture(f'http://{self.ip}/mjpg/video.mjpg')
        while self._run_flag:
            ret, frame = self.cap.read()
            if ret:
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (640, 480))
                if self.func:
                    self.func(img)
                converted_img = QImage(img, img.shape[1], img.shape[0], QImage.Format.Format_RGB888)
                res_img = converted_img.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio)
                self.change_pixmap_signal.emit(res_img)

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self.cap.release()
        self._run_flag = False
        self.wait()


class App(QWidget):
    change_ip_signal1 = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Подключение к камерам")
        self.img_width = 640
        self.img_height = 480

        self.image_label1 = QLabel(self)
        self.image_label1.resize(self.img_width, self.img_height)
        self.image_label1.setPixmap(QPixmap.fromImage(QImage('noimg.jpg')))
        self.text_label1 = QLabel("Cam")
        self.ip_1 = QLineEdit()
        self.ip_1.setText('85.158.74.11')
        self.change_ip_b1 = QPushButton('Изменить')
        self.change_ip_b1.setDisabled(True)
        self.list_w1 = QListWidget()
        self.list_w1.addItem('Без обработки')
        self.list_w1.setCurrentRow(0)
        self.start_b1 = QPushButton('Старт')
        self.stop_b1 = QPushButton('Стоп')
        self.stop_b1.setDisabled(True)
        self.change_ip_b1.clicked.connect(self.change_ip_b1_clicked)
        self.start_b1.clicked.connect(self.start_b1_clicked)
        self.stop_b1.clicked.connect(self.stop_b1_clicked)

        self.image_label2 = QLabel(self)
        self.image_label2.resize(self.img_width, self.img_height)
        self.image_label2.setPixmap(QPixmap.fromImage(QImage('noimg.jpg')))
        self.text_label2 = QLabel("Cam cv2")
        self.ip_2 = QLineEdit()
        self.ip_2.setText('85.158.74.11')
        self.list_w2 = QListWidget()
        self.list_w2.addItem('Без обработки')
        self.list_w2.setCurrentRow(0)
        self.change_ip_b2 = QPushButton('Изменить')
        self.change_ip_b2.setDisabled(True)
        self.start_b2 = QPushButton('Старт')
        self.stop_b2 = QPushButton('Стоп')
        self.stop_b2.setDisabled(True)
        self.change_ip_b2.clicked.connect(self.change_ip_b2_clicked)
        self.start_b2.clicked.connect(self.start_b2_clicked)
        self.stop_b2.clicked.connect(self.stop_b2_clicked)

        self.REQUIRED_FIELDS = ['NAME', 'VERSION', 'AUTHOR', 'CAPTION', 'edit_img']
        files = self.get_py_files()
        modules = self.get_modules(files)
        self.funcs_list = [None]
        self.plugins = list(self.check_plugins(modules))
        for plugin in self.plugins:
            self.list_w1.addItem(plugin.CAPTION)
            self.list_w2.addItem(plugin.CAPTION)
            self.funcs_list.append(plugin.edit_img)

        hbox = QHBoxLayout()
        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.text_label1)
        vbox1.addWidget(self.ip_1)
        vbox1.addWidget(self.list_w1)
        vbox1.addWidget(self.change_ip_b1)
        vbox1.addWidget(self.image_label1)
        vbox1.addWidget(self.start_b1)
        vbox1.addWidget(self.stop_b1)

        vbox2 = QVBoxLayout()
        vbox2.addWidget(self.text_label2)
        vbox2.addWidget(self.ip_2)
        vbox2.addWidget(self.list_w2)
        vbox2.addWidget(self.change_ip_b2)
        vbox2.addWidget(self.image_label2)
        vbox2.addWidget(self.start_b2)
        vbox2.addWidget(self.stop_b2)
        
        hbox.addLayout(vbox1)
        hbox.addLayout(vbox2)

        self.setLayout(hbox)
        self.thread = None
        self.thread_cv2 = None

    @pyqtSlot(QImage)
    def update_img1(self, img):
        px_map = QPixmap.fromImage(img)
        self.image_label1.setPixmap(px_map)

    @pyqtSlot(QImage)
    def update_img2(self, cv_img):
        px_map = QPixmap.fromImage(cv_img)
        self.image_label2.setPixmap(px_map)

    def start_b1_clicked(self):
        self.thread = TakeImgCV2Thread(self.ip_1.text(),
                                       self.funcs_list[self.list_w1.currentRow()])
        self.thread.change_pixmap_signal.connect(self.update_img1)
        self.thread.start()
        self.stop_b1.setEnabled(True)
        self.change_ip_b1.setEnabled(True)
        self.start_b1.setDisabled(True)

    def stop_b1_clicked(self):
        self.thread.terminate()
        self.start_b1.setEnabled(True)
        self.stop_b1.setDisabled(True)

    def change_ip_b1_clicked(self):
        self.stop_b1_clicked()
        self.start_b1_clicked()

    def start_b2_clicked(self):
        self.thread_cv2 = TakeImgCV2Thread(self.ip_2.text(),
                                            self.funcs_list[self.list_w2.currentRow()])
        self.thread_cv2.change_pixmap_signal.connect(self.update_img2)
        self.thread_cv2.start()
        self.stop_b2.setEnabled(True)
        self.change_ip_b2.setEnabled(True)
        self.start_b2.setDisabled(True)

    def stop_b2_clicked(self):
        self.thread_cv2.terminate()
        self.start_b2.setEnabled(True)
        self.stop_b2.setDisabled(True)

    def change_ip_b2_clicked(self):
        self.stop_b2_clicked()
        self.start_b2_clicked()

    def get_py_files(self) -> Generator[str, None, None]:
        """Получаем все файлы из папки"""
        for file in os.listdir(PATH_WITH_PLUGINS):
            # Отбрасываем все файлы, которые заканчиваются не на .py
            if file[-3:] != '.py':
                continue
            yield file[:-3]

    def get_modules(self, files: Iterable[str]) -> Generator[object, None, None]:
        """Получаем модули из файлов"""
        for file in files:
            module = __import__(f'{PATH_WITH_PLUGINS}.{file}')
            module = getattr(module, file)
            # Если в модуле нет класса Plugin, пропускаем
            if not hasattr(module, 'Plugin'):
                print(file, 'Модуль не имеет класса Plugin')
                continue
            yield getattr(module, 'Plugin')()

    def check_plugins(self, modules: Iterable[object]):
        """Проверяем, чтоб в модуле были нужные переменные и функции"""
        for module in modules:
            print(dir(module))

            # Если хоть какого-то эллемента из массива REQUIRED_FIELDS нет - пропускаем
            if not all([hasattr(module, field) for field in self.REQUIRED_FIELDS]):
                print(module, 'Модуль не имеет нужных полей')
                continue
            yield module


if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')
    app = QApplication(sys.argv)
    main_window = App()
    main_window.show()
    sys.exit(app.exec())
