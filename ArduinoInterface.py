import serial.tools.list_ports as port_list
import serial
import time
from PyQt5 import QtCore, QtGui
import sys


class ArduinoInterface:
    def __init__(self, rec_ids):
        self.receiver_ids = rec_ids
        self.total_num_receivers = len(self.receiver_ids)
        self.voltages = [0] * self.total_num_receivers
        self.signal_strength = [0] * self.total_num_receivers
        self.ports_names = []
        self.ports_COMs = []
        self.serialPort = None
        self.signal_strength_test_active = False

    def find_ports(self):
        # Find connected Ports for Arduino
        ports = list(port_list.comports())

        for p in ports:
            print(p)
            self.ports_COMs.append(p[0])
            self.ports_names.append(p[1])

        index = 0
        for p in self.ports_names:
            index = index + 1
            if "arduino uno" in p.lower():
                try:
                    self.serialPort = serial.Serial(
                        port=self.ports_COMs[index - 1], baudrate=115200, bytesize=8, write_timeout=1, timeout=2,
                        stopbits=serial.STOPBITS_ONE
                    )
                except:
                    print("Could not connect to Arduino Uno")

        if self.serialPort is None:  # open just the first port
            try:
                self.serialPort = serial.Serial(
                    port=self.ports_COMs[0], baudrate=115200, bytesize=8, write_timeout=1, timeout=2,
                    stopbits=serial.STOPBITS_ONE
                )
            except:
                print("Could not open the first port as default")

    def go_all_black(self):
        # Make all LEDs go black
        for ids in self.receiver_ids:
            self.send(2, ids, 0, 0, 0, 0, 0)  # 2 = Picture Mode

    def print_receiver_infos(self):
        for x in range(self.total_num_receivers):
            print(f"Receiver {x} voltage: {self.voltages[x]} signal strength: {self.signal_strength[x]}")

    # def send(self, channel, picturenum, brightness):
    def send(self, mode, receiver_id, picture, hue, saturation, brightness_value, velocity):
        starttime_SP_write = time.time_ns()
        if mode != 3:
            self.signal_strength_test_active = False
            # print("Signal Strength Test OFF")

        byte1, byte2, byte3, byte4, byte5, byte6, byte7 = int(mode), int(receiver_id), int(picture), int(hue), \
                                                          int(saturation), int(brightness_value), int(velocity)
        self.serialPort.write(
            chr(byte1).encode('latin_1') + chr(byte2).encode('latin_1') + chr(byte3).encode('latin_1') +
            chr(byte4).encode('latin_1') + chr(byte5).encode('latin_1') + chr(byte6).encode('latin_1') +
            chr(byte7).encode('latin_1'))
        # print("Duration for serial port write " + str((time.time_ns() - starttime_SP_write) / 1000000) + " ms")
        # self.serialPort.reset_input_buffer()  # Fixed some problems earlier!
        # serialPort.reset_output_buffer()

        self.receive()
        duration = (time.time_ns() - starttime_SP_write) / 1000000
        if duration > 3:
            print("Duration for serial port write and receive: " + str(duration) + " ms")
        # self.print_receiver_infos()

        # print("after readLine")

        # Print the contents of the serial data
        # try:
        #     for d in res:
        #         print(d, end="")
        #     print("")
        # except:
        #     print("Error")
        #     pass
    def receive(self):
        if self.serialPort.in_waiting >= 72:  # measured 72 bytes/characters
            # Read data out of the buffer until a carriage return / new line is found
            input_bytearray = self.serialPort.readline()
            res = str(input_bytearray.decode("Ascii"))
            lst = res.split()
            self.voltages = lst[:6]
            self.signal_strength = lst[-6:]

    def signal_strength_test_start(self):
        self.send(3, 0, 0, 0, 0, 0, 0)
        self.signal_strength_test_active = True
