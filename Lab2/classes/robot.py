#!/usr/bin/python3

from Lab2.classes.sensor import generate_sensor_data, print_sensor_data
import numpy
import Lab2.classes.utils as utils

class Robot(object):

    def __init__(self):
        self.data = None

    def getSensorReadings(self, n=1000, noise=0.05):
        self.data = generate_sensor_data(n, noise)
        return self.data


    def printSensorData(self, data, filename):
        print_sensor_data(data, filename)


    def null_filter(self, data, width=0):
        filtered = []
        for datum in data:
            filtered.append(datum)

        return filtered


    def filterData(self, data, window=1, usemedian=False, usenumpy=False):
        if (window < 1): window = 1

        func = self.__getfilterFunction(usemedian, usenumpy)
        filtered = []
        width = int((window-1) /2)
        lenData = len(data)-1

        for n in range(lenData):
            if n <= (width):  #
                l = data[0:n+1]
                r = data[n+1:(n+width)+1]
                dataslice = l+r

            elif n >= (lenData - width):
                dataslice = data[n-width-1:lenData+1:]

            else:
                dataslice = data[n-width-1:n+width]

            datum = func(dataslice)
            filtered.append(datum)

        return filtered


    def __getfilterFunction(self, usemedian=False, usenumpy=False):
        if usenumpy == True:
            if usemedian == True:
                func = numpy.median
            else:
                func = numpy.mean
        else:
            if usemedian == True:
                func = utils.median
            else:
                func = utils.mean

        return func

