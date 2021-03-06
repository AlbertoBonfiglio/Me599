#!/usr/bin/python3

import io
import matplotlib.pyplot as plt
import numpy
import uuid
import cv2


from collections import Counter
from datetime import datetime
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps, ImageMath
from urllib.request import urlopen # fix for Python3
from time import time, mktime, sleep, localtime

import Lab6.classes.event as event
from Lab6.classes.grabber import Webcam
from Lab6.classes.utils import get_closest_colour
from Lab6.classes.filter import FilterHelper


colors = ['chartreuse', 'darkgreen', 'darkolivegreen','darkseagreen'
'darkturquoise','forestgreen','green'
,'greenyellow'
,'lawngreen'
,'lightgreen'
,'lightseagreen'
,'lime'
,'limegreen'
,'mediumseagreen'
,'mediumspringgreen'
,'olive'
,'olivedrab'
,'palegoldenrod'
,'palegreen'
,'seagreen'
,'springgreen'
,'yellowgreen']

# Interface to the Oregon State University webcams.  This should work
# with any web-enabled AXIS camera system.
class Webcamera(Webcam):

    #TODO calculate the right threshold
    __daylightThreshold = 75

    def __init__(self):
        super(Webcamera, self).__init__()
        self.history = []
        self.colors = ImageColors()

        self.filter = FilterHelper()
        self.OnCapture = event.Event()
        self.OnCaptureComplete = event.Event()


    def capture(self, duration=10, delay=0.01, persist=False):
        try:
            self.history = []

            _start = time()
            _running = True
            while _running:
                args = []
                _filename = str(uuid.uuid4()) + '.jpg'
                _image = self.save_image(_filename, persist)
                _intensity = self.image_average_intensity(_image)
                _daylight = self.daytime(_intensity)
                _mcc = self.image_most_common_colour(_image)
                _size = (_image.height * _image.width)

                _image_data = WebImage(_filename, _intensity, _daylight,  _mcc, _size, localtime(), delay)
                self.history.append(_image_data)

                _elapsed = (time() - _start)

                args.append(_elapsed)
                args.append(localtime())
                args.append(_image_data)

                self.OnCapture(self, args)

                if _elapsed >= duration: _running = False

                #TODO add save and read back capability

            self.OnCaptureComplete(self, None)
        except Exception as ex:
            print(ex)


    def save_image(self, filename=None, persist=True):
        try:
            if filename == None: filename = str(uuid.uuid4()) + '.jpg'

            _image = urlopen('{0}/axis-cgi/jpg/image.cgi'.format(self.url)).read()
            # convert directly to an Image instead of saving / reopening
            # thanks to SO: http://stackoverflow.com/a/12020860/377366
            _image = Image.open(io.BytesIO(_image))
            if persist:
                _image.save(filename)

            return _image

        except Exception as ex:
            print(ex)


    def image_average_intensity(self, image):
        try:
            pixels = numpy.array(image.getdata())
            return numpy.mean(pixels)

        except Exception as ex:
            print(ex)


    def image_most_common_colour(self, image):
        try:
            pixels = image.getdata()
            colours = Counter(pixels).most_common(1) #Handy Python function for counting occurences.

            rgb = colours[0][0]
            frequency = colours[0][1]
            name = get_closest_colour(rgb)

            return (rgb, frequency, name, (frequency/len(pixels)))

        except Exception as ex:
            print(ex)


    def daytime(self, intensity=0):
        return intensity >= self.__daylightThreshold


    def plot_history_intensity(self):
        try:
            caption = 'average intensity over time'
            with plt.xkcd():
                fig, ax = plt.subplots(nrows=2, ncols=1, sharex=False, sharey=False,  tight_layout=True, figsize=(9, 4.5))
                fig.suptitle(caption,  fontsize=18, fontweight='bold')

                x = [datetime.fromtimestamp(mktime(wimage.time)) for wimage in self.history]

                y = [wimage.intensity for wimage in self.history]
                #ax.set_xticklabels(x, fontsize='small')
                ax[0].plot(x, y)

                y1 = self.filter.filterData(y, 5)
                ax[1].plot(x, y1)

            plt.show()
        except Exception as ex:
            print(ex)


    def __image_rotate(self, image, angle=180):
        (h, w) = image.shape[:2]
        image_center = (w / 2, h / 2)

        # rotate the image by 180 degrees
        rotation_matrix = cv2.getRotationMatrix2D(image_center, angle, 1.0)
        rotated = cv2.warpAffine(image, rotation_matrix, (w, h))

        return rotated


    def __preprocess_image(self, image, ratio=0.75, blur=21):
        #resize to make things a bit faster, convert to grayscale,
        # and apply some gaussian blur to reduce aliasing and pixel differences
        _image = image.resize((int(image.width*ratio), int(image.height*ratio)))
        _image = cv2.GaussianBlur(_image, (blur, blur), 0)

        return _image


    def funkyfy(self, image=None, colorrange=([0,100,0],[255, 255,120]), useopencv=True):
        #Not the most elegant solution
        try:
            if colorrange ==None:
                colorrange = ([numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)],
                              [numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)])

            if image == None:
                image = self.save_image(persist=False) #gets a webcam image

            image = image.resize((int(image.width*0.5), int(image.height*0.5)))

            image_bgr = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)
            image_bgr = self.__image_rotate(image_bgr, 2)

            lower = numpy.array(colorrange[0], dtype="uint8")
            upper = numpy.array(colorrange[1], dtype="uint8")

            mask = cv2.inRange(image_bgr, lower, upper)
            output = cv2.bitwise_and(image_bgr, image_bgr, mask = mask)

            b, g, r = cv2.split(output)
            g[g>0] = 255

            output = cv2.merge((g,b,r))

            for row in range(130, len(output)):
                for col in range(len(output[row])):
                    tup = (output[row][col])
                    if any(v != 0 for v in tup):
                        image_bgr[row][col] = tup


            image_bgr = self.__image_rotate(image_bgr, -2)
            return image_bgr, output
        except Exception as ex:
            print(ex)



    #TODO finetune mincontour,
    # Gets two images and calculates the difference in pixels
    def detect_motion(self, interval=0.5):
        min_contour_area = 5
        max_contour_area = 1250
        retval = False
        threshold = 65
        try:
            #TODO write code to change static image if night
            _image_static = None
            _image_static = self.save_image(persist=False)
            _image_static = cv2.cvtColor(numpy.array(_image_static), cv2.COLOR_RGB2GRAY)
            _image_static = cv2.GaussianBlur(_image_static, (21, 21), 0)
            sleep(interval) #defaults to one second

            _image_dynamic = self.save_image(persist=False)
            _image_dynamic = cv2.cvtColor(numpy.array(_image_dynamic), cv2.COLOR_RGB2GRAY)
            _image_dynamic1 = cv2.GaussianBlur(_image_dynamic, (21, 21), 0)

            # ideas from http://docs.opencv.org/master/d4/d73/tutorial_py_contours_begin.html#gsc.tab=0
            _delta = cv2.absdiff(_image_dynamic1, _image_static)

            _threshold = cv2.threshold(_delta, 25, 255, cv2.THRESH_BINARY)[1]

            # dilate the thresholded image to fill in holes, then find contour on thresholded image
            _threshold = cv2.dilate(_threshold, None, iterations=2)

            #TODO evaluate different parameters
            (img, contours, _) = cv2.findContours(_threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            #(img, contours, _) = cv2.findContours(_threshold.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            # loop over the contours
            for contour in contours:
                # if the contour is too small, ignore it
                _area = cv2.contourArea(contour)
                if _area < min_contour_area or _area > max_contour_area:
                    continue  # skip to the next

                # compute the bounding box for the contour, draw it on the frame,
                retval = True
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(_image_dynamic, (x, y), (x + w, y + h), (0, 12, 255), 2)
                #cv2.ellipse(_image_dynamic, (x, y+20), (10, 20), 90, 0, 360, (255, 0, 0), 2)
                #cv2.ellipse(_image_dynamic1,(200,200),(80,50),45,0,360,(0,0,255),1)

                # draw the text and timestamp on the frame
                #cv2.putText(_image_dynamic1, "Motion: {}".format(text), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                #cv2.putText(_image_dynamic1, datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"), (10, _image_dynamic1.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
            return retval, _image_dynamic

        except Exception as ex:
            print(ex)


    def detect_motion_new(self, winName, interval=1):
        #Implemented after talking with Dr Smart about image averaging and background extraction

        min_contour_area = 25
        max_contour_area = 1250
        retval = False
        threshold = 65
        try:
            _image_static = None
            _image_static = self.save_image(persist=False)
            _image_static = cv2.cvtColor(numpy.array(_image_static), cv2.COLOR_RGB2GRAY)
            _image_static = cv2.GaussianBlur(_image_static, (21, 21), 0)

            accumulator = numpy.float32(_image_static)
            while True:
                sleep(interval)
                _image_static = self.save_image(persist=False)
                _image_static = cv2.cvtColor(numpy.array(_image_static), cv2.COLOR_RGB2GRAY)
                _image_static = cv2.GaussianBlur(_image_static, (21, 21), 0)

                cv2.accumulateWeighted(numpy.float32(_image_static), accumulator, 0.1)

                _image_static = cv2.convertScaleAbs(accumulator)

                _image_dynamic = self.save_image(persist=False)
                _image_dynamic1 = cv2.cvtColor(numpy.array(_image_dynamic), cv2.COLOR_RGB2GRAY)
                _image_dynamic1 = cv2.GaussianBlur(_image_dynamic1, (21, 21), 0)

                # ideas from http://docs.opencv.org/master/d4/d73/tutorial_py_contours_begin.html#gsc.tab=0
                _delta = cv2.absdiff(_image_dynamic1, _image_static)

                _threshold = cv2.threshold(_delta, 17, 255, cv2.THRESH_BINARY)[1]
                # dilate the thresholded image to fill in holes, then find contour on thresholded image
                _threshold = cv2.dilate(_threshold, None, iterations=5)

                (img, contours, _) = cv2.findContours(_threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                dyn = cv2.cvtColor(numpy.array(_image_dynamic), cv2.COLOR_RGB2GRAY)
                # loop over the contours
                for contour in contours:
                    # if the contour is too small, ignore it
                    _area = cv2.contourArea(contour)
                    if _area < min_contour_area: # or _area > max_contour_area:
                        continue  # skip to the next

                    # compute the bounding box for the contour, draw it on the frame,

                    (x, y, w, h) = cv2.boundingRect(contour)
                    #cv2.rectangle(dyn, (x, y), (x + w, y + h), (0, 12, 255), 2)
                    cv2.ellipse(dyn, (x+5, y+25), (10, 20), 90, 0, 360, (255, 0, 0), 2)

                cv2.imshow(winName, numpy.hstack([dyn, _threshold]))

                key = cv2.waitKey(10)
                if key == 27:
                    cv2.destroyWindow(winName)
                    break

        except Exception as ex:
            print(ex)

    #TODO detect Event
    def detect_event(self):
        crop_coord = (180, 320, 555, 490)
        min_contour_area = 1000
        max_contour_area = 3000
        event_count = 0
        threshold = 65

        try:
            #convert to grayscale,
            # and apply some gaussian blur to reduce aliasing (see wikipedia)
            _image_dynamic = Image.open('event_day.jpg').crop(crop_coord) #self.save_image(persist=False).crop(crop_coord)
            _image_dynamic = self.__preprocess_image(_image_dynamic, 1)

            _image_static = Image.open('nopeeps_day.jpg').crop(crop_coord)
            _image_static = self.__preprocess_image(_image_static, 1)

            # ideas from http://docs.opencv.org/master/d4/d73/tutorial_py_contours_begin.html#gsc.tab=0
            _delta = cv2.absdiff(_image_dynamic, _image_static)
            #cv2.imshow('delta', _delta)
            _threshold = cv2.threshold(_delta, 25, 255, cv2.THRESH_BINARY)[1]

            #cv2.imshow('thres', _threshold)

            # dilate the thresholded image to fill in holes, then find contour on thresholded image
            _threshold = cv2.dilate(_threshold, None, iterations=2)

            (img, contours, _) = cv2.findContours(_threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # loop over the contours
            text = 'None'
            for contour in contours:
                # if the contour is too small, ignore it
                _area = cv2.contourArea(contour)
                if _area < min_contour_area or _area > max_contour_area:
                    continue # skip to the next

                # compute the bounding box for the contour, draw it on the frame,
                event_count +=1
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(_image_dynamic, (x, y), (x + w, y + h), (0, 255, 0), 2)
                text = "Detected"

                # draw the text and timestamp on the frame
            return (event_count > 0), event_count, _image_dynamic

        except Exception as ex:
            print(ex)





class WebImage(object):
    def __init__(self, id, intensity, daytime, most_common, size, ctime, interval):
        self.id = id
        self.intensity = intensity
        self.daytime = daytime

        self.most_common = most_common
        self.size = size
        self.time = ctime
        self.interval = interval


    def most_common_rgb(self):
        return self.most_common[0]

    def most_common_frequency(self):
        return self.most_common[1]

    def most_common_name(self):
        return self.most_common[3]

    def most_common_percent(self):
        return self.most_common[4]


class ImageColor(object):
    def __init__(self, name, hex, rgb, luminosity, hue, saturation, light, palette, group ):
        self.name = name
        self.hex = hex
        self.rgb = rgb
        self.luminosity = luminosity
        self.hue = hue
        self.saturation = saturation
        self. light = light
        self.palette = palette
        self.group = group


class ImageColors(object):
    def __init__(self):
        self.colors = []





