import tkinter as tk
from datetime import time

import serial
from tkinter import *
import time

serialPort = serial.Serial(
    port="COM11", baudrate=115200, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE
)

root = tk.Tk()


# Channels: 20 30 40 50 60 70

def send(channel, pictureNum, brightness):
    byte1 = int((channel / 10 - 2) + 144)
    byte2 = pictureNum
    byte3 = int((channel / 10 - 2) + 224)
    byte4 = brightness
    byte5 = 0
    serialPort.write(chr(byte1).encode('latin_1'))
    serialPort.write(chr(byte2).encode('latin_1'))
    serialPort.write(chr(byte3).encode('latin_1'))
    serialPort.write(chr(byte4).encode('latin_1'))
    serialPort.write(chr(byte5).encode('latin_1'))
    print("byte1 = " + str(byte1))
    print("byte2 = " + str(byte2))
    print("byte3 = " + str(byte3))
    print("byte4 = " + str(byte4))
    print("byte5 = " + str(byte5))
    print("Channel select: " + str(ch_select.get()))


channel = [20, 30, 40, 50, 60, 70]


def send_1():
    if ch_select.get() == -1:  # Select all (-1)
        send(20, inputvar.get(), bslider.get())
        send(30, inputvar.get(), bslider.get())
        send(40, inputvar.get(), bslider.get())
        send(50, inputvar.get(), bslider.get())
        send(60, inputvar.get(), bslider.get())
        send(70, inputvar.get(), bslider.get())
        #time.sleep(0.25)

    else:
        send(ch_select.get(), inputvar.get(), bslider.get())  # Select single Channel


def send_off():
    if ch_select.get() == -1:  # Select all (-1)
        send(20, 0, 0)
        send(30, 0, 0)
        send(40, 0, 0)
        send(50, 0, 0)
        send(60, 0, 0)
        send(70, 0, 0)
    else:
        send(ch_select.get(), 0, 0)


def input_inc():
    tmp = inputvar.get()
    tmp = tmp + 1
    inputvar.set(tmp)
    send_1()


def input_dec():
    tmp = inputvar.get()
    if tmp > 0:
        tmp = tmp - 1
    inputvar.set(tmp)
    send_1()


ch_select = tk.IntVar()

# Input Picture Nr.
inputlabel = tk.Label(root, bg="white", text="Select Picture Nr.", anchor="n")
inputlabel.grid(row=1, column=1)
inputvar = tk.IntVar()
inputbox = tk.Entry(root, textvariable=inputvar, width=10)
inputvar.set('0')
inputbox.grid(row=2, column=1, sticky="s", padx=20)

# Radiobuttons Channel
for ch in channel:
    radiob = tk.Radiobutton(root, text=ch, value=ch, variable=ch_select)
    radiob.grid(row=int(ch / 10 + 3), column=1)  # row 4 - 9
radio_all = tk.Radiobutton(root, text="all", value=-1, variable=ch_select)
radio_all.grid(row=11, column=1)
ch_select.set(20)  # setdefault to CH 20

# Title/Labels
title = tk.Label(root, bg="yellow", text="Remote Control LED Poi")
title.grid(row=0, column=1)
channel = tk.Label(root, bg="white", text="Select Channel")
channel.grid(row=4, column=1)
# Buttons
button1 = tk.Button(root, text="Send", highlightthickness="20", command=send_1)
button1.grid(row=1, column=2)
button2 = tk.Button(root, text="Off", highlightthickness="20", command=send_off)
button2.grid(row=2, column=2)
buttonplus = tk.Button(root, bg="white", text="+", anchor="w", command=input_inc)
buttonplus.grid(row=2, column=1, sticky="ne")
buttonminus = tk.Button(root, bg="white", text="-", anchor="e", command=input_dec)
buttonminus.grid(row=2, column=1, sticky="nw", padx=10)
buttonExit = tk.Button(root, text="Exit", command=root.destroy)
buttonExit.grid(row=12, column=3)
# Slider brightness
brightlabel = tk.Label(root, bg="white", text="Brightness", anchor="n")
brightlabel.grid(row=3, column=2)
bslider = tk.Scale(root, from_=0, to=8, orient=HORIZONTAL)
bslider.grid(row=4, column=2)
bslider.set(1)  # default
root.mainloop()
