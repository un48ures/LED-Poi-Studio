import sys
import time
import threading
import wave
import serial
import os
import os.path
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.uic.properties import QtWidgets
from PyQt5 import QtWidgets
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QColor
import numpy as np
from pydub import AudioSegment
import pyqtgraph as pg
from pygame import mixer
import serial.tools.list_ports as port_list
import cProfile
import pstats

ui_file = 'C:\\Users\\felix\\PycharmProjects\\Controller\\Stopwatch\\stopwatch3.ui'
backup_file = 'C:\\Users\\felix\\PycharmProjects\\Controller\\Stopwatch\\markers_backup.txt'
audio_file_path = 'C:\\Users\\felix\\PycharmProjects\\Controller\\Stopwatch\\song.mp3'

receiver_ids = [1, 2, 3, 4, 5, 6]
mode = 2  # when this program is used automatically Picture Mode (2) is used
brightness = 2  # set fixed global brightness for testing
saturation = 0  # unused
velocity = 0  # unused

REDUCTION_FACTOR = 6

RECEIVER_COUNT = 6


class MarkerList:
    def __init__(self):
        self.List = []
        if os.path.isfile(backup_file):
            print("backup file found")
            self.f = open(backup_file, "r")
        else:
            self.f = open(backup_file, "w")
            print("no backup file found - new backup file created")
        self.reload_backup()

    def reload_backup(self):
        self.f = open(backup_file, "r")
        str_input = self.f.read()
        backup_details = []
        [backup_details.append(b.split()) for b in str_input.splitlines()]
        print(backup_details)
        self.List = backup_details
        self.f.close()

    def add_marker(self, number, time_stamp, ID, picture, send_status):
        self.List.append([number, time_stamp, ID, picture, send_status])
        self.update_backup_file()

    def update_backup_file(self):
        self.f = open(backup_file, "w")
        for x in self.List:
            for i in x:
                self.f.write(str(i) + " ")
            self.f.write("\n")
        self.f.close()

    def output_list_as_string(self):
        output = ""
        if len(self.List) > 0:
            for x in self.List:
                output += f"\nMarker {x[0]} - Time: {x[1]} - ID {x[2]} - Picture: {x[3]} - Status Sent: {x[4]}"
        return output

    def delete_last(self):
        if len(self.List) > 0:
            self.List.pop()
            self.update_backup_file()
            print("Last Marker deleted")
        else:
            print("List empty")

    def reset_send_status_all(self):
        for x in self.List:
            x[4] = "False"

    def get_marker(self):
        return self.List

    def get_marker_time_ms(self, index):
        ms = 0
        if index < len(self.List):
            m = self.List[index]
            ms = int(m[1][10]) * 10 + int(m[1][9]) * 100 + int(m[1][7]) * 1000 + int(m[1][6]) * 10000 + int(
                m[1][4]) * 60 * 1000
            if ms < 0 or ms > 1200000:  # 20 min
                ms = 0
        return ms

    def set_marker_sent_status(self, marker_number, status_new):
        for lm in self.List:
            if lm[0] == marker_number:
                lm[-1] = status_new
                print("Set sent status of marker " + str(marker_number) + " to " + str(status_new))

    def get_highest_marker_number(self):
        if len(self.List) > 0:
            # print("ListMarkers len: " + str(self.List[-1][0]))
            return int(self.List[-1][0])
        else:
            return 0


class MyGUI(QMainWindow):

    def __init__(self):
        super(MyGUI, self).__init__()
        self.audio_time = None
        self.audio_signal = None
        self.cursor = None
        self.first_marker = None
        self.waveform_data = None
        uic.loadUi(ui_file, self)
        self.lst_markers_plt_h = list()
        self.show()
        self.running = False
        self.started = False
        self.passed = 0
        self.previous_passed = 0
        self.paused = False
        self.plotwidget = 0
        self.sound_file = audio_file_path
        self.arduino = ArduinoInterface()
        self.arduino.find_ports()
        self.marker_list = MarkerList()
        self.audio_converter = AudioConverter()
        self.current_index = self.marker_list.get_highest_marker_number() + 1
        self.pushButton.clicked.connect(self.start_stop)
        self.pushButton_2.clicked.connect(self.reset)
        self.pushButton_3.clicked.connect(self.set_marker)
        self.pushButton_4.clicked.connect(self.delete_marker)
        self.pushButton_5.clicked.connect(self.save_serial_config)
        self.pushButton_6.clicked.connect(self.open_audio_file)
        self.exit_Button.clicked.connect(self.exit)
        self.comboBox_2.addItems(self.arduino.ports_names)
        self.refresh_marker_table()
        self.open_audio_file(1)  # 1 = default file (audio_file_path)
        self.cursor_position = 0
        self.create_infos_table()

    def open_audio_file(self, default):
        if default != 1:
            file_info = QFileDialog.getOpenFileName(self, 'Open file', 'c:\\', "Sound files (*.mp3)")
            self.sound_file = file_info[0]
        mixer.music.load(self.sound_file)
        self.label_4.setText(self.sound_file)
        self.audio_time, self.audio_signal = self.audio_converter.convert_mp3_to_array(self.sound_file)
        self.waveform_widget.clear()
        self.plot_waveform()

    def reduce_samples(self, factor):
        signal_red = self.audio_signal[np.mod(np.arange(self.audio_signal.size), 2) != 0]
        # just throw out every 2nd samples for factor times
        for x in range(factor):
            signal_red = signal_red[np.mod(np.arange(signal_red.size), 2) != 0]
        return np.arange(0, self.audio_time[-1], self.audio_time[-1] / signal_red.size), signal_red  # calc time lst

    def plot_waveform(self):
        # reduce samples
        print("Start plotting waveform")
        starttime = time.time()
        time_red, signal_red = self.reduce_samples(REDUCTION_FACTOR)
        duration = int((time.time() - starttime) * 100) / 100
        print(f"Reducing samples finisehd after {duration} s.")
        print(len(self.audio_signal))
        print(len(signal_red))
        wf_widget_plot_handle = self.waveform_widget.plot(time_red, signal_red)
        # wf_widget_plot_handle.setDownsampling(auto=False, ds=5)
        self.cursor = self.waveform_widget.plot([0, 0], [0, 0], pen='r')
        # Marker Plot Handle
        for c in range(len(self.marker_list.List)):
            self.lst_markers_plt_h.append(self.waveform_widget.plot([0, 0], [0, 0], pen='b'))

        self.waveform_widget.plotItem.setMouseEnabled(y=False)  # zoom only in x
        duration = int((time.time() - starttime) * 100) / 100
        self.update_marker_plot_data()
        print(f"Plotting waveform finisehd after {duration} s.")

    def update_cursor_plot_data(self):
        position = mixer.music.get_pos() / 1000
        self.cursor.setData([position, position], [-2 * 10 ** 9, 2 * 10 ** 9])  # cursor

    def update_marker_plot_data(self):
        # Marker
        for index in range(len(self.marker_list.List)):
            m_pos = self.marker_list.get_marker_time_ms(index) / 1000  # marker
            if m_pos > 0:
                # self.first_marker.setData([m_pos, m_pos], [-2 * 10 ** 9, 2 * 10 ** 9], pen='b')
                self.lst_markers_plt_h[index].setData([m_pos, m_pos], [-2 * 10 ** 9, 2 * 10 ** 9], pen='b')
                pass
            else:
                self.lst_markers_plt_h[index].setData([0, 0], [0, 0], pen='b')
                pass

    def start_animation(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QGuiApplication.instance().exec()

    def animation(self):
        timer_cursor = QtCore.QTimer()
        timer_cursor.timeout.connect(self.update_cursor_plot_data)
        timer_cursor.start(25)
        timer_clock = QtCore.QTimer()
        timer_clock.timeout.connect(self.clock)
        timer_clock.start(10)
        timer_info_table = QtCore.QTimer()
        timer_info_table.timeout.connect(self.update_info_table)
        timer_info_table.start(250)
        self.start_animation()

    def refresh_marker_table(self):
        print("Refresh Table")
        self.table1.clear()
        self.table1.setRowCount(len(self.marker_list.List))
        row_counter = 0
        for rows in self.marker_list.List:
            item_counter = 0
            for items in rows:
                # print(items)
                widget = QtWidgets.QTableWidgetItem(items)
                # Color for Status False (Red) and True (Green)
                if items == "False":
                    widget.setBackground(QColor(255, 0, 0))
                elif items == "True":
                    widget.setBackground(QColor(0, 255, 0))
                self.table1.setItem(row_counter, item_counter, widget)
                item_counter = item_counter + 1
            row_counter = row_counter + 1
        # Tweak to update
        self.table1.setRowCount(len(self.marker_list.List) + 1)

    def create_infos_table(self):
        self.tableWidget.setRowCount(RECEIVER_COUNT)
        for r in range(RECEIVER_COUNT):
            self.tableWidget.setItem(r, 0, QtWidgets.QTableWidgetItem("LED Poi " + str(r + 1)))
            self.tableWidget.setItem(r, 1, QtWidgets.QTableWidgetItem(str(self.arduino.voltages[r]) + " V"))
            self.tableWidget.setItem(r, 2, QtWidgets.QTableWidgetItem(str(self.arduino.signal_strength[r]) + " %"))

    def update_info_table(self):
        for r in range(RECEIVER_COUNT):
            item = self.tableWidget.item(r, 1)
            item.setText(str(self.arduino.voltages[r]) + " V")
            item = self.tableWidget.item(r, 2)
            item.setText(str(self.arduino.signal_strength[r]) + " %")

    # Refresh status in table from false to true
    def paint_status_green(self, row_number):
        self.table1.setRowCount(len(self.marker_list.List))
        # Color for Status False (Red) and True (Green)
        status = self.marker_list.List[int(row_number) - 1][4]
        if status == "True":
            widget = QtWidgets.QTableWidgetItem(status)
            widget.setBackground(QColor(0, 255, 0))
            self.table1.setItem(int(row_number) - 1, 4, widget)
        # Tweak to update
        self.table1.setRowCount(len(self.marker_list.List) + 1)

    def start_stop(self):
        # Stop
        if self.running:
            self.running = False
            self.pushButton.setText("Resume")
            mixer.music.pause()
            print("Music pause")
            self.paused = True
        # Start - Running
        else:
            self.running = True
            self.pushButton.setText("Stop")
            # self.pushButton_2.setEnabled(False)
            # threading.Thread(target=self.stopwatch).start()
            print(self.checkBox.isChecked())
            if self.checkBox.isChecked():
                # Check for next marker to be sent
                print("Thread send marker started")
                threading.Thread(target=self.send_marker).start()
            # Play Music
            if self.paused:
                mixer.music.unpause()
                self.paused = False
                print("Music resume")
            else:
                mixer.music.play()
                print("Music Play")

    def send_marker(self):
        list_m = self.marker_list.get_marker()
        while self.running:
            starttime = time.time_ns()
            # rows -> markers
            for r in list_m:
                ids = r[2]
                picture = int(r[3])
                send_status = r[4]
                # print(f"For Marker {r[0]} the timestamp is: {ms} ms and sent status is: {send_status}")
                if send_status == "False":
                    ms = int(r[1][10]) * 10 + int(r[1][9]) * 100 + int(r[1][7]) * 1000 + int(r[1][6]) * 10000 + int(
                        r[1][4]) * 60 * 1000
                    # Not send marker if older than 250ms
                    if ms < int(mixer.music.get_pos()) < ms + 250:
                        # Send marker values
                        # print("Current time is over timestamp of Marker ----> Send to Arduino")
                        starttime_serial_send = time.time_ns()
                        if r[2] != "ALL":
                            self.arduino.send(mode, ids, picture, saturation, brightness, velocity)
                            self.label_3.setText(
                                "Last sent message:\n\n" + f"Channel: {ids}\n" + f"Picture Nr.: {picture}\n" +
                                f"Brightness: {brightness}\n\n")
                        else:
                            # Broadcast to all receivers
                            for ids in receiver_ids:
                                self.arduino.send(mode, ids, picture, saturation, brightness, velocity)
                            self.label_3.setText(
                                "Last sent message:\n\n" + "Channel: ALL\n" + f"Picture Nr.: {picture}\n" +
                                f"Brightness: {brightness} \n\n")
                        # print("Duration for serial_send: " + str(
                        # (time.time_ns() - starttime_serial_send) / 1000000) + " ms")
                        # set marker sent_status "True"
                        r[4] = "True"
                        self.paint_status_green(r[0])  # problematic !
            time.sleep(0.001)
            # print("Duration for Thread send_marker: " + str((time.time_ns() - starttime) / 1000000) + " ms")

    def reset(self):
        self.pushButton.setText("Start")
        # self.pushButton_2.setEnabled(False)
        self.label.setText("00:00:00:00")
        mixer.music.stop()
        self.paused = False
        print("Music stop")
        self.marker_list.reset_send_status_all()
        self.passed = 0
        # Make all LEDs go black
        for ids in receiver_ids:
            self.arduino.send(mode, ids, 0, saturation, 0, velocity)
        self.refresh_marker_table()

    def set_marker(self):
        self.marker_list.add_marker(self.current_index, self.format_time_string(self.passed),
                                    self.comboBox.currentText(),
                                    self.spinBox.value(), False)
        self.lst_markers_plt_h.append(self.waveform_widget.plot([0, 0], [0, 0], pen='b'))
        self.update_marker_plot_data()
        self.refresh_marker_table()
        self.current_index += 1

    def delete_marker(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.marker_list.delete_last()
            self.lst_markers_plt_h[self.current_index - 1].setData([0, 0], [0, 0], pen='b')  # delete marker from plot
            self.lst_markers_plt_h.pop(self.current_index - 1)
            self.refresh_marker_table()

    def format_time_string(self, time_passed):
        secs = time_passed % 60
        mins = time_passed // 60
        hours = mins // 60
        return f"{int(hours):02d}:{int(mins):02d}:{int(secs):02d}:{int((self.passed % 1) * 100):02d}"

    def clock(self):
        self.passed = mixer.music.get_pos() / 1000.0
        if self.passed < 0:
            self.passed = 0
        self.label.setText(self.format_time_string(self.passed))

    def save_serial_config(self):
        self.arduino.serialPort.setPort(self.arduino.ports_COMs[self.comboBox_2.currentIndex()])
        time.sleep(2.5)
        self.arduino.go_all_black()

    def exit(self):
        self.arduino.go_all_black()
        self.arduino.serialPort.close()
        time.sleep(0.100)
        sys.exit()


class ArduinoInterface:
    def __init__(self):
        self.voltages = [0] * RECEIVER_COUNT
        self.signal_strength = [0] * RECEIVER_COUNT
        self.ports_names = []
        self.ports_COMs = []
        self.serialPort = None

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
                self.serialPort = serial.Serial(
                    port=self.ports_COMs[index - 1], baudrate=115200, bytesize=8, write_timeout=1, timeout=2,
                    stopbits=serial.STOPBITS_ONE
                )

        if not self.serialPort.is_open: # open just the first port
            self.serialPort = serial.Serial(
                port=self.ports_COMs[0], baudrate=115200, bytesize=8, write_timeout=1, timeout=2,
                stopbits=serial.STOPBITS_ONE
            )

    def go_all_black(self):
        # Make all LEDs go black
        for ids in receiver_ids:
            self.send(mode, ids, 0, saturation, 0, velocity)

    def print_receiver_infos(self):
        for x in range(RECEIVER_COUNT):
            print(f"Receiver {x} voltage: {self.voltages[x]} signal strength: {self.signal_strength[x]}")

    # def send(self, channel, picturenum, brightness):
    def send(self, mode, receiver_id, picture_hue, saturation, brightness_value, velocity):
        starttime_SP_write = time.time_ns()
        byte1, byte2, byte3, byte4, byte5, byte6 = int(mode), int(receiver_id), int(picture_hue), int(saturation), \
                                                   int(brightness_value), int(velocity)

        self.serialPort.write(chr(byte1).encode('latin_1') + chr(byte2).encode('latin_1') + chr(byte3).encode('latin_1') +
                         chr(byte4).encode('latin_1') + chr(byte5).encode('latin_1') + chr(byte6).encode('latin_1'))
        # print("Duration for serial port write " + str((time.time_ns() - starttime_SP_write) / 1000000) + " ms")
        # self.serialPort.reset_input_buffer()  # Fixed some problems earlier!
        # serialPort.reset_output_buffer()

        if self.serialPort.in_waiting > 0:
            # Read data out of the buffer until a carriage return / new line is found
            bytearray = self.serialPort.readline()
            res = str(bytearray.decode("Ascii"))
            lst = res.split()
            self.voltages = lst[:6]
            self.signal_strength = lst[-6:]

        print("Duration for serial port write and receive: " + str((time.time_ns() - starttime_SP_write) / 1000000) + " ms")
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


class AudioConverter:
    def __init__(self):
        self.starttime = 0

    def convert_mp3_to_array(self, input_file):
        print("Started WAV Conversion")
        self.starttime = time.time()
        sound = AudioSegment.from_mp3(input_file)
        sound.export('converted.wav', format="wav")
        with wave.open('converted.wav', 'r') as wav_file:
            signal = wav_file.readframes(-1)
            # signal = np.fromstring(signal, int)
            signal = np.frombuffer(signal, int)
            # Get time from indices
            fs = wav_file.getframerate()
            time_x = np.linspace(0, len(signal) / fs, num=int(len(signal)))
        print("Conversion of " + str(input_file) + " done!")
        duration = (int((time.time() - self.starttime) * 100)) / 100  # truncate to 2 decimals
        print("Conversion took: " + str(duration) + " s")
        print("Audio duration: " + str(int(len(signal) / fs / 60)) + ' min ' + str(int(len(signal) / fs % 60)) + ' s')
        return time_x, signal


def main():
    mixer.init()
    app = QApplication([])
    cProfile.run('MyGUI()', 'PROFILE.txt')
    window = MyGUI()
    mixer.music.load(window.sound_file)
    window.animation()
    app.exec_()


if __name__ == "__main__":
    main()
    # on exit
    # f.close()
