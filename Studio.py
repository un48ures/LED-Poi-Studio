import sys
import time
import threading
import os
from PyQt6 import uic
from PyQt6.QtWidgets import *
from PyQt6.uic.properties import QtWidgets
from PyQt6 import QtWidgets
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QFont
import numpy as np
from pygame import mixer
import pygame
from ArduinoInterface import ArduinoInterface
from Marker import MarkerList
import AudioConverter
import pyqtgraph as pg
import colorsys
from pyqtgraph import InfiniteLine
import math
import ctypes
from helper_functions import truncate

# own files
from dark_theme import dark_theme
from time_functions import format_time_string
from helper_functions import calc_jitter_info
from helper_functions import delete_jitter_values

# For higher precision on windows
ctypes.windll.winmm.timeBeginPeriod(1)  # Request 1 ms resolution

# Create a stop event
stop_event = threading.Event()

# Treads

def set_column_not_editable(table_widget, column_index):
    for row in range(table_widget.rowCount()):
        item = table_widget.item(row, column_index)
        if item is None:
            item = QTableWidgetItem()  # Create a new item if none exists
            table_widget.setItem(row, column_index, item)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)  # Disable editing


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores the temp path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # If not running as a bundled executable
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


ui_file = resource_path('Studio_GUI_new.ui')
mp3_files = AudioConverter.find_mp3_files(os.path.dirname(__file__))
REDUCTION_FACTOR = 4  # Audio Sample reduction factor - plot
receiver_ids = [1, 2, 3, 4, 5, 6]
COLOR_MODE = 1
PICTURE_MODE = 2
p_flag = True
cursor_thread_interval = 50 # in ms
clock_thread_intervall = 25 # in ms
send_marker_thread_intervall = 3 # in ms
project_file_default_path = 'C:/Users/aac_n/Documents/work/LED-Poi-Studio/projectFile.txt'

class MyGUI(QMainWindow):

    def __init__(self):
        super(MyGUI, self).__init__()
        self.cursor_position = 0  # seconds in float
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
        self.label_cursor = pg.TextItem("Test", anchor=(0, 1),color='r', fill=pg.mkBrush(0, 0, 0, 150))
        font = QFont("Arial", 16)  # 16 pt font size
        self.label_cursor.setFont(font)
        self.waveform_widget.setBackground(QColor(59, 59, 59))  # 0x3b3b3b
        self.waveform_widget.hideAxis('bottom')
        self.waveform_widget.hideAxis('left')
        self.waveform_widget.scene().sigMouseMoved.connect(self.mouse_moved)
        self.waveform_widget.scene().sigMouseClicked.connect(self.mouse_clicked_play_cursor)
        self.sound_file = mp3_files[0]  # just load the first .mp3 file thats in the homedirectory
        self.arduino = ArduinoInterface(receiver_ids)
        self.arduino.find_ports()
        self.marker_list = MarkerList(project_file_default_path)
        self.label_19.setText(project_file_default_path)
        self.audio_converter = AudioConverter.AudioConverter()
        self.current_index = self.marker_list.get_highest_marker_number() + 1
        self.pushButton.clicked.connect(self.start_stop)
        self.pushButton_2.clicked.connect(self.reset)
        self.pushButton_3.clicked.connect(self.set_marker_picture)
        self.pushButton_8.clicked.connect(self.set_marker_color)
        self.pushButton_4.clicked.connect(self.delete_marker)
        self.pushButton_5.clicked.connect(self.save_serial_config)
        self.pushButton_6.clicked.connect(self.open_audio_file)
        self.pushButton_7.clicked.connect(self.set_marker_off)
        self.pushButton_9.clicked.connect(self.open_project_file)
        self.testButton.clicked.connect(self.send_test_button_data)
        self.offButton.clicked.connect(self.arduino.go_all_black)
        self.signalTestButton.clicked.connect(self.arduino.signal_strength_test_start)
        self.exit_Button.clicked.connect(self.exit)
        self.comboBox_2.addItems(self.arduino.ports_names)
        self.refresh_marker_table()
        self.open_audio_file(True)  # 1 = default file (audio_file_path)
        self.create_info_table()
        self.music_startpoint_offset = 0
        self.time_stamp = 0
        self.table1.cellChanged.connect(self.on_cell_changed)
        self.old_mixer_pos = 0.0

    def keyPressEvent(self, event):
        # Check if the pressed key is the spacebar
        if event.key() == Qt.Key.Key_Space:
            self.on_spacebar_pressed()

    def on_spacebar_pressed(self):
        self.start_stop()

    def on_cell_changed(self, row, column):
        self.marker_list.List[row][column] = str(self.table1.item(row, column).text())
        self.marker_list.update_backup_file()
        print(f"self.marker_list.List[{row}][{column}] is now: {self.table1.item(row, column).text()}")

    def mouse_moved(self, evt):
        vb = self.waveform_widget.plotItem.vb
        #if self.waveform_widget.sceneBoundingRect().contains(evt):
            # mouse_point = vb.mapSceneToView(evt)
            # print(f"X： {mouse_point.x()} Y: {mouse_point.y()}</p>")

    def mouse_clicked_play_cursor(self, evt):
        vb = self.waveform_widget.plotItem.vb
        scene_coords = evt.scenePos()
        if self.waveform_widget.sceneBoundingRect().contains(scene_coords):
            mouse_point = vb.mapSceneToView(scene_coords)
            # print(f'clicked plot X: {mouse_point.x()}, Y: {mouse_point.y()}, event: {evt}')
            mixer.music.stop()
            mixer.music.play()
            mixer.music.set_pos(mouse_point.x())
            mixer.music.pause()
            self.running = False
            self.paused = True
            self.music_startpoint_offset = mouse_point.x()

            # reset all markers to "False"
            self.marker_list.reset_send_status_all()

    def open_project_file(self):
        path_project_file = QFileDialog.getOpenFileName(self, 'Open file', 'c:\\', "Project files (*.txt)")
        print(f"path_project_file: {path_project_file[0]}")
        self.marker_list.set_backup_file_path(path_project_file[0])
        self.label_19.setText(path_project_file[0])
        self.create_dummy_lines_in_waveform()

    def open_audio_file(self, default):
        if not default:
            path_audio_file = QFileDialog.getOpenFileName(self, 'Open file', 'c:\\', "Sound files (*.mp3 *.wav *.aac *.ogg)")
            self.sound_file = path_audio_file[0]

        try:
            mixer.music.load(self.sound_file)
            self.label_4.setText(self.sound_file)
            self.audio_time, self.audio_signal = self.audio_converter.convert_mp3_to_array(self.sound_file)
            self.waveform_widget.clear()
            self.plot_waveform()
        except pygame.error as e:
            # If loading fails, handle the error
            print(f"Failed to load sound file '{self.sound_file}': {e}")
            return None

    def reduce_samples(self, factor):
        #  throw out every 2nd sample
        signal_red = self.audio_signal[np.mod(np.arange(self.audio_signal.size), 2) != 0]
        # again throw out every 2nd sample for x-factor times
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
        wf_widget_plot_handle = self.waveform_widget.plot(time_red, signal_red,
                                                          pen=pg.mkPen(QColor(116, 173, 158), width=1))
        # wf_widget_plot_handle.setDownsampling(auto=False, ds=5)
        self.waveform_widget.setBackground(QColor(48, 74, 67))
        self.waveform_widget.showAxis('bottom')
        self.cursor = InfiniteLine(pos=self.cursor_position, angle=90, pen='r')
        self.waveform_widget.addItem(self.cursor)
        self.waveform_widget.plotItem.setMouseEnabled(y=False)  # zoom only in x
        self.waveform_widget.addItem(self.label_cursor)
        self.create_dummy_lines_in_waveform()
        self.update_marker_plot_data()

        # Debug info - plot duration
        duration = int((time.time() - starttime) * 100) / 100
        print(f"Plotting waveform finisehd after {duration} s.")

    def create_dummy_lines_in_waveform(self):
        # Create vertical dummy lines for each marker
        for c in range(len(self.marker_list.List)):
            temp = InfiniteLine(pos=0, angle=90, pen='b')
            self.lst_markers_plt_h.append(temp)
            self.waveform_widget.addItem(temp)

        #Re-add the cursor label to keep it on top
        self.waveform_widget.removeItem(self.label_cursor)
        self.waveform_widget.addItem(self.label_cursor)

    # Thread function with precision timer
    def update_cursor_pos_loop(self):
        next_call = time.perf_counter()

        while not stop_event.is_set():
            self.update_cursor_pos()  # ← Replace with your function
            next_call += cursor_thread_interval
            delay = next_call - time.perf_counter()
            if delay > 0:
                time.sleep(0.010)
            else:
                # We're late — skip sleep to catch up
                print(f"⚠ Missed interval by {-delay * 1000:.2f} ms")

    def update_cursor_pos(self):
        if self.cursor is not None:
            try:
                self.cursor_position = mixer.music.get_pos() / 1000 + self.music_startpoint_offset
            except:
                print("Mixer not initialized")
            self.cursor.setPos(self.cursor_position)

    def update_marker_plot_data(self):
        # Find closest marker
        closest_marker, unused = self.marker_list.find_nearest_to_time(self.cursor_position * 1000)

        # Draw every marker in the list
        if len(self.marker_list.List) > 0 and len(self.lst_markers_plt_h) > 0:
            for index in range(len(self.marker_list.List)):
                m_pos = self.marker_list.get_marker_time_ms_by_index(index) / 1000  # marker
                if m_pos > 0:
                    self.lst_markers_plt_h[index].setPos(m_pos)

                    # Find/Draw closest marker in orange
                    if index == closest_marker:  # mark the closest marker orange
                        self.label_cursor.setText(str(index)) # write index number as string in the plot
                        self.label_cursor.setPos(m_pos, 0)
                        self.lst_markers_plt_h[index].setPen('y', width = 3)
                        # There is a problem, that the closest marker in yellow is overdrawn in blue
                    else:
                        self.lst_markers_plt_h[index].setPen('b')

    def start_animation(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QGuiApplication.instance().exec()

    def animation(self):
        # timer_cursor = QtCore.QTimer()
        # timer_cursor.timeout.connect(self.update_cursor_pos)
        # timer_cursor.start(100)
        # timer_clock = QtCore.QTimer()
        # timer_clock.timeout.connect(self.clock)
        # timer_clock.start(50)
        timer_info_table = QtCore.QTimer()
        timer_info_table.timeout.connect(self.update_gui_slow)
        timer_info_table.start(100)
        #timer_send = QtCore.QTimer()
        # timer_send.timeout.connect(self.send_marker)
        # timer_send.start(2)
        self.start_animation()

    def refresh_marker_table(self):
        print("Refresh Table")
        try:
            self.table1.cellChanged.disconnect(self.on_cell_changed)
        except:
            print("Not yet connected")
        # self.table1.clear()
        self.table1.setRowCount(len(self.marker_list.List))
        row_counter = 0
        # Update color of status and background color of color column
        for rows in self.marker_list.List:
            item_counter = 0
            for item in rows:
                widget = QtWidgets.QTableWidgetItem(str(item))
                # "Color" for mode 1 and "Picture" for mode 2
                if item_counter == 3:
                    if item == '1':
                        widget = QtWidgets.QTableWidgetItem('Color')
                    if item == '2':
                        widget = QtWidgets.QTableWidgetItem('Picture')
                # Status Background
                if item == "False":
                    widget.setBackground(QColor(189, 31, 0))
                elif item == "True":
                    widget.setBackground(QColor(0, 176, 47))
                # Color column - Background as value
                if item_counter == 5 and int(item) != 0:
                    r, g, b = colorsys.hsv_to_rgb(int(item) / 255, 1, 1)
                    widget.setBackground(QColor(int(r * 255), int(g * 255), int(b * 255), 100))

                self.table1.setItem(row_counter, item_counter, widget)

                item_counter = item_counter + 1
            row_counter = row_counter + 1
        # Tweak to update
        self.table1.setRowCount(len(self.marker_list.List) + 1)
        set_column_not_editable(self.table1, 0)
        set_column_not_editable(self.table1, 3)

    def create_info_table(self):
        self.tableWidget.setRowCount(len(receiver_ids))
        for r in range(len(receiver_ids)):
            self.tableWidget.setItem(r, 0, QtWidgets.QTableWidgetItem("LED Poi " + str(r + 1)))
            self.tableWidget.setItem(r, 1, QtWidgets.QTableWidgetItem(str(self.arduino.voltages[r]) + " V"))
            self.tableWidget.setItem(r, 2, QtWidgets.QTableWidgetItem(str(self.arduino.signal_strength[r]) + " %"))

    def update_gui_slow(self):
        if self.arduino.signal_strength_test_active:
            self.arduino.receive()

        # Info table with voltages and signal strength
        for r in range(len(receiver_ids)):
            item = self.tableWidget.item(r, 1)
            item.setText(str(truncate(self.arduino.voltages[r], 2)) + " V")
            item = self.tableWidget.item(r, 2)
            item.setText(str(self.arduino.signal_strength[r]) + " %")

        # Update brightness slider label
        self.label_brightness.setText(str(self.brightnessSlider.value()))
        self.label_color.setText(str(self.colorSlider.value()))
        r, g, b = colorsys.hsv_to_rgb(self.colorSlider.value() / 255, 1, 1)
        self.label_color.setStyleSheet(
            "background-color: rgb(" + str(r * 255) + ", " + str(g * 255) + ", " + str(b * 255) + ")")

        # update velocity slider label
        self.label_velocity.setText(str(self.velocitySlider.value()) + " ms")

        # Update markers in plot
        self.update_marker_plot_data()

    # Refresh status in table from false to true
    def paint_status_in_table_green(self, row_index):
        self.table1.setRowCount(len(self.marker_list.List))
        # Color for Status False (Red) and True (Green)
        status = self.marker_list.List[int(row_index)][7]
        if status == "True":
            widget = QtWidgets.QTableWidgetItem(status)
            widget.setBackground(QColor(0, 176, 47))
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
            self.table1.cellChanged.connect(self.on_cell_changed)
        # Start - Running
        else:
            print("Music play")
            try:
                self.table1.cellChanged.disconnect(self.on_cell_changed)

            except:
                print("Not yet connected")

            self.running = True
            self.stop_watch_start = time.perf_counter()
            self.pushButton.setText("Stop")

            # Play Music
            if self.paused:
                mixer.music.unpause()
                self.paused = False
                print("Music resume")
            else:
                # mixer.music.play(-1, self.music_startpoint)
                mixer.music.play()
                print("Music Play")

    # Thread function with precision timer
    def send_marker_loop(self):
        next_call = time.perf_counter()

        while not stop_event.is_set():
            self.send_marker()  # ← Replace with your function
            next_call += send_marker_thread_intervall
            delay = next_call - time.perf_counter()
            if delay > 0:
                time.sleep(0.001)
            else:
                # We're late — skip sleep to catch up
                print(f"⚠ Missed interval by {-delay * 1000:.2f} ms")

    def send_marker(self):
        if self.checkBox.isChecked() and self.running:
            list_m = self.marker_list.get_marker_list()
            if self.old_mixer_pos != mixer.music.get_pos():
                #print(f"Jitter: {mixer.music.get_pos() - self.old_mixer_pos}")
                avg, max = calc_jitter_info(mixer.music.get_pos() - self.old_mixer_pos)
                self.label_14.setText(str(truncate(max, 2)))
                self.label_16.setText(str(truncate(avg, 2)))
                # starttime = time.time_ns()
                # rows -> markers
                index = 0
                for r in list_m:
                    ids = r[2]
                    mode = int(r[3])
                    picture = int(r[4])
                    color = int(r[5])
                    velocity = int(r[6])
                    send_status = r[-1]
                    saturation = 0
                    if send_status == "False":
                        # decrypt time
                        ms = self.marker_list.get_marker_time_ms(r)
                        # Not send marker if older than 50 ms -> somehow program gets interrupted sometimes for up to 24 ms
                        current_time = mixer.music.get_pos() + self.music_startpoint_offset * 1000
                        if ms < current_time < (ms + 50):  # 0 <-> 50
                            # starttime_serial_send = time.time_ns()
                            if ids != "ALL": # -> single receiver
                                self.arduino.send(mode, ids, picture, color, saturation,
                                                  self.brightnessSlider.value(),
                                                  velocity)
                                #time.sleep(0.0001)
                            else:
                                # Broadcast to all receivers
                                for ids in receiver_ids:
                                    self.arduino.send(mode, ids, picture, color, saturation,
                                                      self.brightnessSlider.value(), velocity)
                                    #time.sleep(0.0001)
                            # print("Duration for serial_send: " + str(
                            # (time.time_ns() - starttime_serial_send) / 1000000) + " ms")
                            # set marker sent_status "True"
                            self.label_3.setText(
                                f"Channel: {ids}\n"
                                + f"Picture Nr.: {picture}\n"
                                + f"Color/Hue.: {color}\n"
                                + f"Saturation.: {saturation}\n"
                                + f"Brightness: {self.brightnessSlider.value()}\n"
                                + f"Velocity.: {velocity}"
                            )
                            r[-1] = "True"
                            self.paint_status_in_table_green(index)  # used to be time problematic !
                    index += 1
                self.old_mixer_pos = mixer.music.get_pos()
            else:
                time.sleep(0.001)
            # time.sleep(0.001)
            # print(f"Duration for Thread send_marker: {(time.time_ns() - starttime) / 1000} us")
            # print(starttime)
            # print(time.time_ns() / 1000000 - self.time_stamp)
            # self.time_stamp = time.time_ns() / 1000000


    def send_test_button_data(self):
        mode_t = 0
        saturation = 255
        ids = self.receiverBox.currentText()
        if self.spinBox.value() == 0:
            mode_t = COLOR_MODE
        else:
            mode_t = PICTURE_MODE

        if ids != "ALL":
            self.arduino.send(mode_t, int(self.receiverBox.currentText()), self.spinBox.value(),
                              self.colorSlider.value(),
                              saturation, self.brightnessSlider.value(), self.velocitySlider.value())
        else:
            # Broadcast to all receivers
            for ids in range(6):
                self.arduino.send(mode_t, ids + 1, self.spinBox.value(), self.colorSlider.value(), saturation,
                                  self.brightnessSlider.value(), self.velocitySlider.value())

        self.label_3.setText(
            f"Channel: {ids}\n"
            + f"Picture Nr.: {self.spinBox.value()}\n"
            + f"Color/Hue.: {self.colorSlider.value()}\n"
            + f"Saturation.: {saturation}\n"
            + f"Brightness: {self.brightnessSlider.value()}\n"
            + f"Velocity.: {self.velocitySlider.value()}"
        )

    def reset(self):
        self.pushButton.setText("Start")
        try:
            self.table1.cellChanged.disconnect(self.on_cell_changed)
        except:
            print("Not yet connected")
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
            self.arduino.send(2, ids, 0, 0, 0, 0, 0)
        self.refresh_marker_table()
        self.table1.cellChanged.connect(self.on_cell_changed)
        delete_jitter_values() # Clear values for jitter calc

    def set_marker_picture(self):
        self.marker_list.add_marker(self.current_index, format_time_string(self.passed),
                                    self.receiverBox.currentText(), str(PICTURE_MODE),
                                    self.spinBox.value(), self.colorSlider.value(), self.velocitySlider.value(), False)

        # self.lst_markers_plt_h.append(self.waveform_widget.plot([0, 0], [0, 0], pen='b'))
        temp = InfiniteLine(pos=0, angle=90, pen='b')
        self.lst_markers_plt_h.append(temp)
        self.waveform_widget.addItem(temp)

        self.update_marker_plot_data()
        self.refresh_marker_table()
        self.current_index += 1

    def set_marker_color(self):
        self.marker_list.add_marker(self.current_index, format_time_string(self.passed),
                                    self.receiverBox.currentText(), str(COLOR_MODE),
                                    0, self.colorSlider.value(), 0, False)
        #self.lst_markers_plt_h.append(self.waveform_widget.plot([0, 0], [0, 0], pen='b'))
        temp = InfiniteLine(pos=0, angle=90, pen='b')
        self.lst_markers_plt_h.append(temp)
        self.waveform_widget.addItem(temp)

        self.update_marker_plot_data()
        self.refresh_marker_table()
        self.current_index += 1

    def set_marker_off(self):
        self.marker_list.add_marker(self.current_index, format_time_string(self.passed),
                                    self.receiverBox.currentText(), PICTURE_MODE,
                                    0, 0, 0, False)
        #self.lst_markers_plt_h.append(self.waveform_widget.plot([0, 0], [0, 0], pen='b'))
        temp = InfiniteLine(pos=0, angle=90, pen='b')
        self.lst_markers_plt_h.append(temp)
        self.waveform_widget.addItem(temp)

        self.update_marker_plot_data()
        self.refresh_marker_table()
        self.current_index += 1

    def delete_marker(self):
        # delete nearest marker
        # find nearest marker
        index = self.marker_list.delete_next_marker_to_time_ms(self.cursor_position * 1000)
        if index > -1:
            invisible_pen = pg.mkPen((0, 0, 0, 0))  # transparent pen
            self.lst_markers_plt_h[index].setPen(invisible_pen)  # delete marker from plot
            self.lst_markers_plt_h.pop(index)
            self.refresh_marker_table()
            self.current_index -= 1

    def clock_loop(self):
        next_call = time.perf_counter()

        while not stop_event.is_set():
            self.clock()  # ← Replace with your function
            next_call += clock_thread_intervall
            delay = next_call - time.perf_counter()
            if delay > 0:
                time.sleep(0.005)
            else:
                # We're late — skip sleep to catch up
                print(f"⚠ Missed interval by {-delay * 1000:.2f} ms")

    def clock(self):
        try:
            self.passed = mixer.music.get_pos() / 1000.0 + self.music_startpoint_offset
        except:
            print("Couldn´t get mixer pos - error")
        if self.passed < 0:
            self.passed = 0
        self.label.setText(format_time_string(self.passed))

    def save_serial_config(self):
        self.arduino.serialPort.setPort(self.arduino.ports_COMs[self.comboBox_2.currentIndex()])
        time.sleep(2.5)
        self.arduino.go_all_black()

    def exit(self):
        if self.arduino.serialPort is not None:
            self.arduino.go_all_black()
            self.arduino.serialPort.close()
        else:
            print("No serial connection established")
        time.sleep(0.100)
        sys.exit()


def main():
    mixer.init()
    app = QApplication([])
    # Apply the dark theme stylesheet
    app.setStyleSheet(dark_theme)

    # Create GUI
    window = MyGUI()

    # Create Threads
    send_marker_thread = threading.Thread(target=window.send_marker_loop, daemon=True)
    clock_loop_thread = threading.Thread(target=window.clock_loop, daemon=True)
    update_cursor_thread = threading.Thread(target=window.update_cursor_pos_loop, daemon=True)
    # Start Threads
    send_marker_thread.start()
    clock_loop_thread.start()
    update_cursor_thread.start()

    window.setWindowIcon(QIcon(resource_path('icon_LS_v2_128_128.ico')))
    window.animation()

    # Run the GUI
    try:
        app.exec()
    finally:
        stop_event.set()  # Signal all loops to stop
        send_marker_thread.join()
        clock_loop_thread.join()
        update_cursor_thread.join()
        print("Threads stopped cleanly.")


if __name__ == "__main__":
    main()
    # on exit
    # f.close()
    ctypes.windll.winmm.timeEndPeriod(1)
