import time
from PyQt5.QtCore import *

_DOWNLOAD = True


class QThreadFtpDownloader(QThread):
    progress = pyqtSignal(float)
    finished = pyqtSignal()

    def __init__(self):
        QThread.__init__(self)
        self.file_list = []
        self.ftp = 0
        self.address = ''
        self.number_of_files = 0

    def on_input(self, file_list, ftp, address, number_of_files):
        self.file_list = file_list
        self.ftp = ftp
        self.address = address
        self.number_of_files = number_of_files

    def run(self):
        for i, file_name in enumerate(self.file_list, 1):
            if _DOWNLOAD:
                with open(self.address + '/' + file_name, 'wb') as fp:
                    print(self.ftp.retrbinary('RETR ' + file_name, fp.write))
            self.progress.emit(float(i / self.number_of_files) * 100)
            time.sleep(0.05)
        self.progress.emit(100.0)
        self.finished.emit()
