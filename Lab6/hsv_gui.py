#!/usr/bin/python3

from tkinter import Label, Scale, Image, PhotoImage, W,E, N, S, HORIZONTAL, Canvas
import tkinter as tk
import Lab6.classes.event as event
import cv2
import numpy

import Lab6.classes.grabber2 as G2
from Lab6.classes.grabber2 import Webcamera


class HsvGui(tk.Frame):
    def __init__(self, master=None,):
        tk.Frame.__init__(self, master)
        self.root = master

        self.Webcam = G2.Webcamera()
        self.baseImage = self.Webcam.save_image(persist=False)
        self.baseImage = cv2.cvtColor(numpy.array(self.baseImage), cv2.COLOR_RGB2BGR)
        self.createWidgets()
        self.OnValueChange = event.Event()

        self.title = "Webcam"

        cv2.startWindowThread()
        cv2.namedWindow(self.title, cv2.WINDOW_NORMAL)
        cv2.imshow(self.title, self.baseImage)
        self.Funkify()


    def createWidgets(self):

        Label(self.root, text="Value:").grid(row=0, sticky=W)

        Label(self.root, text="H:").grid(row=1, sticky=W)
        Label(self.root, text="S:").grid(row=2, sticky=W)
        Label(self.root, text="V:").grid(row=3, sticky=W)

        Label(self.root, text="S:").grid(row=4, sticky=W)
        Label(self.root, text="V:").grid(row=5, sticky=W)
        Label(self.root, text="H:").grid(row=6, sticky=W)


        self.valueLabel = Label(self.root, text="000-000-000 to 000-000-000")
        self.valueLabel.grid(row=0, column=1, sticky=W)

        self.Hvalue = Scale(self.root, from_=0, to=255, orient=HORIZONTAL, command=self.__sliderCallback)
        self.Hvalue.grid(row=1, column=1)
        self.Hvalue.set(0)

        self.Svalue = Scale(self.root, from_=0, to=255, orient=HORIZONTAL, command=self.__sliderCallback)
        self.Svalue.grid( row=2, column=1)
        self.Svalue.set(90)

        self.Vvalue = Scale(self.root, from_=0, to=255, orient=HORIZONTAL, command=self.__sliderCallback)
        self.Vvalue.grid( row=3, column=1)
        self.Vvalue.set(0)


        self.HvalueMax = Scale(self.root, from_=0, to=255, orient=HORIZONTAL, command=self.__sliderCallback)
        self.HvalueMax.grid(row=4, column=1)
        self.HvalueMax.set(255)

        self.SvalueMax = Scale(self.root, from_=0, to=255, orient=HORIZONTAL, command=self.__sliderCallback)
        self.SvalueMax.grid(row=5, column=1)
        self.SvalueMax.set(255)

        self.VvalueMax = Scale(self.root, from_=0, to=255, orient=HORIZONTAL, command=self.__sliderCallback)
        self.VvalueMax.grid(row=6, column=1)
        self.VvalueMax.set(120)

        self.Go = tk.Button(self.root, text="Go!", fg="Green", command=self.Funkify)
        self.Go.grid(row=7, column=0)
        self.QUIT = tk.Button(self.root, text="QUIT", fg="red", command=self.root.destroy)
        self.QUIT.grid(row=7, column=1)




    def Funkify(self):
        H = int(self.Hvalue.get())
        S = int(self.Svalue.get())
        V = int(self.Vvalue.get())
        lower = [H, S, V]

        Hmax = int(self.HvalueMax.get())
        Smax = int(self.SvalueMax.get())
        Vmax = int(self.VvalueMax.get())
        upper= [Hmax, Smax, Vmax]

        #self.valueLabel['text'] = '{0}-{1}-{2} to {3}-{4}-{5}'.format(H, S, V, Hmax, Smax, Vmax)

        output, a = self.Webcam.funkyfy(colorrange=(lower, upper))

        cv2.imshow(self.title, numpy.hstack([output, a]))


    def __sliderCallback(self, args):
        print('Sliding!!')

