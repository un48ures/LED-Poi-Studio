import sys
import time
import threading
import os
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.uic.properties import QtWidgets
from PyQt5 import QtWidgets
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QColor
import numpy as np
from pygame import mixer
import cProfile
import pstats
from ArduinoInterface import ArduinoInterface
from Marker import MarkerList
from AudioConverter import AudioConverter
import pyqtgraph as pg
import colorsys

dirname = os.path.dirname(__file__)

ui_file = dirname + '/Studio_GUI.ui'
default_audio_file_path = dirname + '/Syren.mp3'

REDUCTION_FACTOR = 4 # Audio Sample reduction factor - plot

receiver_ids = [1, 2, 3, 4, 5, 6]
mode = 2  # when this program is used automatically Picture Mode (2) is used
# brightness = 10  # set fixed global brightness for testing
saturation = 0  # unused
velocity = 0  # unused
COLOR_MODE = 1
PICTURE_MODE = 2


class MyGUI(QMainWindow):

    def __init__(self):
        super(MyGUI, self).__init__()
        self.stop_watch_start = 0
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
        self.sound_file = default_audio_file_path
        self.arduino = ArduinoInterface(receiver_ids)
        self.arduino.find_ports()
        self.marker_list = MarkerList()
        self.audio_converter = AudioConverter()
        self.current_index = self.marker_list.get_highest_marker_number() + 1
        self.pushButton.clicked.connect(self.start_stop)
        self.pushButton_2.clicked.connect(self.reset)
        self.pushButton_3.clicked.connect(self.set_marker_picture)
        self.pushButton_8.clicked.connect(self.set_marker_color)
        self.pushButton_4.clicked.connect(self.delete_marker)
        self.pushButton_5.clicked.connect(self.save_serial_config)
        self.pushButton_6.clicked.connect(self.open_audio_file)
        self.pushButton_7.clicked.connect(self.set_marker_off)
        self.testButton.clicked.connect(self.send_test_button_data)
        self.offButton.clicked.connect(self.arduino.go_all_black)
        self.signalTestButton.clicked.connect(self.arduino.signal_strength_test)
        self.exit_Button.clicked.connect(self.exit)
        self.comboBox_2.addItems(self.arduino.ports_names)
        self.refresh_marker_table()
        self.open_audio_file(1)  # 1 = default file (audio_file_path)
        self.cursor_position = 0 # seconds in float
        self.create_info_table()
        # mouse click
        self.waveform_widget.scene().sigMouseMoved.connect(self.mouse_moved)
        self.waveform_widget.scene().sigMouseClicked.connect(self.mouse_clicked_play_cursor)
        self.music_startpoint_offset = 0
        self.time_stamp = 0;

    def mouse_moved(self, evt):
        vb = self.waveform_widget.plotItem.vb
        if self.waveform_widget.sceneBoundingRect().contains(evt):
            mouse_point = vb.mapSceneToView(evt)
            # print(f"X： {mouse_point.x()} Y: {mouse_point.y()}</p>")

    def mouse_clicked_play_cursor(self, evt):
        vb = self.waveform_widget.plotItem.vb
        scene_coords = evt.scenePos()
        if self.waveform_widget.sceneBoundingRect().contains(scene_coords):
            mouse_point = vb.mapSceneToView(scene_coords)
            print(f'clicked plot X: {mouse_point.x()}, Y: {mouse_point.y()}, event: {evt}')
            mixer.music.stop()
            mixer.music.play()
            mixer.music.set_pos(mouse_point.x())
            mixer.music.pause()
            self.running = False
            self.paused = True
            self.music_startpoint_offset = mouse_point.x()

            # reset all markers to "False"
            self.marker_list.reset_send_status_all()


    def open_audio_file(self, default):
        if default != 1:
            file_info = QFileDialog.getOpenFileName(self, 'Open file', 'c:\\', "Sound files (*.mp3 *.wav *.aac *.ogg)")
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
        self.cursor = self.waveform_widget.plot([0, 0], [0, 0], pen=pg.mkPen('r', width=1))
        # Marker Plot Handle
        for c in range(len(self.marker_list.List)):
            self.lst_markers_plt_h.append(self.waveform_widget.plot([0, 0], [0, 0], pen=pg.mkPen('b', width=2)))

        self.waveform_widget.plotItem.setMouseEnabled(y=False)  # zoom only in x
        duration = int((time.time() - starttime) * 100) / 100
        self.update_marker_plot_data()
        print(f"Plotting waveform finisehd after {duration} s.")

    def update_cursor_plot_data(self):
        self.cursor_position = mixer.music.get_pos() / 1000 + self.music_startpoint_offset
        self.cursor.setData([ self.cursor_position,  self.cursor_position], [-2 * 10 ** 9, 2 * 10 ** 9])  # cursor

    def update_marker_plot_data(self):
        # Marker
        for index in range(len(self.marker_list.List)):
            m_pos = self.marker_list.get_marker_time_ms_by_index(index) / 1000  # marker
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
        #timer_send = QtCore.QTimer()
        #timer_send.timeout.connect(self.send_marker)
        #timer_send.start(1)
        self.start_animation()

    def refresh_marker_table(self):
        print("Refresh Table")
        # self.table1.clear()
        self.table1.setRowCount(len(self.marker_list.List))
        row_counter = 0
        # Update color of status and background color of color column
        for rows in self.marker_list.List:
            item_counter = 0
            for items in rows:
                widget = QtWidgets.QTableWidgetItem(str(items))
                # Status Background
                if items == "False":
                    widget.setBackground(QColor(220, 20, 0))
                elif items == "True":
                    widget.setBackground(QColor(20, 220, 0))
                # Color Background
                if item_counter == 5 and int(items) != 0:
                    r, g, b = colorsys.hsv_to_rgb(int(items) / 255, 1, 1)
                    widget.setBackground(QColor(int(r * 255), int(g * 255), int(b * 255), 100))

                self.table1.setItem(row_counter, item_counter, widget)

                item_counter = item_counter + 1
            row_counter = row_counter + 1
        # Tweak to update
        self.table1.setRowCount(len(self.marker_list.List) + 1)

    def create_info_table(self):
        self.tableWidget.setRowCount(len(receiver_ids))
        for r in range(len(receiver_ids)):
            self.tableWidget.setItem(r, 0, QtWidgets.QTableWidgetItem("LED Poi " + str(r + 1)))
            self.tableWidget.setItem(r, 1, QtWidgets.QTableWidgetItem(str(self.arduino.voltages[r]) + " V"))
            self.tableWidget.setItem(r, 2, QtWidgets.QTableWidgetItem(str(self.arduino.signal_strength[r]) + " %"))

    def update_info_table(self):
        for r in range(len(receiver_ids)):
            item = self.tableWidget.item(r, 1)
            item.setText(str(self.arduino.voltages[r]) + " V")
            item = self.tableWidget.item(r, 2)
            item.setText(str(self.arduino.signal_strength[r]) + " %")
        self.label_brightness.setText(str(self.brightnessSlider.value())) # update brightness slider label
        self.label_color.setText(str(self.colorSlider.value()))
        r, g, b = colorsys.hsv_to_rgb(self.colorSlider.value() / 255, 1, 1)
        self.label_color.setStyleSheet("background-color: rgb(" + str(r * 255) + ", " + str(g * 255) + ", " + str(b * 255) + ")")
        self.label_velocity.setText(str(self.velocitySlider.value()) + " ms")  # update brightness slider label

    # Refresh status in table from false to true
    def paint_status_green(self, row_index):
        self.table1.setRowCount(len(self.marker_list.List))
        # Color for Status False (Red) and True (Green)
        status = self.marker_list.List[int(row_index)][7]
        if status == "True":
            widget = QtWidgets.QTableWidgetItem(status)
            widget.setBackground(QColor(0, 255, 0))
            self.table1.setItem(int(row_index), 7, widget)
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
            self.stop_watch_start = time.perf_counter()
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
                # mixer.music.play(-1, self.music_startpoint)
                mixer.music.play()
                print("Music Play")

    def send_marker(self):
        if self.checkBox.isChecked() and self.running:
            list_m = self.marker_list.get_marker()
            while self.running: # no more thread used
                print(f"time.time_ns: {time.time_ns()}\n")
                print(f"time.perf_counter. {time.perf_counter()}\n")
                print(f"mixer.music.get_pos: {mixer.music.get_pos()}\n")
                print(f"time.perf_counter - starttime {time.perf_counter() - self.stop_watch_start}\n")
                starttime = time.time_ns()
                # rows -> markers
                index = 0
                for r in list_m:
                    ids = r[2]
                    mode = int(r[3])
                    picture = int(r[4])
                    color = int(r[5])
                    velocity = int(r[6])
                    send_status = r[-1]

                    if send_status == "False":
                        # decrypt time
                        ms = self.marker_list.get_marker_time_ms(r)
                        # Not send marker if older than 30 ms -> somehow program gets interrupted sometimes for up to 24 ms
                        if ms < (mixer.music.get_pos() + self.music_startpoint_offset * 1000) < (ms + 30):  # 0 <-> 250
                            # starttime_serial_send = time.time_ns()
                            if ids != "ALL":
                                self.arduino.send(mode, ids, picture, color, saturation, self.brightnessSlider.value(), velocity)
                            else:
                                # Broadcast to all receivers
                                for ids in receiver_ids:
                                    self.arduino.send(mode, ids, picture, color, saturation, self.brightnessSlider.value(), velocity)
                            # print("Duration for serial_send: " + str(
                            # (time.time_ns() - starttime_serial_send) / 1000000) + " ms")
                            # set marker sent_status "True"
                            self.label_3.setText(
                                "Last sent message:\n\n"
                                + f"Channel: {ids}\n"
                                + f"Picture Nr.: {picture}\n"
                                + f"Color/Hue.: {color}\n"
                                + f"Saturation.: {saturation}\n"
                                + f"Brightness: {self.brightnessSlider.value()}\n"
                                + f"Velocity.: {velocity}\n"
                                  f"\n\n")
                            r[-1] = "True"
                            self.paint_status_green(index)  # used to be time problematic !
                    index += 1
                # time.sleep(0.001)
                # print(f"Duration for Thread send_marker: {(time.time_ns() - starttime) / 1000} us")
                #print(starttime)
                #print(time.time_ns() / 1000000 - self.time_stamp)
                #self.time_stamp = time.time_ns() / 1000000

    def send_test_button_data(self):
        mode_t = 0
        saturation = 255
        ids = self.comboBox.currentText()
        if self.spinBox.value() == 0:
            mode_t = COLOR_MODE
        else:
            mode_t = PICTURE_MODE

        if ids != "ALL":
            self.arduino.send(mode_t, int(self.comboBox.currentText()), self.spinBox.value(), self.colorSlider.value(), saturation , self.brightnessSlider.value(), self.velocitySlider.value())
        else:
            # Broadcast to all receivers
            for ids in range(6):
                self.arduino.send(mode_t, ids + 1, self.spinBox.value(), self.colorSlider.value(), saturation, self.brightnessSlider.value(), self.velocitySlider.value())

        self.label_3.setText(
            "Last sent message:\n\n"
            + f"Channel: {ids}\n"
            + f"Picture Nr.: {self.spinBox.value()}\n"
            + f"Color/Hue.: {self.colorSlider.value()}\n"
            + f"Saturation.: {saturation}\n"
            + f"Brightness: {self.brightnessSlider.value()}\n"
            + f"Velocity.: { self.velocitySlider.value()}\n"
              f"\n\n")

    # def send_all_off_data(self):


    def reset(self):
        self.pushButton.setText("Start")
        # self.pushButton_2.setEnabled(False)
        self.label.setText("00:00:00:00")
        mixer.music.stop()
        self.paused = False
        self.running = False
        print("Music stop")
        self.marker_list.reset_send_status_all()
        self.passed = 0
        self.music_startpoint_offset = 0
        # Make all LEDs go black
        for ids in receiver_ids:
            self.arduino.send(mode, ids, 0, 0, saturation, 0, velocity)
        self.refresh_marker_table()

    def set_marker_picture(self):
        self.marker_list.add_marker(self.current_index, self.format_time_string(self.passed),
                                    self.comboBox.currentText(), PICTURE_MODE,
                                    self.spinBox.value(), 0, self.velocitySlider.value(),  False)
        self.lst_markers_plt_h.append(self.waveform_widget.plot([0, 0], [0, 0], pen='b'))
        self.update_marker_plot_data()
        self.refresh_marker_table()
        self.current_index += 1

    def set_marker_color(self):
        self.marker_list.add_marker(self.current_index, self.format_time_string(self.passed),
                                    self.comboBox.currentText(), COLOR_MODE,
                                    0, self.colorSlider.value(), 0,  False)
        self.lst_markers_plt_h.append(self.waveform_widget.plot([0, 0], [0, 0], pen='b'))
        self.update_marker_plot_data()
        self.refresh_marker_table()
        self.current_index += 1


    def set_marker_off(self):
        self.marker_list.add_marker(self.current_index, self.format_time_string(self.passed),
                                    self.comboBox.currentText(), PICTURE_MODE,
                                    0, 0, 0,  False)
        self.lst_markers_plt_h.append(self.waveform_widget.plot([0, 0], [0, 0], pen='b'))
        self.update_marker_plot_data()
        self.refresh_marker_table()
        self.current_index += 1

    def delete_marker(self):
        # delete nearest marker
        # find nearest marker
        index = self.marker_list.delete_next_marker_to_time_ms(self.cursor_position * 1000)
        if index > -1:
            self.lst_markers_plt_h[index].setData([0, 0], [0, 0], pen='b')  # delete marker from plot
            self.lst_markers_plt_h.pop(index)
            self.refresh_marker_table()
            self.current_index -= 1


    def format_time_string(self, time_passed):
        secs = time_passed % 60
        mins = time_passed // 60
        hours = mins // 60
        return f"{int(hours):02d}:{int(mins):02d}:{int(secs):02d}:{int((self.passed % 1) * 1000):03d}"

    def clock(self):
        self.passed = mixer.music.get_pos() / 1000.0 + self.music_startpoint_offset
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





def main():
    mixer.init()
    app = QApplication([])
    # cProfile.run('MyGUI()', 'PROFILE.txt')
    window = MyGUI()
    mixer.music.load(window.sound_file)
    window.animation()
    app.exec_()


if __name__ == "__main__":
    main()
    # on exit
    # f.close()
