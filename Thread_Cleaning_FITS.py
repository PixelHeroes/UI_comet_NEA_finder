import os
from PyQt5.QtCore import *
import numpy as np
import multiprocessing as mp
from tqdm import tqdm
from astropy.io import fits
import neossatlib as neo


class QThreadCleaning(QThread):
    progress = pyqtSignal(float)
    finished = pyqtSignal()

    def __init__(self):
        QThread.__init__(self)
        self.address = ''
        self.pbar = 0

    def on_input(self, address1, address2):
        self.address1 = address1
        self.address2 = address2
        self.file_list = sorted(os.listdir(self.address1))

    def barupdate(self, result):
        print('Bar Update', result)
        self.pbar.update()

    def run(self):
        cleaning_flag = True

        for i, file in enumerate(self.file_list, 0):
            print(self.address1 + '/' + file)
            if file[0] != '.':
                with fits.open(self.address1 + '/' + file) as hdul:
                    if int(hdul[0].header['SHUTTER'][0]) == 1:
                        print('DARK', self.address1 + '/' + file)
                        cleaning_flag = False
                        break

        if cleaning_flag:
            for i, file in enumerate(self.file_list, 0):
                print('Copying ' + self.address1 + '/' + file + ' ' + self.address2)
                os.system('cp ' + self.address1 + '/' + file + ' ' + self.address2)
                self.progress.emit(i * 100 / len(self.file_list))
        else:
            _CLEAN_SAVE_FITS = True
            _LOADING_FITS = True

            self.progress.emit(6.0)

            workdir = self.address1 + '/'  # Directory that contains FITS files (don't forget the trailing "/")
            savedir_FITS = self.address1 + "_Cleaned/"  # Directory to save cleaned images.
            # fileslist is located in 'workdir'
            fileslist = 'files.list'  # Simple text file that contains the names of all the FITS files to process.
            bpix = -1.0e10  # value to mark bad pixels. Any pixel *below* bpix is considered invalid.
            # sigscalel = 1.0  # low bounds for display clipping.  Keep small to keep background 'dark'
            # sigscaleh = 1.0  # high bounds for display clipping.
            nprocessor = 6  # Number of processors to use for data processing.
            # --- Parameters for making a Dark image ---#
            # ilow = 1  # number of low value frames to reject when generating dark image
            # ihigh = 1  # number of high value frames to reject when generating dark image
            # --- Parameters for Fourier Decomp. ---#
            snrcut = 10.0  # When to stop decomposition
            fmax = 2  # Maximum number of frequencies in model
            xoff = 0  # pixel offsets
            yoff = 0
            T = 8  # Oversampling for FFT calculations to better estimate frequency of electronic interference.
            # info = 0  # 0 - no plots, no output, 1 - no plots, output, 2 - plots, output

            if not os.path.isdir(savedir_FITS):
                os.mkdir(savedir_FITS)
            # if not os.path.isfile(workdir + fileslist):
            #     os.mknod(workdir + fileslist)
            # if not os.path.isfile(savedir_FITS + fileslist):
            #     os.mknod(savedir_FITS + fileslist)

            with open(workdir + fileslist, 'w') as namelist:
                for f in sorted(os.listdir(workdir)):
                    if '.fits' in f:
                        namelist.write('./' + f + '\n')

            with open(savedir_FITS + fileslist, 'w') as namelist2:
                for f in sorted(os.listdir(workdir)):
                    if '.fits' in f:
                        # print(workdir+f)
                        hdulist = fits.open(workdir + f)
                        shutter = hdulist[0].header['SHUTTER']
                        mode = hdulist[0].header['MODE']
                        if (int(shutter[0]) == 0) & ((int(mode[0:2]) == 16) or (int(mode[0:2]) == 13)):  # Check if shutter was open or closed. 0: open / 1: close
                            f = f.replace('.fits', '')
                            # print(f)
                            namelist2.write('./' + f + '_cord.fits' + '\n')

            imagefiles = neo.read_file_list(workdir + fileslist)

            # Use the first image to set dimensions for processing.
            i = 0  # index of first image.
            filename = workdir + imagefiles[i]
            trim, btrim, xsc, ysc, xov, yov = neo.getimage_dim(filename)

            darklist = []
            nfiles = len(imagefiles)
            icount = 0
            for i in range(nfiles):
                filename = workdir + imagefiles[i]
                hdulist = fits.open(filename)
                shutter = hdulist[0].header['SHUTTER']
                if int(shutter[0]) != 0:  # Check if shutter was open or closed.
                    darklist.append(imagefiles[i])
                hdulist.close()
                icount = icount + 1  # simple counter to track images reviewed.
            print("Number of dark images: ", len(darklist))

            self.progress.emit(10.0)
            # image = neo.read_fitsdata(workdir + darklist[1])
            #
            # # Plot Science Raster
            # imstat = neo.imagestat(image[trim[2]:trim[3], trim[0]:trim[1]], bpix)
            # neo.plot_image(image[trim[2]:trim[3], trim[0]:trim[1]], imstat, 0.1, 1.5)  # The last two parameters control the plot scale (sigma-low, sigma-high)
            #
            # # Plot Overscan Raster
            # imstat = neo.imagestat(image[btrim[2]:btrim[3], btrim[0]:btrim[1]], bpix)
            # neo.plot_image(image[btrim[2]:btrim[3], btrim[0]:btrim[1]], imstat, 0.1, 1.5)

            self.pbar = tqdm(total=len(darklist))  # Will make a progressbar to monitor processing.
            pool = mp.Pool(processes=nprocessor)  # Use lots of threads - because we can!
            results = [pool.apply_async(neo.darkprocess, args=(workdir, darkfile, xsc, ysc, xov, yov, snrcut, fmax, xoff, yoff, T,
                                                               bpix,), callback=self.barupdate) for darkfile in darklist]
            # print(np.shape(results))
            alldarkdata = [p.get() for p in results]
            pool.close()
            pool.join()

            self.progress.emit(50.0)
            # combine darks
            darkavg = neo.combinedarks(alldarkdata)

            # imstat = neo.imagestat(darkavg, bpix)
            # neo.plot_image(darkavg, imstat, 0.3, 10.0)

            # Get list of light images
            lightlist = []
            jddate = []
            exptime = []
            nfiles = len(imagefiles)
            for i in range(nfiles):
                filename = workdir + imagefiles[i]
                hdulist = fits.open(filename)
                shutter = hdulist[0].header['SHUTTER']
                mode = hdulist[0].header['MODE']
                print('MODE', mode)
                # Mode=16 => Fine point.  Mode=13 => Fine Slew
                if (int(shutter[0]) == 0) & ((int(mode[0:2]) == 16) or (int(mode[0:2]) == 13)):  # Check if shutter was open or closed.
                    lightlist.append(imagefiles[i])
                    jddate.append(float(hdulist[0].header['JD-OBS']))
                    exptime.append(float(hdulist[0].header['EXPOSURE']))
                hdulist.close()
            # jddate = np.array(jddate)
            # exptime = np.array(exptime)
            print("Number of images: ", len(lightlist))
            self.progress.emit(55.0)
            # save
            print("Saving cleaned images...")
            self.pbar = tqdm(total=len(lightlist))  # Progress bar.
            pool = mp.Pool(processes=24)  # How many threads to use.
            results = [pool.apply_async(neo.lightprocess_save, args=(workdir + lightlist[i], savedir_FITS, darkavg, xsc, ysc, xov, yov,
                                                                     snrcut, fmax, xoff, yoff, T, bpix,), callback=self.barupdate)
                       for i in range(len(lightlist))]
            # saveall = [p.get() for p in results]
            pool.close()
            pool.join()

        self.progress.emit(100.0)
        self.finished.emit()
