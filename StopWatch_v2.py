import time
import threading
import serial
import os
import os.path

from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.uic.properties import QtWidgets
from PyQt5 import QtWidgets
from PyQt5.QtGui import QColor

from pygame import mixer

# Find connected Ports for Arduino
import serial.tools.list_ports as port_list

ports = list(port_list.comports())
ports_names = []
ports_COMs = []
for p in ports:
    print(p)
    ports_COMs.append(p[0])
    ports_names.append(p[1])

serialPort = serial.Serial(
    port="COM1", baudrate=115200, bytesize=8, write_timeout=1, timeout=2, stopbits=serial.STOPBITS_ONE
)

receiver_ids = [1, 2, 3, 4, 5, 6]
mode = 2  # Picture Mode
brightness = 2  # set global brightness
saturation = 0  # some not used default values
velocity = 0  # some not used default values


class MarkerList:
    def __init__(self):
        self.List = []
        if os.path.isfile('./markers_backup.txt'):
            print("file is present")
            self.f = open("markers_backup.txt", "r")
        else:
            self.f = open("markers_backup.txt", "w")
        self.reload_backup()

    def reload_backup(self):
        self.f = open("markers_backup.txt", "r")
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
        self.f = open("markers_backup.txt", "w")
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

    def set_marker_sent_status(self, marker_number, status_new):
        for lm in self.List:
            if lm[0] == marker_number:
                lm[-1] = status_new
                print("Set sent status of marker " + str(marker_number) + " to " + str(status_new))

    def get_highest_marker_number(self):
        if len(self.List) > 0:
            print("ListMarkers len > 0")
            print(self.List[-1][0])
            return int(self.List[-1][0])
        else:
            return 0


class MyGUI(QMainWindow):

    def __init__(self):
        super(MyGUI, self).__init__()
        uic.loadUi("stopwatch3.ui", self)
        self.show()
        self.running = False
        self.started = False
        self.passed = 0
        self.previous_passed = 0
        self.paused = False
        self.arduino = Arduino()
        self.marker_list = MarkerList()
        self.lap = self.marker_list.get_highest_marker_number() + 1
        self.pushButton.clicked.connect(self.start_stop)
        self.pushButton_2.clicked.connect(self.reset)
        self.pushButton_3.clicked.connect(self.set_marker)
        self.pushButton_4.clicked.connect(self.delete_marker)
        self.pushButton_5.clicked.connect(self.save_serial)
        self.comboBox_2.addItems(ports_names)
        # self.label_2.setStyleSheet("border: 10px solid transparent")
        # self.label_2.setText(self.marker_list.output_list_as_string())
        # self.label_2.setStyleSheet("background-color:grey border: 10px solid transparent")
        self.refresh_table()

    def refresh_table(self):
        self.table1.setRowCount(len(self.marker_list.List))
        row_counter = 0
        item_counter = 0
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

    def start_stop(self):
        # Stop
        if self.running:
            self.running = False
            self.pushButton.setText("Resume")
            self.pushButton_2.setText("Reset")
            self.pushButton_2.setEnabled(True)
            mixer.music.pause()
            print("Music pause")
            self.paused = True
        # Start - Running
        else:
            self.running = True
            self.pushButton.setText("Stop")
            self.pushButton_2.setEnabled(False)
            threading.Thread(target=self.stopwatch).start()
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
        while self.running:
            current_time_ms = int(mixer.music.get_pos())  # current Time
            # print(f"current time {current_time_ms}")
            list_m = self.marker_list.get_marker()

            # rows -> markers
            for r in list_m:
                # print("test")
                ms = int(r[1][10]) * 10 + int(r[1][9]) * 100 + int(r[1][7]) * 1000 + int(r[1][6]) * 10000 + int(
                    r[1][4]) * 60 * 1000
                send_status = r[4]
                # print(f"For Marker {r[0]} the timestamp is: {ms} ms and sent status is: {send_status}")
                # Send marker if current time is over planned time (+500ms delay compensation)
                # Not send marker if older than 1 second
                if ms < current_time_ms + 500 < ms + 1000 and send_status == "False":
                    # Send marker values
                    # print("Current time is over timestamp of Marker ----> Send to Arduino")
                    picture = int(r[3])

                    if r[2] != "ALL":
                        ids = r[2]
                        self.arduino.send(mode, ids, picture, saturation, brightness, velocity)
                        self.label_3.setText(
                            "Last sent message:\n\n" + f"Channel: {id}\n" + f"Picture Nr.: {picture}\n" +
                            f"Brightness: {brightness}\n\n")
                    else:
                        # Broadcast to all receivers
                        for ids in receiver_ids:
                            self.arduino.send(mode, ids, picture, saturation, brightness, velocity)
                        self.label_3.setText(
                            "Last sent message:\n\n" + "Channel: ALL\n" + f"Picture Nr.: {picture}\n" +
                            f"Brightness: {brightness} \n\n")

                        # set marker sent_status "True"
                    self.marker_list.set_marker_sent_status(r[0], "True")
                    # self.label_2.setText(self.marker_list.output_list_as_string())
                    starttime = time.time_ns()
                    self.refresh_table()
                    endtime = time.time_ns()
                    print("End Time: " + str((endtime - starttime)) + " ns")
                    print("Send Marker Refresh Table")

    def reset(self):
        self.pushButton.setText("Start")
        self.pushButton_2.setEnabled(False)
        self.label.setText("00:00:00:00")
        mixer.music.stop()
        self.paused = False
        print("Music stop")
        self.marker_list.reset_send_status_all()
        self.passed = 0
        # Make all LEDs go black
        for ids in receiver_ids:
            self.arduino.send(mode, ids, 0, saturation, 0, velocity)
        # Update List of Markers on GUI
        # self.label_2.setText(self.marker_list.output_list_as_string())
        self.refresh_table()

    def set_marker(self):
        self.marker_list.add_marker(self.lap, self.format_time_string(self.passed), self.comboBox.currentText(),
                                    self.spinBox.value(), False)
        # self.label_2.setText(self.marker_list.output_list_as_string())
        self.refresh_table()
        self.lap += 1

    def delete_marker(self):
        if self.lap > 0:
            self.lap -= 1
            self.marker_list.delete_last()
            # self.label_2.setText(self.marker_list.output_list_as_string())
            self.refresh_table()

    def format_time_string(self, time_passed):
        secs = time_passed % 60
        mins = time_passed // 60
        hours = mins // 60
        return f"{int(hours):02d}:{int(mins):02d}:{int(secs):02d}:{int((self.passed % 1) * 100):02d}"

    def stopwatch(self):
        start = time.time()
        if self.started:
            until_now = self.passed
        else:
            until_now = 0
            self.started = True

        while self.running:
            self.passed = time.time() - start + until_now
            # self.label.setText(self.format_time_string(self.passed))
            self.label.setText(self.format_time_string((int(mixer.music.get_pos())) // 1000))

    def save_serial(self):
        print(self.comboBox_2.currentIndex())
        print(ports_COMs[self.comboBox_2.currentIndex()])
        serialPort.setPort(ports_COMs[self.comboBox_2.currentIndex()])

class Arduino:
    def __init__(self):
        self.bytes = [0]

    # def send(self, channel, picturenum, brightness):
    def send(self, mode, receiver_id, picture_hue, saturation, brightness_value, velocity):
        byte1 = int(mode)
        byte2 = int(receiver_id)
        byte3 = int(picture_hue)
        byte4 = int(saturation)
        byte5 = int(brightness_value)
        byte6 = int(velocity)
        # print("byte1 = " + str(byte1) + "(Mode)")
        # print("byte2 = " + str(byte2) + "(receiver_id)")
        # print("byte3 = " + str(byte3) + "(picture/hue)")
        # print("byte4 = " + str(byte4) + "(saturation)")
        # print("byte5 = " + str(byte5) + "(brightness/value)")
        # print("byte6 = " + str(byte6) + "(velocity)")
        serialPort.write(chr(byte1).encode('latin_1'))
        serialPort.write(chr(byte2).encode('latin_1'))
        serialPort.write(chr(byte3).encode('latin_1'))
        serialPort.write(chr(byte4).encode('latin_1'))
        serialPort.write(chr(byte5).encode('latin_1'))
        serialPort.write(chr(byte6).encode('latin_1'))
        serialPort.reset_input_buffer()
        # serialPort.reset_output_buffer()

        # if serialPort.in_waiting > 8:
        #     # Read data out of the buffer until a carriage return / new line is found
        #     serialString = serialPort.readline()
        #     res = serialString.decode("Ascii").split()
        #     # print("after readLine")
        #
        #     # Print the contents of the serial data
        #     try:
        #         for d in res:
        #             print(d, end="")
        #         print("")
        #     except:
        #         print("Error")
        #         pass


def main():
    mixer.init()
    mixer.music.load("song.mp3")
    app = QApplication([])
    window = MyGUI()
    app.exec_()


if __name__ == "__main__":
    main()
    # on exit
    # f.close()
