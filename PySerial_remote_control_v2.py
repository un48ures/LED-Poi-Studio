import time
import tkinter as tk
from tkinter import ttk
import threading

import serial
from tkinter import *

# Find connected Ports for Arduino
import serial.tools.list_ports as port_list

root = tk.Tk()
root.title("Remote Control LED Poi Sticks")

# Channels: 20 30 40 50 60 70
receiver_ids = [1, 2, 3, 4, 5, 6]

# Protocol:
# 1.byte - mode
# 2.byte - receiver_id
# 3.byte - picture/hue
# 4.byte - saturation
# 5.byte - brightness/value
# 6.byte - velocity

# Send bytes
def send(mode, receiver_id, picture, hue, saturation, brightness_value, velocity):
    byte1 = mode
    byte2 = receiver_id
    byte3 = picture
    byte4 = hue
    byte5 = saturation
    byte6 = brightness_value
    byte7 = velocity
    starttime_SP_write = time.time_ns()
    serialPort.write(
        chr(byte1).encode('latin_1') + chr(byte2).encode('latin_1') + chr(byte3).encode('latin_1') +
        chr(byte4).encode('latin_1') + chr(byte5).encode('latin_1') + chr(byte6).encode('latin_1') + chr(byte7).encode(
            'latin_1'))
    # msg = chr(byte1).encode('latin_1') + chr(byte2).encode('latin_1') + chr(byte3).encode('latin_1') + chr(byte4).encode('latin_1') + chr(byte5).encode('latin_1') + chr(byte6).encode('latin_1')
    # serialPort.write(msg)

    print("byte1 = " + str(byte1) + "(Mode)")
    print("byte2 = " + str(byte2) + "(receiver_id)")
    print("byte3 = " + str(byte3) + "(picture/hue)")
    print("byte4 = " + str(byte4) + "(saturation)")
    print("byte5 = " + str(byte5) + "(brightness/value)")
    print("byte6 = " + str(byte6) + "(velocity)")
    print("Receiver select: " + str(receiver_select.get()))

    # Wait until there is data waiting in the serial buffer
    if serialPort.in_waiting > 50:

        # Read data out of the buffer until a carriage return / new line is found
        serialString = serialPort.readline()
        res = serialString.decode("Ascii").split()
        # print("after readLine")

        # Print the contents of the serial data
        try:
            inputb1.set(res[0] + "V")
            inputb2.set(res[1] + "V")
            inputb3.set(res[2] + "V")
            inputb4.set(res[3] + "V")
            inputb5.set(res[4] + "V")
            inputb6.set(res[5] + "V")
            inputss1.set(res[6] + "%")
            inputss2.set(res[7] + "%")
            inputss3.set(res[8] + "%")
            inputss4.set(res[9] + "%")
            inputss5.set(res[10] + "%")
            inputss6.set(res[11] + "%")
        except:
            pass
    print("Duration for serial port write and receive: " + str(
        (time.time_ns() - starttime_SP_write) / 1000000) + " ms")

def send_single_all():
    if receiver_select.get() == -1:  # Select all (-1)
        send(mode_select.get(), receiver_ids[0], input_picture.get(), hslider.get(), sslider.get(), bslider.get(), vslider.get())
        send(mode_select.get(), receiver_ids[1], input_picture.get(), hslider.get(), sslider.get(), bslider.get(), vslider.get())
        send(mode_select.get(), receiver_ids[2], input_picture.get(), hslider.get(), sslider.get(), bslider.get(), vslider.get())
        send(mode_select.get(), receiver_ids[3], input_picture.get(), hslider.get(), sslider.get(), bslider.get(), vslider.get())
        send(mode_select.get(), receiver_ids[4], input_picture.get(), hslider.get(), sslider.get(), bslider.get(), vslider.get())
        send(mode_select.get(), receiver_ids[5], input_picture.get(), hslider.get(), sslider.get(), bslider.get(), vslider.get())
        # time.sleep(0.25)

    else:
        send(mode_select.get(), receiver_select.get(), input_picture.get(), hslider.get(), sslider.get(), bslider.get(), vslider.get())


def send_off():
    if receiver_select.get() == -1:  # Select all (-1)
        send(mode_select.get(), receiver_ids[0], 0, 0, 0, 0, 0)
        send(mode_select.get(), receiver_ids[1], 0, 0, 0, 0, 0)
        send(mode_select.get(), receiver_ids[2], 0, 0, 0, 0, 0)
        send(mode_select.get(), receiver_ids[3], 0, 0, 0, 0, 0)
        send(mode_select.get(), receiver_ids[4], 0, 0, 0, 0, 0)
        send(mode_select.get(), receiver_ids[5], 0, 0, 0, 0, 0)

    else:
        send(mode_select.get(), receiver_select.get(), 0, 0, 0, 0, 0)


def input_inc():
    tmp = input_picture.get()
    tmp = tmp + 1
    input_picture.set(tmp)
    send_single_all()


def input_dec():
    tmp = input_picture.get()
    if tmp > 0:
        tmp = tmp - 1
    input_picture.set(tmp)
    send_single_all()



# Title/Labels
title = tk.Label(root, bg="yellow", text="Remote Control LED Poi")
title.grid(row=0, column=0, sticky="W")

# Mode Label
modeLabel = tk.Label(root, bg="white", text="Mode", anchor="n")
modeLabel.grid(row=1, column=0)
# Mode Radio Buttons
mode_select = tk.IntVar()
mode_select.set(1)
# Mode Video Light - Hardware Buttons
radiom0 = tk.Radiobutton(root, text="Video Light Mode - HW Buttons", value=0, variable=mode_select)
radiom0.grid(row=2, column=0, sticky="W")
# Mode Video Light - Remote
radiom1 = tk.Radiobutton(root, text="Video Light Mode - Remote", value=1, variable=mode_select)
radiom1.grid(row=3, column=0, sticky="W")
# Mode Picture Mode
radiom2 = tk.Radiobutton(root, text="Picture Mode", value=2, variable=mode_select)
radiom2.grid(row=4, column=0, sticky="W")
# Mode Battery Level / Signal Strength
radiom3 = tk.Radiobutton(root, text="Battery Level / Signal Strength", value=3, variable=mode_select)
radiom3.grid(row=5, column=0, sticky="W")

# List available COM Ports
ports = list(port_list.comports())
for p in ports:
    print(p)
# Take first COM Port of List as default
serialPort = serial.Serial(port=str(ports[0]).split()[0], baudrate=115200, bytesize=8, timeout=2,
                           stopbits=serial.STOPBITS_ONE)
# COMBO BOX for COM Port
combo = ttk.Combobox(root, state="readonly", values=ports)
combo.grid(row=8, column=0)


# Apply selected COM Port
def apply():
    serialPort.setPort(combo.get().split()[0])


def mode_refresher():
    mode_select_old = mode_select.get()
    while 1:
        if mode_select.get() != mode_select_old:
            send_single_all()
        if mode_select.get() == 3:
            check_for_incoming_receiver_values()
        if mode_select_old != mode_select.get():
            mode_select_old = mode_select.get()
        time.sleep(0.25)


def check_for_incoming_receiver_values():
    if serialPort.in_waiting > 8:
        print("Receiver Values incoming")
        # Read data out of the buffer until a carriage return / new line is found
        serialString = serialPort.readline()
        res = serialString.decode("Ascii").split()
        # print("after readLine")

        # Print the contents of the serial data
        try:
            inputb1.set(res[0] + "V")
            inputb2.set(res[1] + "V")
            inputb3.set(res[2] + "V")
            inputb4.set(res[3] + "V")
            inputb5.set(res[4] + "V")
            inputb6.set(res[5] + "V")
            inputss1.set(res[6] + "%")
            inputss2.set(res[7] + "%")
            inputss3.set(res[8] + "%")
            inputss4.set(res[9] + "%")
            inputss5.set(res[10] + "%")
            inputss6.set(res[11] + "%")
        except:
            pass

threading.Thread(target=mode_refresher).start()


# Button Apply
buttonA = tk.Button(root, bg="white", text="Apply", anchor="e", command=apply)
buttonA.grid(row=8, column=1, sticky="w", padx=10)

# Select Picture Nr. Label
inputlabel = tk.Label(root, bg="white", text="Select Picture Nr.", anchor="n")
inputlabel.grid(row=1, column=1)
# Input Box Select Picture Nr.
input_picture = tk.IntVar()
input_picture.set('0')
inputbox = tk.Entry(root, textvariable=input_picture, width=5)
inputbox.grid(row=2, column=1, padx=20)
# Button Plus
buttonplus = tk.Button(root, bg="white", text="+", anchor="w", command=input_inc)
buttonplus.grid(row=2, column=1, sticky="e")
# Button Minus
buttonminus = tk.Button(root, bg="white", text="-", anchor="e", command=input_dec)
buttonminus.grid(row=2, column=1, sticky="w", padx=10)
# Button Send
button1 = tk.Button(root, text="Send", highlightthickness="6", command=send_single_all)
button1.grid(row=3, column=1)
# Button Off
button2 = tk.Button(root, text="Off", highlightthickness="6", command=send_off)
button2.grid(row=4, column=1)

# Select Receiver ID Label
channel = tk.Label(root, bg="white", text="Select Receiver ID")
channel.grid(row=1, column=4, padx=10)
# Radiobuttons receiver IDs
receiver_select = tk.IntVar()
for ids in receiver_ids:
    radiob = tk.Radiobutton(root, text=ids, value=ids, variable=receiver_select)
    radiob.grid(row=int(ids + 1), column=4)  # row 4 - 9
radio_all = tk.Radiobutton(root, text="all", value=-1, variable=receiver_select)
radio_all.grid(row=8, column=4)
receiver_select.set(1)  # setdefault to CH 20

# Slider brightness/value Label
brightlabel = tk.Label(root, bg="white", text="Brightness/Value", anchor="n")
brightlabel.grid(row=1, column=5)
# Slider brightness input
bslider = tk.Scale(root, from_=0, to=8, orient=HORIZONTAL)
bslider.grid(row=2, column=5)
bslider.set(1)  # default

# Slider Hue Label
brightlabel = tk.Label(root, bg="white", text="Hue", anchor="n")
brightlabel.grid(row=1, column=6)
# Slider Hue input
hslider = tk.Scale(root, from_=0, to=255, orient=HORIZONTAL)
hslider.grid(row=2, column=6)
hslider.set(1)  # default

# Slider Saturation Label
brightlabel = tk.Label(root, bg="white", text="Saturation")
brightlabel.grid(row=1, column=7)
# Slider Saturation input
sslider = tk.Scale(root, from_=0, to=255, orient=HORIZONTAL)
sslider.grid(row=2, column=7)
sslider.set(1)  # default

# Slider velocity Label
brightlabel = tk.Label(root, bg="white", text="Velocity", anchor="n")
brightlabel.grid(row=1, column=8)
# Slider brightness input
vslider = tk.Scale(root, from_=0, to=255, orient=HORIZONTAL)
vslider.grid(row=2, column=8)
vslider.set(1)  # default

# Battery Level Label
inputlabel = tk.Label(root, bg="white", text="Battery Level")
inputlabel.grid(row=1, column=9)
batteryBoxWidth = 10
# Input Box Battery 1
inputb1 = tk.IntVar()
inputb1.set('0.0V')
inputbox = tk.Entry(root, textvariable=inputb1, width=batteryBoxWidth)
inputbox.grid(row=2, column=9, padx=20)
# Input Box Battery 2
inputb2 = tk.IntVar()
inputb2.set('0.0V')
inputbox = tk.Entry(root, textvariable=inputb2, width=batteryBoxWidth)
inputbox.grid(row=3, column=9, padx=20)
# Input Box Battery 3
inputb3 = tk.IntVar()
inputb3.set('0.0V')
inputbox = tk.Entry(root, textvariable=inputb3, width=batteryBoxWidth)
inputbox.grid(row=4, column=9, padx=20)
# Input Box Battery 4
inputb4 = tk.IntVar()
inputb4.set('0.0V')
inputbox = tk.Entry(root, textvariable=inputb4, width=batteryBoxWidth)
inputbox.grid(row=5, column=9, padx=20)
# Input Box Battery 5
inputb5 = tk.IntVar()
inputb5.set('0.0V')
inputbox = tk.Entry(root, textvariable=inputb5, width=batteryBoxWidth)
inputbox.grid(row=6, column=9, padx=20)
# Input Box Battery 6
inputb6 = tk.IntVar()
inputb6.set('0.0V')
inputbox = tk.Entry(root, textvariable=inputb6, width=batteryBoxWidth)
inputbox.grid(row=7, column=9, padx=20)

SignalBoxWidth = 10
# Signal Strength Level Label
inputlabel = tk.Label(root, bg="white", text="Signal Strength")
inputlabel.grid(row=1, column=10)
batteryBoxWidth = 10
# Input Box Signal Strength 1
inputss1 = tk.IntVar()
inputss1.set('0%')
inputbox = tk.Entry(root, textvariable=inputss1, width=SignalBoxWidth)
inputbox.grid(row=2, column=10, padx=20)
# Input Box Signal Strength 2
inputss2 = tk.IntVar()
inputss2.set('0%')
inputbox = tk.Entry(root, textvariable=inputss2, width=SignalBoxWidth)
inputbox.grid(row=3, column=10, padx=20)
# Input Box Signal Strength 3
inputss3 = tk.IntVar()
inputss3.set('0%')
inputbox = tk.Entry(root, textvariable=inputss3, width=SignalBoxWidth)
inputbox.grid(row=4, column=10, padx=20)
# Input Box Signal Strength 4
inputss4 = tk.IntVar()
inputss4.set('0%')
inputbox = tk.Entry(root, textvariable=inputss4, width=SignalBoxWidth)
inputbox.grid(row=5, column=10, padx=20)
# Input Box Signal Strength 5
inputss5 = tk.IntVar()
inputss5.set('0%')
inputbox = tk.Entry(root, textvariable=inputss5, width=SignalBoxWidth)
inputbox.grid(row=6, column=10, padx=20)
# Input Box Signal Strength 6
inputss6 = tk.IntVar()
inputss6.set('0%')
inputbox = tk.Entry(root, textvariable=inputss6, width=SignalBoxWidth)
inputbox.grid(row=7, column=10, padx=20)

# Exit Button
buttonExit = tk.Button(root, text="Exit", command=root.destroy)
buttonExit.grid(row=9, column=11)
root.mainloop()
