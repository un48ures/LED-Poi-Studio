import serial.tools.list_ports as port_list
import serial
import time
import struct


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

        START_BYTE = 0xAA
        packet = bytes([START_BYTE, int(mode), int(receiver_id), int(picture),
                        int(hue), int(saturation), int(brightness_value), int(velocity)])

        if self.serialPort is not None:
            self.serialPort.write(packet)
        else:
            print("No serial connection established - can`t write to serial Port")

        self.receive()
        duration = (time.time_ns() - starttime_SP_write) / 1000000
        # print("Duration for serial port write and receive: " + str(duration) + " ms")


    def receive(self):
        if self.serialPort is None:
            return

        expected_bytes = 12 * 4  # 12 floats, 4 bytes each = 48 bytes
        if self.serialPort.in_waiting >= expected_bytes:
            try:
                raw_data = self.serialPort.read(expected_bytes)
                floats = struct.unpack('<12f', raw_data)  # Little-endian float
                self.voltages = floats[:6]
                self.signal_strength = floats[6:]
            except Exception as e:
                print(f"[Binary Receive] Error: {e}")

    def signal_strength_test_start(self):
        self.send(3, 0, 0, 0, 0, 0, 0)
        self.signal_strength_test_active = True
