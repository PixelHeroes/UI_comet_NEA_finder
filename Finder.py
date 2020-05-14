import os
import sys
import cv2
import time
import pickle
import socket
import datetime
import numpy as np
from ftplib import FTP
from PyQt5 import QtWidgets
from MainWindow import Ui_MainWindow
from PyQt5.QtCore import *
import matplotlib
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from Thread_FTP_Downloader import QThreadFtpDownloader
from Thread_Cleaning_FITS import QThreadCleaning
from Thread_Orbit_Clustering import QThreadOrbitCluster
from Thread_Convert2PNG import QThreadPngConvert
from Thread_Detection import QThreadDetection
from Thread_Copy import QThreadCopy


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.ftp = FTP('ftp.asc-csa.gc.ca')
        self.file_list = []
        self.number_of_files = 0
        self.thread_ftp_downloader = QThreadFtpDownloader()
        self.thread_cleaning = QThreadCleaning()
        self.thread_orbit_cluster = QThreadOrbitCluster()
        self.thread_png_convert = QThreadPngConvert()
        self.thread_detection = QThreadDetection()
        self.thread_copy = QThreadCopy()
        self.ftp_selected_year = 0
        self.ftp_selected_doy = 0
        self.all_orbits = []
        self.orbit_first_sample_num = []
        self.all_orbits_backup = []
        self.all_orbits_data = []
        self.all_orbits_file_names = []
        self.all_orbits_number = 0

        # self.thread_ftp_downloader.finished.connect(self.cleaning_function())
        self.thread_orbit_cluster.finished.connect(self.orbit_cluster_plot)
        self.thread_orbit_cluster.file_names.connect(self.orbit_cluster_save_file_names)
        self.thread_orbit_cluster.backup.connect(self.orbit_cluster_backup)
        # self.thread_png_convert.data_to_save.connect(self.save_png_converted_function)
        self.txt_download_addr.setText(os.getcwd())
        self.pb_change_download_addr.clicked.connect(self.on_change_addr_click)
        self.pb_download.clicked.connect(self.on_download_click)
        self.pb_load_cleaned.clicked.connect(self.on_load_cleaned_click)
        self.pb_convert_png.clicked.connect(self.save_png_function)
        self.pb_detect.clicked.connect(self.on_detect_click)
        self.cb_year.currentIndexChanged.connect(self.on_year_selected)
        self.cb_orbit_number.currentIndexChanged.connect(self.on_orbit_selected)
        self.rb_ftp.toggled.connect(self.set_download_mode_ftp)
        self.rb_doy.toggled.connect(self.set_download_mode_doy)
        self.rb_doy.setFocus(True)
        self.rb_doy.click()
        self.rb_local.toggled.connect(self.set_download_mode_local)
        self.pb_load_cleaned.setVisible(False)
        self.pb_detect.setVisible(False)
        self.lbl_cleaned_addr.setVisible(False)
        self.pb_detect.setEnabled(True)
        # self.pbar_download.setEnabled(False)
        self.tb_orbits.setItem(0, 0, QtWidgets.QTableWidgetItem(''))
        self.tb_orbits.setItem(0, 1, QtWidgets.QTableWidgetItem(''))
        self.tb_orbits.setItem(0, 2, QtWidgets.QTableWidgetItem(''))
        self.tb_orbits.setItem(0, 3, QtWidgets.QTableWidgetItem(''))

        self.initialize()

        # self.lbl_cleaned_addr.setText('Survey_Cleaned_2019_292')
        # self.on_detect_click()

    def initialize(self):
        print(self.ftp.login())
        self.ftp.cwd('users/OpenData_DonneesOuvertes/pub/NEOSSAT/ASTRO/')
        year_list = sorted(self.ftp.nlst())
        print(year_list)
        self.cb_year.clear()
        self.cb_year.addItems(year_list)
        self.cb_year.setCurrentIndex(2)

    def set_all_widgets_enable(self, state):
        self.chb_raw.setEnabled(state)
        # self.chb_auto.setEnabled(state)
        self.rb_ftp.setEnabled(state)
        self.rb_doy.setEnabled(state)
        self.rb_local.setEnabled(state)
        self.pb_download.setEnabled(state)
        self.pb_change_download_addr.setEnabled(state)
        self.pb_convert_png.setEnabled(state)
        self.cb_year.setEnabled(state)
        self.cb_doy.setEnabled(state)
        self.pb_detect.setEnabled(state)
        self.cb_orbit_number.setEnabled(state)

    def orbit_cluster_save_file_names(self, file_list):
        self.all_orbits_file_names = file_list

    def on_detect_click(self):
        self.thread_detection.on_input(self.lbl_cleaned_addr.text() + '_Orbit_' + self.cb_orbit_number.currentText() + '_png')
        self.thread_detection.progress.connect(self.detection_progress_fn)
        self.thread_detection.start()
        self.set_all_widgets_enable(False)

    def save_png_function(self):
        matplotlib.use('Agg')
        self.thread_png_convert.on_input(self.lbl_cleaned_addr.text() + '_Orbit_' + self.cb_orbit_number.currentText())  # , self.all_orbits_file_names[sum(self.orbit_first_sample_num[0:t]):sum(self.orbit_first_sample_num[0:t+1])])
        self.thread_png_convert.progress.connect(self.convert_progress_fn)
        self.thread_png_convert.start()
        self.set_all_widgets_enable(False)

    def orbit_cluster_backup(self, backup):
        self.all_orbits_backup = list(backup)
        print('Orbits Backup Data', self.all_orbits_backup)

    def orbit_cluster_plot(self, orbits):
        orbits = list(orbits)
        self.all_orbits = orbits
        print('Orbits', orbits)
        with open(self.lbl_cleaned_addr.text().split('/')[-1] + '-Orbits.pickle', 'wb') as f:
            pickle.dump(orbits, f)

        # plt.plot(orbits, 'bo')
        # plt.ylabel('Number of orbits')
        # plt.show()

        X = np.array([[i, orbits[i]] for i in range(len(orbits))])
        X = StandardScaler().fit_transform(X)

        # #############################################################################
        # Compute DBSCAN
        db = DBSCAN(eps=0.3, min_samples=10).fit(X)
        core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
        core_samples_mask[db.core_sample_indices_] = True
        labels = db.labels_

        # Number of clusters in labels, ignoring noise if present.
        n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise_ = list(labels).count(-1)

        if n_clusters_:
            print('Estimated number of orbits: %d' % n_clusters_)
        else:
            print('Estimated number of clusters: 1')
        print('Estimated number of noise points: %d' % n_noise_)

        # Black removed and is used for noise instead.
        unique_labels = set(labels)
        colors = [plt.cm.Spectral(each) for each in np.linspace(0, 1, len(unique_labels))]
        legend_number = 0
        legend_plot = []
        self.orbit_first_sample_num = []
        for k, col in zip(unique_labels, colors):
            if k == -1:
                # Black used for noise.
                col = [0, 0, 0, 1]
            legend_number += 1
            class_member_mask = (labels == k)

            xy = X[class_member_mask & core_samples_mask]
            self.orbit_first_sample_num.append(len(xy[:, 0]))
            l, = plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=tuple(col),
                     markeredgecolor='k', markersize=14, label=str(legend_number))
            legend_plot.append(l)

            xy = X[class_member_mask & ~core_samples_mask]
            plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=tuple(col),
                     markeredgecolor='k', markersize=6)
        plt.legend(handles=legend_plot)
        self.all_orbits_number = legend_number

        for i in range(legend_number):
            if not os.path.isdir(self.lbl_cleaned_addr.text() + '_Orbit_' + str(i+1)):
                os.mkdir(self.lbl_cleaned_addr.text() + '_Orbit_' + str(i+1))
            tmp_arr = self.all_orbits_file_names[sum(self.orbit_first_sample_num[0:i]):sum(self.orbit_first_sample_num[0:i+1])]

            # tmp_file_list = []
            # for j in tmp_arr:
            #     tmp_file_list.append(j + ' ' + self.lbl_cleaned_addr.text() + '_Orbit_' + str(i+1))
            # self.thread_copy.on_input()
            # self.thread_copy.progress.connect(self.copy_progress_fn)
            # self.thread_copy.start()

            for c, j in enumerate(tmp_arr, 0):
                os.system('cp ' + j + ' ' + self.lbl_cleaned_addr.text() + '_Orbit_' + str(i+1))

                # value = 80.0 + ((i * c * 100) / (legend_number * len(tmp_arr)))
                # self.pbar_orbit.setValue(int(value))
                # tmp = "%.1f" % value
                # self.lbl_orbit.setText(tmp + '%')
                # print("%f%% Read" % value)
                # time.sleep(0.1)

            self.all_orbits_data.append(self.all_orbits_backup[sum(self.orbit_first_sample_num[0:i])])
            print(i + 1, 'th Orbit Sample Data', self.all_orbits_backup[sum(self.orbit_first_sample_num[0:i])])

        if legend_number == 1:
            if not os.path.isdir(self.lbl_cleaned_addr.text() + '_Orbit_1'):
                os.mkdir(self.lbl_cleaned_addr.text() + '_Orbit_1')
            for j in self.all_orbits_file_names:
                os.system('cp ' + j + ' ' + self.lbl_cleaned_addr.text() + '_Orbit_1')

        self.cb_orbit_number.clear()
        self.cb_orbit_number.addItems([str(i + 1) for i in range(legend_number)])
        # 0 temp - 1 ra - 2 dec - 3 rol
        self.tb_orbits.setItem(0, 0, QtWidgets.QTableWidgetItem(self.all_orbits_data[0][0]))
        self.tb_orbits.setItem(0, 1, QtWidgets.QTableWidgetItem(self.all_orbits_data[0][1]))
        self.tb_orbits.setItem(0, 2, QtWidgets.QTableWidgetItem(self.all_orbits_data[0][2]))
        self.tb_orbits.setItem(0, 3, QtWidgets.QTableWidgetItem(self.all_orbits_data[0][3]))
        self.tb_orbits.setItem(0, 4, QtWidgets.QTableWidgetItem(self.all_orbits_data[0][4]))

        value = 100.0
        self.pbar_orbit.setValue(int(value))
        tmp = "%.1f" % value
        self.lbl_orbit.setText(tmp + '%')
        print("%f%% Read" % value)

        self.pb_convert_png.setEnabled(True)
        self.cb_orbit_number.setFocus(True)
        self.set_all_widgets_enable(True)

        if n_clusters_ == 0:
            n_clusters_ = 1
        plt.title('Estimated Number of Orbits: %d' % n_clusters_)
        plt.show()

    def on_orbit_selected(self):
        self.tb_orbits.setItem(0, 0, QtWidgets.QTableWidgetItem(self.all_orbits_data[self.cb_orbit_number.currentIndex()][0]))
        self.tb_orbits.setItem(0, 1, QtWidgets.QTableWidgetItem(self.all_orbits_data[self.cb_orbit_number.currentIndex()][1]))
        self.tb_orbits.setItem(0, 2, QtWidgets.QTableWidgetItem(self.all_orbits_data[self.cb_orbit_number.currentIndex()][2]))
        self.tb_orbits.setItem(0, 3, QtWidgets.QTableWidgetItem(self.all_orbits_data[self.cb_orbit_number.currentIndex()][3]))
        self.tb_orbits.setItem(0, 4, QtWidgets.QTableWidgetItem(self.all_orbits_data[self.cb_orbit_number.currentIndex()][4]))

    def set_download_mode_ftp(self):
        if self.rb_ftp.isChecked():
            self.txt_download_addr.setText('users/OpenData_DonneesOuvertes/pub/NEOSSAT/ASTRO/')
            # self.chb_raw.setVisible(False)
            self.pb_download.setVisible(True)
            # self.chb_auto.setVisible(True)
            self.cb_year.setVisible(False)
            self.cb_doy.setVisible(False)
            self.lbl_year.setVisible(False)
            self.lbl_doy.setVisible(False)
            self.pb_change_download_addr.setVisible(False)

    def set_download_mode_doy(self):
        if self.rb_doy.isChecked():
            self.txt_download_addr.setText(os.getcwd())
            self.pb_download.setVisible(True)
            # self.chb_auto.setVisible(True)
            self.cb_year.setVisible(True)
            self.cb_doy.setVisible(True)
            self.lbl_year.setVisible(True)
            self.lbl_doy.setVisible(True)
            self.pb_change_download_addr.setVisible(True)

    def set_download_mode_local(self):
        if self.rb_local.isChecked():
            self.txt_download_addr.setText('')
            self.pb_download.setVisible(False)
            # self.chb_auto.setVisible(False)
            self.cb_year.setVisible(False)
            self.cb_doy.setVisible(False)
            self.lbl_year.setVisible(False)
            self.lbl_doy.setVisible(False)
            self.pb_change_download_addr.setVisible(True)

    def detection_progress_fn(self, value):
        if value == 100:
            self.set_all_widgets_enable(True)
        self.pbar_detect.setValue(int(value))
        tmp = "%.1f" % value
        self.lbl_detect.setText(tmp + '%')
        print("%f%% Detection Completed" % value)

    def convert_progress_fn(self, value):
        if value == 100:
            self.pb_detect.setEnabled(True)
            self.set_all_widgets_enable(True)
            self.on_detect_click()
        self.pbar_convert_png.setValue(int(value))
        tmp = "%.1f" % value
        self.lbl_convert.setText(tmp + '%')
        print("%f%% Converted" % value)

    def orbit_progress_fn(self, value):
        # if value == 80:
        #     self.set_all_widgets_enable(True)
        self.pbar_orbit.setValue(int(value))
        tmp = "%.1f" % value
        self.lbl_orbit.setText(tmp + '%')
        print("%f%% Read" % value)

    def cleaning_progress_fn(self, value):
        if value == 100:
            self.set_all_widgets_enable(True)
            self.orbit_clustering_function()
        self.pbar_cleaning.setValue(int(value))
        tmp = "%.1f" % value
        self.lbl_cleaning.setText(tmp + '%')
        print("%f%% Cleaning" % value)

    def download_progress_fn(self, value):
        if value == 100:
            self.set_all_widgets_enable(True)
            if not os.path.isdir(self.lbl_cleaned_addr.text()):
                os.mkdir(self.lbl_cleaned_addr.text())
            # self.orbit_clustering_function()
            if self.rb_doy.isChecked():
                self.thread_cleaning.on_input(self.txt_download_addr.text() + '/Survey_' +
                    self.cb_year.currentText() + '_' + self.cb_doy.currentText() + '_AutoDownload', self.lbl_cleaned_addr.text())
            elif self.rb_ftp.isChecked():
                self.thread_cleaning.on_input('./Survey_' + str(self.ftp_selected_year) + '_' + str(self.ftp_selected_doy) + '_AutoDownload', self.lbl_cleaned_addr.text())
            self.thread_cleaning.progress.connect(self.cleaning_progress_fn)
            self.thread_cleaning.start()
            self.set_all_widgets_enable(False)
        self.pbar_download.setValue(int(value))
        tmp = "%.1f" % value
        self.lbl_download.setText(tmp + '%')
        print("%f%% Downloaded" % value)

    def print_output(self, s):
        print(s)

    @pyqtSlot()
    def on_change_addr_click(self):
        folder_addr = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.txt_download_addr.setText(folder_addr)
        if len(folder_addr) > 0 and self.rb_local.isChecked():
            self.lbl_cleaned_addr.setText(folder_addr)
            self.pbar_download.setValue(100.0)
            self.lbl_download.setText('100.0%')
            self.pbar_cleaning.setValue(100.0)
            self.lbl_cleaning.setText('100.0%')
            # self.orbit_clustering_function()
            self.thread_cleaning.on_input(self.txt_download_addr.text(), self.lbl_cleaned_addr.text())
            self.thread_cleaning.progress.connect(self.cleaning_progress_fn)
            self.thread_cleaning.start()
            self.set_all_widgets_enable(False)

    @pyqtSlot()
    def on_download_click(self):
        should_start = False
        if self.rb_ftp.isChecked():
            try:
                print('Start to download ...')
                self.lbl_download.setText('0.0%')
                self.pbar_download.setValue(0)
                if self.txt_download_addr.text().find('ftp://ftp.asc-csa.gc.ca/') >= 0:
                    self.txt_download_addr.setText(self.txt_download_addr.text()[len('ftp://ftp.asc-csa.gc.ca/'):])
                self.ftp.cwd('/')
                self.ftp.cwd(self.txt_download_addr.text())
                should_start = True
                tmp = self.txt_download_addr.text().split('/')
                found = False
                for i, folders in enumerate(tmp, 0):
                    # print(folders, i, '20' in folders, len(folders))
                    if ('20' in folders) and len(folders) == 4:
                        found = True
                        break
                if found:
                    self.ftp_selected_year = tmp[i]
                    self.ftp_selected_doy = tmp[i + 1]
                    print('Year', self.ftp_selected_year, ', Day of Year', self.ftp_selected_doy)
                else:
                    self.ftp_selected_year = str(time.asctime().split(' ')[-1])
                    self.ftp_selected_doy = str(datetime.datetime.now().timetuple().tm_yday)
                    print('Year', self.ftp_selected_year, ', Day of Year', self.ftp_selected_doy)
            except Exception as e:
                print('ERROR, on_download_click True ::', e)
                self.txt_download_addr.setText('users/OpenData_DonneesOuvertes/pub/NEOSSAT/ASTRO/')
        elif self.rb_doy.isChecked():
            try:
                print('Start to download ...')
                self.lbl_download.setText('0.0%')
                self.pbar_download.setValue(0)
                self.cb_year.setEnabled(False)
                self.cb_doy.setEnabled(False)
                self.pbar_download.setEnabled(True)
                self.ftp.cwd(self.cb_doy.currentText())
                should_start = True
            except Exception as e:
                print('ERROR, on_download_click False ::', e)

        if should_start:
            if self.rb_ftp.isChecked():
                self.lbl_cleaned_addr.setText('./Survey_' + str(self.ftp_selected_year) + '_' + str(self.ftp_selected_doy) + '_Cleaned')
                print('ftp', self.lbl_cleaned_addr.text())
            elif self.rb_doy.isChecked():
                self.lbl_cleaned_addr.setText(self.txt_download_addr.text() + '/Survey_' + self.cb_year.currentText() + '_' + self.cb_doy.currentText() + '_Cleaned')
                print('doy', self.lbl_cleaned_addr.text())
            all_file_list = self.ftp.nlst()
            # print(len(all_file_list), sorted(all_file_list))
            self.file_list = []
            for file in all_file_list:
                if self.chb_raw.isChecked():
                    if file.find('clean') < 0 and file.find('cor') < 0:
                        self.file_list.append(file)
                else:
                    self.file_list.append(file)
            self.file_list = sorted(self.file_list)
            print(self.file_list)
            self.number_of_files = len(self.file_list)
            print('Going to download', self.number_of_files, 'File(s)')

            if self.rb_ftp.isChecked():
                tmp_folder = './Survey_' + str(self.ftp_selected_year) + '_' + str(self.ftp_selected_doy) + '_AutoDownload'
                if not os.path.isdir(tmp_folder):
                    os.mkdir(tmp_folder)
                self.thread_ftp_downloader.on_input(self.file_list, self.ftp, tmp_folder, self.number_of_files)
            elif self.rb_doy.isChecked():
                tmp_folder = self.txt_download_addr.text() + '/Survey_' + \
                                 self.cb_year.currentText() + '_' + self.cb_doy.currentText() + '_AutoDownload'
                if not os.path.isdir(tmp_folder):
                    os.mkdir(tmp_folder)
                self.thread_ftp_downloader.on_input(self.file_list, self.ftp, tmp_folder, self.number_of_files)
            self.thread_ftp_downloader.progress.connect(self.download_progress_fn)
            self.thread_ftp_downloader.start()
            self.set_all_widgets_enable(False)

    @pyqtSlot()
    def on_year_selected(self):
        try:
            try:
                self.ftp.cwd(self.cb_year.currentText())
            except Exception as e:
                print('ERROR, on_year_selected, ftp.cwd ::', e)
                # self.ftp.cwd('..')
                self.ftp.cwd('/')
                self.ftp.cwd('users/OpenData_DonneesOuvertes/pub/NEOSSAT/ASTRO/')
                self.ftp.cwd(self.cb_year.currentText())
            day_list = sorted(self.ftp.nlst())
            print(day_list)
            self.cb_doy.clear()
            self.cb_doy.addItems(day_list)
            self.cb_doy.setCurrentText('306')  # TODO remove this line
        except Exception as e:
            print('ERROR, on_year_selected ::', e)
            self.rb_ftp.setChecked(True)

    def on_load_cleaned_click(self):
        pass
        # folder_addr = str(QtWidgets.QFileDialog.getExistingDirectory())
        # if len(folder_addr):
        #     self.lbl_cleaned_addr.setText(folder_addr)
        #     self.orbit_clustering_function()

    def orbit_clustering_function(self):
        matplotlib.use('MacOSX')
        self.lbl_orbit.setText('0.0%')
        self.pbar_orbit.setValue(0)

        file_list = os.listdir(self.lbl_cleaned_addr.text())
        file_list = sorted(file_list)
        print(len(file_list), file_list)

        if not os.path.isdir(self.lbl_cleaned_addr.text() + '_Dark/'):
            os.mkdir(self.lbl_cleaned_addr.text() + '_Dark/')
        self.thread_orbit_cluster.on_input(self.lbl_cleaned_addr.text(), file_list, self.lbl_cleaned_addr.text() + '_Dark/')
        self.thread_orbit_cluster.progress.connect(self.orbit_progress_fn)
        self.thread_orbit_cluster.start()
        self.set_all_widgets_enable(False)

        print('Orbit Cluster Started')


def is_connected():
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        pass
    return False


if not is_connected():
    print('Connection to Internet is NOT Established!!!')
    exit(0)

app = QtWidgets.QApplication(sys.argv)

window = MainWindow()
window.show()
app.exec()



