import locale
import pprint
import sys
import os
from typing import Generator, Iterable
import cv2
from PyQt6.QtWidgets import QWidget, QApplication, QLabel,\
    QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListWidget, \
    QSpinBox, QComboBox
from PyQt6.QtGui import QPixmap, QColor, QImage
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QSize
import HtmlParser.HtmlParser as hparser
from threading import Thread
from MQueue import Queue
from time import time
import mysql.connector
from mysql.connector import Error


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

        self.text_label1 = QLabel("Камера 1")
        #
        self.text_label2 = QLabel("Камера 2")

        self.ip_cb1 = QComboBox()
        self.ip_cb1.setDisabled(True)
        self.ip_cb1.currentIndexChanged.connect(self.ip_cb1_changed)
        # 2
        self.ip_cb2 = QComboBox()
        self.ip_cb2.setDisabled(True)
        self.ip_cb2.currentIndexChanged.connect(self.ip_cb2_changed)

        self.ip_1 = QLineEdit()
        self.ip_1.setText('85.158.74.11')
        # 2
        self.ip_2 = QLineEdit()
        self.ip_2.setText('85.158.74.11')

        self.change_ip_b1 = QPushButton('Изменить')
        self.change_ip_b1.setDisabled(True)
        self.change_ip_b1.clicked.connect(self.change_ip_b1_clicked)
        # 2
        self.change_ip_b2 = QPushButton('Изменить')
        self.change_ip_b2.setDisabled(True)
        self.change_ip_b2.clicked.connect(self.change_ip_b2_clicked)

        self.list_w1 = QListWidget()
        self.list_w1.addItem('Без обработки')
        self.list_w1.setCurrentRow(0)
        # 2
        self.list_w2 = QListWidget()
        self.list_w2.addItem('Без обработки')
        self.list_w2.setCurrentRow(0)

        self.image_label1 = QLabel(self)
        self.image_label1.resize(self.img_width, self.img_height)
        self.image_label1.setPixmap(QPixmap.fromImage(QImage('noimg.jpg')))
        # 2
        self.image_label2 = QLabel(self)
        self.image_label2.resize(self.img_width, self.img_height)
        self.image_label2.setPixmap(QPixmap.fromImage(QImage('noimg.jpg')))

        self.start_b1 = QPushButton('Старт')
        self.start_b1.clicked.connect(self.start_b1_clicked)
        # 2
        self.start_b2 = QPushButton('Старт')
        self.start_b2.clicked.connect(self.start_b2_clicked)

        self.stop_b1 = QPushButton('Стоп')
        self.stop_b1.setDisabled(True)
        self.stop_b1.clicked.connect(self.stop_b1_clicked)
        # 2
        self.stop_b2 = QPushButton('Стоп')
        self.stop_b2.setDisabled(True)
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
        vbox1.addWidget(self.ip_cb1)
        vbox1.addWidget(self.ip_1)
        vbox1.addWidget(self.list_w1)
        vbox1.addWidget(self.change_ip_b1)
        vbox1.addWidget(self.image_label1)
        vbox1.addWidget(self.start_b1)
        vbox1.addWidget(self.stop_b1)

        vbox2 = QVBoxLayout()
        vbox2.addWidget(self.text_label2)
        vbox2.addWidget(self.ip_cb2)
        vbox2.addWidget(self.ip_2)
        vbox2.addWidget(self.list_w2)
        vbox2.addWidget(self.change_ip_b2)
        vbox2.addWidget(self.image_label2)
        vbox2.addWidget(self.start_b2)
        vbox2.addWidget(self.stop_b2)
        
        hbox.addLayout(vbox1)
        hbox.addLayout(vbox2)

        main_box = QVBoxLayout()

        self.url = "http://insecam.org/ru/bytype/Axis/"
        self.pages = hparser.parse_pages(self.url)
        self.main_label = QLabel(f"Парсинг IP-адресов с сайта: {self.url} \
        Найдено страниц c камерами: {self.pages}")
        main_box.addWidget(self.main_label)

        threads_box = QHBoxLayout()

        self.threads_label = QLabel('Количество потоков')
        self.threads_label.setFixedSize(QSize(150, 20))
        threads_box.addWidget(self.threads_label)

        self.th_spinbox = QSpinBox()
        self.th_spinbox.setMinimum(3)
        self.th_spinbox.setValue(3)
        self.th_spinbox.setFixedSize(QSize(60, 20))
        threads_box.addWidget(self.th_spinbox)

        self.start_label = QLabel('Страницы с')
        self.start_label.setFixedSize(QSize(100, 20))
        threads_box.addWidget(self.start_label)

        self.start_spin = QSpinBox()
        self.start_spin.setMaximum(self.pages)
        self.start_spin.setFixedSize(QSize(60, 20))
        self.start_spin.setValue(1)
        threads_box.addWidget(self.start_spin)

        self.end_label = QLabel(' до ')
        self.end_label.setFixedSize(30, 20)
        threads_box.addWidget(self.end_label)

        self.end_spin = QSpinBox()
        self.end_spin.setMaximum(self.pages)
        self.end_spin.setFixedSize(QSize(60, 20))
        self.end_spin.setValue(self.pages)
        threads_box.addWidget(self.end_spin)

        main_box.addLayout(threads_box)

        self.ip_search_b = QPushButton('Начать поиск')
        self.ips_dict = {}
        self.queue = Queue(3)
        self.stats_queue = Queue(3)
        self.ip_search_b.clicked.connect(self.start_search_b_clicked)
        main_box.addWidget(self.ip_search_b)

        main_box.addLayout(hbox)
        self.setLayout(main_box)
        self.thread = None
        self.thread_cv2 = None

        self.create_table = """
        CREATE TABLE ip_search_stats (
          thread_id INT PRIMARY KEY,
          pages_cnt INT,
          time DOUBLE
          );
         """
        self.host = 'localhost'
        self.user_name = 'root'
        self.password = 'ArtemKo21'
        self.db_name = 'threads'
        self.db_connection = self.create_db_connection()
        self.execute_query('DROP TABLE ip_search_stats')
        self.execute_query(self.create_table)

    def create_db_connection(self):
        connection = None
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user_name,
                passwd=self.password,
                database=self.db_name
            )
            # print("MySQL Database connection successful")
        except Error as err:
            print(f"Error: '{err}'")

        return connection

    def execute_query(self, query):
        cursor = self.db_connection.cursor()
        try:
            cursor.execute(query)
            self.db_connection.commit()
            # print("Query successful")
        except Error as err:
            print(f"Error: '{err}'")

    def closeEvent(self, event):  # Вызывается при закрытии окна
        self.hide()  # Скрываем окно
        if self.thread:
            self.thread.terminate()
            self.thread.wait(5000)
        if self.thread_cv2:
            self.thread_cv2.terminate()
            self.thread_cv2.wait(5000)
        event.accept()  # Закрываем окно

    def execute_thread_query(self, thread_id, count, _time):
        cursor = self.db_connection.cursor()
        query = f"""INSERT INTO ip_search_stats(thread_id, pages_cnt, time)
               VALUES('{thread_id}', '{count}', '{_time}');"""
        try:
            cursor.execute(query)
            self.db_connection.commit()
        except Error as err:
            print(f"Error: '{err}'")

    @staticmethod
    def get_ranges(start, stop, threads):
        delta = stop - start + 1
        ranges = [[start + i*delta//threads, start + (i+1)*delta//threads] for i in range(threads)]
        # print(ranges)
        return ranges

    def search_ips(self, p_range, i):
        time_start = time()
        start, stop = p_range
        for page in range(start, stop):
            self.queue.put(hparser.parse_ips_from_page(self.url, page))
        proc_time = time() - time_start
        # print(proc_time)
        self.queue.task_done()
        # self.stats_queue.put((i, time() - time_start, stop - start))
        # self.stats_queue.task_done()
        Thread(target=self.execute_thread_query, args=(i, stop - start, proc_time), daemon=False).start()

    def start_search_b_clicked(self):
        threads = self.th_spinbox.value()
        ranges = self.get_ranges(self.start_spin.value(), self.end_spin.value(), threads)
        print(ranges)
        self.queue = Queue(threads)
        # self.stats_queue = Queue(threads)
        for i in range(self.th_spinbox.value()):
            Thread(target=self.search_ips, args=(ranges[i], i), daemon=True).start()
        self.queue.join()
        for _ in range(self.end_spin.value() - self.start_spin.value() + 1):
            ips = self.queue.get()
            self.ips_dict.update(ips)
        # for _ in range(threads):
        #     print(self.stats_queue.get())
        self.ip_cb1.addItems(self.ips_dict.keys())
        self.ip_cb2.addItems(self.ips_dict.keys())
        self.ip_cb1.setEnabled(True)
        self.ip_cb2.setEnabled(True)
        self.ip_search_b.setText(f'Поиск завершен. Найдено {len(self.ips_dict)} адресов')

    @pyqtSlot(QImage)
    def update_img1(self, img):
        px_map = QPixmap.fromImage(img)
        self.image_label1.setPixmap(px_map)

    @pyqtSlot(QImage)
    def update_img2(self, cv_img):
        px_map = QPixmap.fromImage(cv_img)
        self.image_label2.setPixmap(px_map)

    def ip_cb1_changed(self, index):
        self.ip_1.setText(self.ip_cb1.currentText())

    def ip_cb2_changed(self, index):
        self.ip_2.setText(self.ip_cb2.currentText())

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
    main_window.move(15, 30)
    sys.exit(app.exec())
