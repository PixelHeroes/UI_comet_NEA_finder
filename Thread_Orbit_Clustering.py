import os
from PyQt5.QtCore import *
from astropy.io import fits


class QThreadOrbitCluster(QThread):
    progress = pyqtSignal(float)
    backup = pyqtSignal(tuple)
    finished = pyqtSignal(tuple)
    file_names = pyqtSignal(list)

    def __init__(self):
        QThread.__init__(self)
        self.file_list = []
        self.ftp = 0
        self.address = ''
        self.number_of_files = 0

    def on_input(self, address, file_list, dark_addr):
        self.file_list = file_list
        self.address = address
        self.number_of_files = len(file_list)
        self.dark_addr = dark_addr

    def run(self):
        # filter_name = ['SIMPLE', 'T']
        filter_name = ['MODE', 'FINE_POINT']
        # filter_name = ['SHUTTER', 'open']

        orbits_b = []
        orbits_data = []
        orbitd_file_list = []
        dark_file_addrr = []
        for i, file_name in enumerate(self.file_list, 0):
            try:
                with fits.open(self.address + '/' + file_name) as hdul:
                    # orbit_number = float(hdul[0].header['OBJCTROL'])

                    # t = file_name.find('.')
                    # hour = int(file_name[(t - 6):(t - 4)])
                    # minute = int(file_name[(t - 4):(t - 2)])
                    # second = int(file_name[(t - 2):t])
                    # orbit_number = (hour * 3600) + (minute * 60) + second
                    # orbits_b.append(orbit_number)
                    # orbits_data.append((str(hdul[0].header['CCD-TEMP']), str(hdul[0].header['OBJCTRA']),
                    #                     str(hdul[0].header['OBJCTDEC']), str(hdul[0].header['OBJCTROL'])))

                    if int(hdul[0].header['SHUTTER'][0]) == 1:
                        os.system('cp ' + self.address + '/' + file_name + ' ' + self.dark_addr)

                    if str(hdul[0].header[filter_name[0]]).find(filter_name[1]) >= 0:
                            # and (float(hdul[0].header['LENDELAY']) > 0.1):
                        orbitd_file_list.append(self.address + '/' + file_name)
                        orbit_number = float(hdul[0].header['OBJCTROL'])
                        orbits_b.append(orbit_number)
                        orbits_data.append((str(hdul[0].header['CCD-TEMP']), str(hdul[0].header['OBJCTRA']),
                                            str(hdul[0].header['OBJCTDEC']), str(hdul[0].header['OBJCTROL']),
                                            str(hdul[0].header['OBJECT'])))
                        print(file_name, 'MODE', hdul[0].header['MODE'])
                        print(file_name, 'CMD', hdul[0].header['CMD'])
                        print(file_name, 'SHUTTER', hdul[0].header['SHUTTER'])
                        print(file_name, 'OBJECT', hdul[0].header['OBJECT'])
                        print(file_name, 'CCD-TEMP', hdul[0].header['CCD-TEMP'])
                        print(file_name, 'OBJCTRA', str(hdul[0].header['OBJCTRA']).split(' '))
                        print(file_name, 'OBJCTDEC', str(hdul[0].header['OBJCTDEC']).split(' '))
                        print(file_name, 'OBJCTROL', float(hdul[0].header['OBJCTROL']))
                        print()
                    else:
                        print('===> Removed', file_name, filter_name[0], hdul[0].header[filter_name[0]])
            except Exception as e:
                print('ERROR, QThreadOrbitCluster ::', e)
            self.progress.emit(float(i / self.number_of_files) * 95)
        self.progress.emit(95.0)
        self.backup.emit(tuple(orbits_data))
        self.file_names.emit(orbitd_file_list)
        self.finished.emit(tuple(orbits_b))
