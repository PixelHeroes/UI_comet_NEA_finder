import os
import cv2 as cv
from pylsd import lsd
from math import sqrt
from PyQt5.QtCore import *
import numpy as np


class QThreadDetection(QThread):
    progress = pyqtSignal(float)
    finished = pyqtSignal()

    def __init__(self):
        QThread.__init__(self)
        self.file_list = []

    def on_input(self, address):
        self.address = address

    def run(self):
        _d = 19
        _noise_dilation = 11
        imageFolderName = os.path.relpath(self.address)
        print('imageFolderName', imageFolderName)

        progress_tmp = 0

        image_merge_name = imageFolderName + "_merge_v3_grey.png"  # gray
        color_image = imageFolderName + "_merge_v3_rgb.png"
        path = './' + imageFolderName
        output_folder = path + "_output"
        mask_folder = path + "_mask"
        # images = sorted(os.listdir(path))

        if not os.path.isdir(output_folder):
            os.mkdir(output_folder)
        if not os.path.isdir(mask_folder):
            os.mkdir(mask_folder)

        images = sorted(os.listdir(path))
        # print(images[0])
        # exit(0)
        dst = cv.imread(path + '/' + images[0])
        rgb = False

        if rgb == False:
            dst = cv.cvtColor(dst, cv.COLOR_RGB2GRAY)
        print(dst.shape)
        print(len(images) - 1)
        for i in range(len(images) - 1):
            tmp_progress_val = float(i * 10 / (len(images) - 1))
            print('1th tmp progress', tmp_progress_val)
            self.progress.emit(progress_tmp + tmp_progress_val)

            src = cv.imread(path + '/' + images[i + 1])
            if rgb == False:
                src = cv.cvtColor(src, cv.COLOR_RGB2GRAY)

            dst = np.maximum(src, dst)
            # if rgb:
            #     for x in range(src.shape[0]):
            #         for y in range(src.shape[1]):
            #             for c in range(src.shape[2]):
            #                 if src[x, y, c] > dst[x, y, c]:
            #                     dst[x, y, c] = src[x, y, c]
            #
            # else:
            #     for x in range(src.shape[0]):
            #         for y in range(src.shape[1]):
            #             if src[x, y] > dst[x, y]:
            #                 dst[x, y] = src[x, y]

        cv.imwrite("./" + image_merge_name, dst)
        progress_tmp += 10
        #################
        dst = cv.imread(path + '/' + images[0])
        rgb = True

        if rgb == False:
            dst = cv.cvtColor(dst, cv.COLOR_RGB2GRAY)
        print(dst.shape)
        print(len(images) - 1)
        for i in range(len(images) - 1):
            tmp_progress_val = float(i * 22 / (len(images) - 1))
            print('2th tmp progress', tmp_progress_val)
            self.progress.emit(progress_tmp + tmp_progress_val)

            src = cv.imread(path + '/' + images[i + 1])
            if rgb == False:
                src = cv.cvtColor(src, cv.COLOR_RGB2GRAY)

            dst = np.maximum(src, dst)
            # if rgb:
            #     for x in range(src.shape[0]):
            #         for y in range(src.shape[1]):
            #             for c in range(src.shape[2]):
            #                 if src[x, y, c] > dst[x, y, c]:
            #                     dst[x, y, c] = src[x, y, c]
            #
            # else:
            #     for x in range(src.shape[0]):
            #         for y in range(src.shape[1]):
            #             if src[x, y] > dst[x, y]:
            #                 dst[x, y] = src[x, y]

        cv.imwrite("./" + color_image, dst)
        progress_tmp += 22

        points1 = []
        points2 = []
        widths1 = []
        images = sorted(os.listdir(path))
        images.append(image_merge_name)

        for j, img in enumerate(images, 0):
            tmp_progress_val = float(j * 16 / len(images))
            print('3th tmp progress', tmp_progress_val)
            self.progress.emit(progress_tmp + tmp_progress_val)

            if img == image_merge_name:
                dst = cv.imread('./' + img, cv.IMREAD_GRAYSCALE)
            else:
                dst = cv.imread(path + '/' + img, cv.IMREAD_GRAYSCALE)

            # dst = cv.GaussianBlur(dst, (0, 0), 0.8)
            # cv.medianBlur(dst,median_kernel,dst)
            dst = cv.bilateralFilter(dst, 9, 35, 30)

            mask = np.zeros(dst.shape)
            lines = lsd.lsd(dst)
            # cv.imshow("image" +str(img),cv.resize(dst, (800, 800)) )

            dst = cv.cvtColor(dst, cv.COLOR_GRAY2RGB)
            for i in range(lines.shape[0]):
                # print(img)
                # if img!= image_merge_name:
                pt1 = (int(lines[i, 0]), int(lines[i, 1]))
                pt2 = (int(lines[i, 2]), int(lines[i, 3]))
                d = sqrt(pow(pt1[0] - pt2[0], 2) + pow(pt1[1] - pt2[1], 2))
                # if d > 10:#_d-4:
                # print('parnia d',d)
                width = lines[i, 4]
                cv.line(mask, pt1, pt2, (255, 255, 255), 1)
                # cv.line(mask, pt1, pt2, (255, 255, 255), int(np.ceil(width / 2)))

            cv.imwrite(mask_folder + "/mask_" + img, mask)
            # cv.imshow("lines "+img,cv.resize(mask, (800, 800)) )

        progress_tmp += 16

        print('in merge')
        images = sorted(os.listdir(mask_folder))
        # images_mask = copy.deepcopy(images)
        if "mask_" + image_merge_name in images: images.remove("mask_" + image_merge_name)
        if "mask_merged.png" in images: images.remove("mask_merged.png")
        # print(images)
        # exit(0)
        # print(images)
        # print(mask_folder+'/'+images[0])
        dst = cv.imread(mask_folder + '/' + images[0])

        dst = cv.cvtColor(dst, cv.COLOR_RGB2GRAY)
        # print(dst.shape)
        print(len(images) - 1)
        for i in range(len(images) - 1):
            tmp_progress_val = float(i * 16 / (len(images) - 1))
            print('4th tmp progress', tmp_progress_val)
            self.progress.emit(progress_tmp + tmp_progress_val)

            # if images[i+1]!=("mask_"+image_merge_name):
            #     print("************************************************","mask_"+image_merge_name)
            src = cv.imread(mask_folder + '/' + images[i + 1])

            src = cv.cvtColor(src, cv.COLOR_RGB2GRAY)

            dst = np.maximum(src, dst)
            # for x in range(src.shape[0]):
            #     for y in range(src.shape[1]):
            #         if src[x, y] > dst[x, y]:
            #             dst[x, y] = src[x, y]

        cv.imwrite(mask_folder + "/mask_merged.png", dst)
        progress_tmp += 16

        print('prepare')
        # print('dst img', mask_folder + "/mask_" + image_merge_name)
        # print('noise img', mask_folder + "/mask_merged.png")
        dst = cv.imread(mask_folder + "/mask_" + image_merge_name, cv.IMREAD_GRAYSCALE)
        noise = cv.imread(mask_folder + "/mask_merged.png", cv.IMREAD_GRAYSCALE)
        image = cv.imread(color_image)
        # _, noise = cv.threshold(noise,127,255,cv.THRESH_BINARY)
        # _, dst = cv.threshold(dst,127,255,cv.THRESH_BINARY)

        dilate_kernel = cv.getStructuringElement(cv.MORPH_RECT, (_noise_dilation, _noise_dilation))
        cv.dilate(noise, dilate_kernel, noise)

        # erode_kernel = cv.getStructuringElement(cv.MORPH_RECT, (3,3))
        # cv.erode(dst,erode_kernel,dst)

        # result = dst - noise
        # super_threshold_indices = result < 0
        # result[super_threshold_indices] = 0

        # dst= np.int32(dst)
        # noise= np.int32(noise)
        # result = dst - noise

        # print('dst', dst.shape, 'noise', noise.shape)
        result = cv.subtract(dst, noise)
        img_size = result.shape[0]
        # opening_kernel = cv.getStructuringElement(shape=cv.MORPH_RECT, ksize=(1,1))
        # result = cv.morphologyEx(np.uint8(result), cv.MORPH_OPEN, opening_kernel)

        # rect_coord_1 = int((300/2000)*img_size)
        # rect_coord_2 = img_size - int((270/2000)*img_size)
        rect_coord_1 = img_size // 40
        rect_coord_2 = img_size - img_size // 40

        found_points = []
        all_points = []
        found_d = []

        mask = np.zeros((img_size, img_size, 3))
        lines = lsd.lsd(result)
        for i in range(lines.shape[0]):
            tmp_progress_val = float(i * 16 / lines.shape[0])
            print('5th tmp progress', tmp_progress_val)
            self.progress.emit(progress_tmp + tmp_progress_val)

            pt1 = (int(lines[i, 0]), int(lines[i, 1]))
            pt2 = (int(lines[i, 2]), int(lines[i, 3]))
            width = lines[i, 4]
            # cv.line(mask, pt1, pt2, (255, 255, 255), int(np.ceil(width / 2)))
            d = sqrt(pow(pt1[0] - pt2[0], 2) + pow(pt1[1] - pt2[1], 2))

            if d > _d:

                if (rect_coord_1 < pt1[0] < rect_coord_2) and (rect_coord_1 < pt1[1] < rect_coord_2) and (rect_coord_1 < pt2[0] < rect_coord_2) and (
                        rect_coord_1 < pt2[1] < rect_coord_2):
                    # print('pt1', pt1)
                    # print('pt2', pt2)
                    print("-------> d" + str(d))

                    pt1_tmp = pt1
                    pt2_tmp = pt2

                    # for j in range(i):
                    #     pt1_tmp = (int(lines[j, 0]), int(lines[j, 1]))
                    #     pt2_tmp = (int(lines[j, 2]), int(lines[j, 3]))
                    #
                    #     if (rect_coord_1 < pt1_tmp[0] < rect_coord_2) and (rect_coord_1 < pt1_tmp[1] < rect_coord_2) and (rect_coord_1 < pt2_tmp[0] < rect_coord_2) and (rect_coord_1 < pt2_tmp[1] < rect_coord_2):
                    #
                    #         cen_org_x = (pt1[0] + pt2[0])//2
                    #         cen_org_y = (pt1[1] + pt2[1])//2
                    #
                    #         cen_tmp_x = (pt1_tmp[0] + pt2_tmp[0])//2
                    #         cen_tmp_y = (pt1_tmp[1] + pt2_tmp[1])//2
                    #
                    #         # print('center', (cen_org_x, cen_org_y), (cen_tmp_x, cen_tmp_y))
                    #
                    #         # if abs(cen_org_x - cen_tmp_x) > 5 or (abs(cen_org_x - cen_tmp_x) <= 5 and abs(cen_org_y - cen_tmp_y) > 5):
                    #         #     print('yeah')
                    #
                    #         # print('pt1', pt1_tmp)
                    #         # print('pt2', pt2_tmp)

                    # cv.circle(image, ((pt1_tmp[0] + pt2_tmp[0]) // 2, (pt1_tmp[1] + pt2_tmp[1]) // 2), int(d * 1.2), (0, 255, 0), 2)
                    found_points.append(((pt1_tmp[0] + pt2_tmp[0]) // 2, (pt1_tmp[1] + pt2_tmp[1]) // 2))
                    found_d.append(int(d * 1.2))

                    cv.line(image, pt1_tmp, pt2_tmp, (255, 255, 255), 1)
                    cv.circle(image, pt1_tmp, 1, (0, 0, 255), -1)
                    cv.circle(image, pt2_tmp, 1, (0, 0, 255), -1)

                    cv.line(mask, pt1_tmp, pt2_tmp, (255, 255, 255), 1)
                    cv.circle(mask, pt1_tmp, 1, (0, 0, 255), -1)
                    cv.circle(mask, pt2_tmp, 1, (0, 0, 255), -1)

                    all_points.append(pt1_tmp)
                    all_points.append(pt2_tmp)
                    # else:
                    #     print('no')
        progress_tmp += 16
        if len(found_points) > 0:
            all_points = np.array(all_points, dtype=np.float32)
            x, y, w, h = cv.boundingRect(all_points)

            # rotrect = cv.minAreaRect(all_points)
            # box = cv.boxPoints(rotrect)
            # box = np.int0(box)
            # cv.drawContours(image, [box], 0, (0, 255, 0), 2)

            if w > h:
                radius = w
            else:
                radius = h
            cir_pt = (int(x + w/2), int(y + h/2))
            # cv.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv.circle(image, cir_pt, radius, (0, 255, 0), 2)

            images = sorted(os.listdir(path))
            for i, img in enumerate(images, 0):
                tmp_progress_val = float(i * 16 / (len(images) - 1))
                print('6th tmp progress', tmp_progress_val)
                self.progress.emit(progress_tmp + tmp_progress_val)

                print('Updating images on Output', img)
                tmp_rgb_img = cv.imread(path + "/" + img)
                # cv.rectangle(tmp_rgb_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv.circle(tmp_rgb_img, cir_pt, radius, (0, 255, 0), 2)
                # for p in range(len(found_points)):
                #     cv.circle(tmp_rgb_img, found_points[p], found_d[p], (0, 255, 0), 2)
                cv.imwrite(output_folder + "/output-" + str(img) + ".png", tmp_rgb_img, (800, 800))

        # cv.line(image, (rect_coord_1, rect_coord_1), (rect_coord_2, rect_coord_1), (0, 0, 255), 2)
        # cv.line(image, (rect_coord_1, rect_coord_1), (rect_coord_1, rect_coord_2), (0, 0, 255), 2)
        # cv.line(image, (rect_coord_2, rect_coord_1), (rect_coord_2, rect_coord_2), (0, 0, 255), 2)
        # cv.line(image, (rect_coord_1, rect_coord_2), (rect_coord_2, rect_coord_2), (0, 0, 255), 2)

        # cv.imshow("result", cv.resize(result, (800, 800)))
        # cv.imshow("dst", cv.resize(dst, (800, 800)))
        # cv.imshow("noise", cv.resize(noise, (800, 800)))
        # cv.imshow("result mask", cv.resize(mask, (800, 800)))

        cv.imwrite(imageFolderName + "_subtracted_result.png", result, (800, 800))
        cv.imwrite(imageFolderName + "_dst.png", dst, (800, 800))
        cv.imwrite(imageFolderName + "_noise.png", noise, (800, 800))
        # image=cv.flip(image,0)
        cv.imwrite(imageFolderName + "_result_mask.png", mask, (800, 800))
        cv.imwrite(imageFolderName + "_result_image.png", image, (800, 800))

        print('Detection Process Ends.')

        # self.progress.emit(float(i / len(lightlist)) * 100)
        self.progress.emit(100.0)
        self.finished.emit()
