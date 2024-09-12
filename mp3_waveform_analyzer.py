import sys
import time
import tkinter.filedialog
import matplotlib
import numpy as np
import wave
import sys
import pygame
import os
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QWidget, QHBoxLayout, QMainWindow, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from pydub import AudioSegment

matplotlib.use('Qt5Agg')

# 1. Step - Find Song
input_f = tkinter.filedialog.askopenfilename()

# input_f = "song.mp3"
destination_f = "test.wav"
pygame.init()
pygame.mixer.init()


def play():
    pygame.mixer.music.load(input_f)
    pygame.mixer.music.play()


def stop():
    pygame.mixer.music.stop()


def pause():
    pygame.mixer.music.pause()


def unpause():
    pygame.mixer.music.unpause()


class ConvertMp3ToWav:
    def __init__(self, input_filename, destination_filename):
        # convert wav to mp3
        sound = AudioSegment.from_mp3(input_filename)
        sound.export(destination_filename, format="wav")


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self, signal_to_plot):
        super().__init__()
        self.signal = signal_to_plot
        self.setWindowTitle("Control Center")
        layoutv = QVBoxLayout()
        layouth = QHBoxLayout()
        self.plot = MplCanvas(width=50, height=40, dpi=100)
        layoutv.addWidget(self.plot)
        button1 = QPushButton("Play")
        button2 = QPushButton("Stop")
        button1.clicked.connect(play)
        button2.clicked.connect(stop)
        self.lt = QLabel()
        self.lt.setText("Time: 00:00")
        layouth.addWidget(self.lt)
        layouth.addWidget(button1)
        layouth.addWidget(button2)
        layoutv.addLayout(layouth)
        widget = QWidget()
        widget.setLayout(layoutv)
        self.setCentralWidget(widget)

    def drawWaveForm(self):
        self.plot.axes.plot(self.signal)

    def drawCursor(self, x_position):
        self.plot.axes.axvline(x=x_position, color='r', label='axvline - full height')


class WavToWaveform():
    def __init__(self, wave_filename):
        with wave.open(wave_filename, 'r') as wav_file:
            # Extract Raw Audio from Wav File
            signal = wav_file.readframes(-1)
            signal = np.fromstring(signal, int)

            # Split the data into channels
            self.channels = [[] for channel in range(wav_file.getnchannels())]
            for index, datum in enumerate(signal):
                self.channels[index % len(self.channels)].append(datum)

            # Get time from indices
            fs = wav_file.getframerate()
            self.Time = np.linspace(0, len(signal) / len(self.channels) / fs, num=int(len(signal) / len(self.channels)))


conv = ConvertMp3ToWav(input_f, destination_f)
waveform = WavToWaveform("test.wav")
app = QtWidgets.QApplication(sys.argv)
print(waveform.Time[-1])
window = MainWindow(waveform.channels[0])
window.drawWaveForm()
window.drawCursor(pygame.mixer.music.get_pos())
window.show()
window.update()
print(pygame.mixer.music.get_busy())
if pygame.mixer.music.get_busy():
    print("busy")
    window.labeltime.setText("Time: " + str(pygame.mixer.music.get_pos()))

sys.exit(app.exec())
