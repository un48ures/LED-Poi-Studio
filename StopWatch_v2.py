import time
import threading
from typing import re

from PyQt5 import uic
from PyQt5.QtWidgets import *

from pygame import mixer


class MarkerList():
    def __init__(self):
        self.ListMarkers = []
        self.f = open("markers_backup.txt", "r")
        self.reload_backup()

    def reload_backup(self):
        str_input = self.f.read()
        backup_details = []
        [backup_details.append(b.split()) for b in str_input.splitlines()]
        print(backup_details)
        self.ListMarkers = backup_details

    def add_marker(self, number, time_stamp, channel, picture, send_status):
        self.ListMarkers.append([number, time_stamp, channel, picture, send_status])
        self.update_backup_file()

    def update_backup_file(self):
        self.f = open("markers_backup.txt", "w")
        for x in self.ListMarkers:
            for i in x:
                self.f.write(str(i) + " ")
            self.f.write("\n")
        self.f.close()

    def output_list_as_string(self):
        output = ""
        if len(self.ListMarkers) > 0:
            for x in self.ListMarkers:
                output += f"\nMarker {x[0]} - Time: {x[1]} - Channel {x[2]} - Picture: {x[3]}"
        return output

    def delete_last(self):
        self.ListMarkers.pop()
        self.update_backup_file()
        print("Last Marker deleted")

    def reset_send_status_all(self):
        for x in self.ListMarkers:
            self.ListMarkers[4] = False


class MyGUI(QMainWindow):

    def __init__(self):
        super(MyGUI, self).__init__()
        uic.loadUi("stopwatch3.ui", self)
        self.show()
        self.running = False
        self.started = False

        self.passed = 0
        self.previous_passed = 0
        self.lap = 1
        self.paused = False
        self.marker_list = MarkerList()

        self.pushButton.clicked.connect(self.start_stop)
        self.pushButton_2.clicked.connect(self.reset)
        self.pushButton_3.clicked.connect(self.set_marker)
        self.pushButton_4.clicked.connect(self.delete_marker)
        self.label_2.setStyleSheet("border: 10px solid transparent")
        self.label_2.setText(self.marker_list.output_list_as_string())
        # self.label_2.setStyleSheet("background-color:grey border: 10px solid transparent")

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
        # Start
        else:
            self.running = True
            self.pushButton.setText("Stop")
            self.pushButton_2.setEnabled(False)
            threading.Thread(target=self.stopwatch).start()
            # Play Music
            if self.paused:
                mixer.music.unpause()
                self.paused = False
                print("Music resume")
            else:
                mixer.music.play()
                print("Music Play")
            # Start with Sending to Arduino
            if self.checkBox.isChecked:
                pass

                # Check the current time of the mixer (mixer.music.getpos())
                # Check if we passed a not yet transmitted marker and send it
                # Set the transmitted marker to "sent"

    def reset(self):
        self.pushButton.setText("Start")
        self.pushButton_2.setEnabled(False)
        self.label.setText("00:00:00:00")
        # self.label_2.setText("Markers: ")
        self.lap = 1
        mixer.music.stop()
        self.paused = False
        print("Music stop")
        self.marker_list.reset_send_status_all()

    def set_marker(self):
        self.marker_list.add_marker(self.lap, self.format_time_string(self.passed), self.comboBox.currentText(),
                                    self.spinBox.value(), False)
        self.label_2.setText(self.marker_list.output_list_as_string())
        self.lap += 1

    def delete_marker(self):
        self.marker_list.delete_last()
        self.label_2.setText(self.marker_list.output_list_as_string())
        self.lap -= 1

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
