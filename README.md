# Near Earth Object (NEO) Finder:
## Introduction
This program is written for Space App Challenge 2019 - NEOSSAT - Challenge #2 and is an
open-source project.
The software is based on python3 and the project is made by JetBrain PyCharm Community.
The main libraries need to be installed are PyQt5, astropy, pylsd, numpy, sklearn, matplotlib
and ftplib. That can be installed with this command:
$ pip3 install PyQt5, astropy, photutils, opencv-python, ocrd-fork-pylsd, numpy, sklearn,
matplotlib, ftplib
The program runs either by PyCharm or with this command in the same folder that “Finder.py”
exists (internet connection is required):
$ python3 Finder.py

## Software Flow
Software flow contains 4 sections. 1-Loading, 2-Cleaning, 3-Orbit Clustering and 4-Detection.
1. In loading section, we have 3 options:
- Using FTP address from ftp://ftp.asc-csa.gc.ca to download dataset
- By entering day of the year and the specific year to download dataset
- Load local dataset that’s been downloaded/cleaned before
Notes: For loading local datasets, it’s better to put them in the same folder that the main script
is running.
2. With FTP or DOY option, when the download progress bar completes or with local option
after selecting the folder that contains .fits files, cleaning algorithm that is developed by Jason
Rowe runs on the the raw .fits files. If there are no Dark images among .fits files, cleaning
process will pass to the next section. If not, cleaning algorithm that takes hours of time will
start (depending on the number of dark images and hardware). After cleaning .fits files, the
software automatically runs the next phase.
3. After cleaning data, we need to specify which orbit is the one that we need the detection
algorithm to run on that. Based on 3 fields of .fits headers, OBJCTRA, OBJCTDEC and
OBJCTROL, orbit cluster algorithm performs DBSCAN clustering method to differentiate orbits,
group them and present number of orbits. After selecting desired orbit, we can go for next
phase that is conversion and detection.
4. The final phase is converting cleaned .fits files that are for the selected orbit to .png files.
This is because we need to perform computer vision algorithms on these picture using
OpenCV. The result .png images are fed into detection algorithm and the final results are saved
in the same folder that the main script is running.

## Algorithm
Detection algorithm is based on merging images, subtracting single images from the merged
image and performing line detection with morphological algorithms on the result images. For
more information you can refer to main presentation in google drive folder.
