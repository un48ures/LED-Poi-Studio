import time
import threading
import serial
import os
import os.path

from PyQt5 import uic
from PyQt5.QtWidgets import *

from pygame import mixer

# Find connected Ports for Arduino
import serial.tools.list_ports as port_list

ports = list(port_list.comports())
for p in ports:
    print(p)
serialPort = serial.Serial(
    port="COM11", baudrate=115200, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE
)

receiver_ids = [1, 2, 3, 4, 5, 6]
mode = 2 #Picture Mode
brightness = 2 #set global brightness
saturation = 0 #some not used default values
velocity = 0 #some not used default values


class MarkerList:
    def __init__(self):
        self.ListMarkers = []
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
        self.ListMarkers = backup_details
        self.f.close()

    def add_marker(self, number, time_stamp, ID, picture, send_status):
        self.ListMarkers.append([number, time_stamp, ID, picture, send_status])
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
                output += f"\nMarker {x[0]} - Time: {x[1]} - ID {x[2]} - Picture: {x[3]} - Status Sent: {x[4]}"
        return output

    def delete_last(self):
        self.ListMarkers.pop()
        self.update_backup_file()
        print("Last Marker deleted")

    def reset_send_status_all(self):
        for x in self.ListMarkers:
            x[4] = "False"

    def get_marker(self):
        return self.ListMarkers

    def set_marker_sent_status(self, marker_number, status_new):
        for lm in self.ListMarkers:
            if lm[0] == marker_number:
                lm[-1] = status_new
                print("Set sent status of marker " + str(marker_number) + " to " + str(status_new))

    def get_highest_marker_number(self):
        if len(self.ListMarkers) > 0:
            print("ListMarkers len > 0")
            print(self.ListMarkers[-1][0])
            return int(self.ListMarkers[-1][0])
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
        #self.label_2.setStyleSheet("border: 10px solid transparent")
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
        # Start - Running
        else:
            self.running = True
            self.pushButton.setText("Stop")
            self.pushButton_2.setEnabled(False)
            threading.Thread(target=self.stopwatch).start()
            if self.checkBox.isChecked():
                # Check for next marker to be sent
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
            #print(f"current time {current_time_ms}")
            list_m = self.marker_list.get_marker()

            # rows -> markers
            for r in list_m:
                # print("test")
                ms = int(r[1][10]) * 10 + int(r[1][9]) * 100 + int(r[1][7]) * 1000 + int(r[1][6]) * 10000 + int(
                    r[1][4]) * 60 * 1000
                send_status = r[4]
                print(f"For Marker {r[0]} the timestamp is: {ms} ms and sent status is: {send_status}")
                # Send marker if current time is over planned time (+500ms delay compensation)
                # Not send marker if older than 1 second
                if ms < current_time_ms + 500 < ms + 1000 and send_status == "False":
                    # Send marker values
                    print("Current time is over timestamp of Marker ----> Send to Arduino")
                    picture = int(r[3])

                    if r[2] != "ALL":
                        ids = r[2]
                        self.arduino.send(mode, ids, picture, saturation, brightness, velocity)
                        self.label_3.setText(
                            "Last sent message:\n\n" + f"Channel: {id}\n" + f"Picture Nr.: {picture}\n" +
                            f"Brightness: {brightness}\n\n")
                    else:
                        # Broadcast to all Channels 20 30 40 50 60 70
                        for ids in receiver_ids:
                            self.arduino.send(mode, ids, picture, saturation, brightness, velocity)
                        self.label_3.setText(
                            "Last sent message:\n\n" + "Channel: ALL\n" + f"Picture Nr.: {picture}\n" +
                            f"Brightness: {brightness} \n\n")


                        # set marker sent_status "True"
                    self.marker_list.set_marker_sent_status(r[0], True)
                self.label_2.setText(self.marker_list.output_list_as_string())

    def reset(self):
        self.pushButton.setText("Start")
        self.pushButton_2.setEnabled(False)
        self.label.setText("00:00:00:00")
        # self.label_2.setText("Markers: ")
        # self.lap = 1
        mixer.music.stop()
        self.paused = False
        print("Music stop")
        self.marker_list.reset_send_status_all()
        self.passed = 0
        # Make all LEDs go black
        for ids in receiver_ids:
            self.arduino.send(mode, ids, 0, saturation, 0, velocity)
        # Update List of Markers on GUI
        self.label_2.setText(self.marker_list.output_list_as_string())

    def set_marker(self):
        self.marker_list.add_marker(self.lap, self.format_time_string(self.passed), self.comboBox.currentText(),
                                    self.spinBox.value(), False)
        self.label_2.setText(self.marker_list.output_list_as_string())
        self.lap += 1

    def delete_marker(self):
        if self.lap > 0:
            self.lap -= 1
            self.marker_list.delete_last()
            self.label_2.setText(self.marker_list.output_list_as_string())

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
        print("byte1 = " + str(byte1) + "(Mode)")
        print("byte2 = " + str(byte2) + "(receiver_id)")
        print("byte3 = " + str(byte3) + "(picture/hue)")
        print("byte4 = " + str(byte4) + "(saturation)")
        print("byte5 = " + str(byte5) + "(brightness/value)")
        print("byte6 = " + str(byte6) + "(velocity)")
        serialPort.write(chr(byte1).encode('latin_1'))
        serialPort.write(chr(byte2).encode('latin_1'))
        serialPort.write(chr(byte3).encode('latin_1'))
        serialPort.write(chr(byte4).encode('latin_1'))
        serialPort.write(chr(byte5).encode('latin_1'))
        serialPort.write(chr(byte6).encode('latin_1'))


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
