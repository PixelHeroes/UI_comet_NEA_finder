import os
from PyQt5.QtCore import *
from astropy.io import fits
import matplotlib.pyplot as plt
import neossatlib as neo
import numpy as np

_CONVERT_PNG = True


class QThreadPngConvert(QThread):
    progress = pyqtSignal(float)
    finished = pyqtSignal()

    def __init__(self):
        QThread.__init__(self)
        self.file_list = []

    def on_input(self, address):
        self.address = address

    def run(self):
        fileslist = 'files.list'
        savedir_FITS = self.address
        savedir_png = self.address + '_png'
        bpix = -1.0e10  # value to mark bad pixels. Any pixel *below* bpix is considered invalid.

        if not os.path.isdir(savedir_png):
            os.mkdir(savedir_png)
        with open(savedir_FITS + fileslist, 'w') as namelist:
            for f in sorted(os.listdir(savedir_FITS)):
                if '.fits' in f:
                    namelist.write('/' + f + '\n')
        imagefiles = neo.read_file_list(savedir_FITS + fileslist)
        # Use the first image to set dimensions for processing.
        i = 0  # index of first image.
        filename = savedir_FITS + imagefiles[i]
        trim, btrim, xsc, ysc, xov, yov = neo.getimage_dim(filename)
        lightlist = []
        nfiles = len(imagefiles)
        print(imagefiles)
        for i in range(nfiles):
            # filename = savedir_FITS + imagefiles[i]
            lightlist.append(imagefiles[i])

        print("Number of images to load: ", len(lightlist))

        for i in range(int(len(lightlist))):
            if _CONVERT_PNG:
                filename = savedir_FITS + lightlist[i]
                hdulist = fits.open(filename)
                shutter = hdulist[0].header['SHUTTER']
                if int(shutter[0]) == 0:
                    scidata = neo.read_fitsdata(filename)
                    sh = scidata.shape
                    strim = np.array([sh[0] - xsc, sh[0], sh[1] - ysc, sh[1]])
                    scidata_c = np.copy(scidata[strim[0]:strim[1], strim[2]:strim[3]])
                    imstat = neo.imagestat(scidata_c, bpix)

                    try:
                        neo.plot_image_exact(scidata_c, imstat, 1.0, 10.0, dpi=300)
                        plt.savefig(savedir_png + '/' + lightlist[i][1:-5] + '.png', dpi=300)
                    except Exception as e:
                        print('ERROR Converting to png ::', e)
                hdulist.close()
            self.progress.emit(float(i / len(lightlist)) * 100)
        self.progress.emit(100.0)
        self.finished.emit()
