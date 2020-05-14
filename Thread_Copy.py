import os
from PyQt5.QtCore import *
from astropy.io import fits


class QThreadCopy(QThread):
    progress = pyqtSignal(float)

    def __init__(self):
        QThread.__init__(self)
        self.file_list = []

    def on_input(self, file_list):
        self.file_list = file_list

    def run(self):
        for i, file_addr in enumerate(self.file_list, 0):
            print('Copying', file_addr)

            self.progress.emit(float(i / self.number_of_files) * 90)
        self.progress.emit(100.0)
