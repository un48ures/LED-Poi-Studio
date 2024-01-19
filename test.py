import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QListWidget, QInputDialog
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap
from pydub import AudioSegment
import pygame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas



class AudioPlayerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.mixer = pygame.mixer
        self.mixer.init()

        self.audio = None
        self.playing = False
        self.current_position = 0
        self.markers = []

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.create_widgets()

    def create_widgets(self):
        layout = QVBoxLayout(self.central_widget)

        # Buttons
        self.load_button = QPushButton("Load MP3", self)
        self.load_button.clicked.connect(self.load_mp3)
        layout.addWidget(self.load_button)

        self.play_button = QPushButton("Play", self)
        self.play_button.clicked.connect(self.play_music)
        layout.addWidget(self.play_button)

        self.pause_button = QPushButton("Pause", self)
        self.pause_button.clicked.connect(self.pause_music)
        layout.addWidget(self.pause_button)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.clicked.connect(self.stop_music)
        layout.addWidget(self.stop_button)

        # Waveform
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        # Label for current play position
        self.position_label = QLabel("Current Position: 00:00", self)
        layout.addWidget(self.position_label)

        # Markers list
        self.markers_list = QListWidget(self)
        layout.addWidget(self.markers_list)

        # Add Marker button
        self.add_marker_button = QPushButton("Add Marker", self)
        self.add_marker_button.clicked.connect(self.add_marker)
        layout.addWidget(self.add_marker_button)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_audio_position)

    def load_mp3(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load MP3", "", "MP3 files (*.mp3)")
        if file_path:
            self.audio = AudioSegment.from_mp3(file_path)
            self.update_waveform()

    def play_music(self):
        if self.audio and not self.playing:
            self.playing = True
            self.update_audio_position()
            self.timer.start(100)

    def pause_music(self):
        if self.playing:
            self.mixer.music.pause()

    def stop_music(self):
        if self.playing:
            self.playing = False
            self.mixer.music.stop()
            self.current_position = 0
            self.update_position_label()
            self.timer.stop()

    def update_audio_position(self):
        if self.playing and self.current_position < len(self.audio):
            temp_wav_filename = "temp.wav"
            self.audio[self.current_position:self.current_position + 100].export(temp_wav_filename, format="wav")
            self.mixer.music.load(temp_wav_filename)
            self.mixer.music.play(start=0)

            # Wait for playback to complete
            pygame.time.Clock().tick(30)

            self.current_position += 100
            self.update_position_label()
            self.draw_markers()
            self.canvas.draw()

        else:
            self.stop_music()

    def update_waveform(self):
        samples = self.audio.get_array_of_samples()
        self.ax.clear()
        self.ax.plot(samples)
        self.draw_markers()
        self.canvas.draw()

    def add_marker(self):
        if self.audio:
            ms_position = self.current_position
            picture_nr, ok = QInputDialog.getInt(self, "Enter Picture Nr.", "Picture Nr.:")
            if ok:
                channel_value, ok = QInputDialog.getInt(self, "Enter Channel Value", "Channel Value:")
                if ok:
                    self.markers.append((ms_position, picture_nr, channel_value))
                    self.update_markers_list()

    def draw_markers(self):
        for marker in self.markers:
            ms_position = marker[0]
            self.ax.axvline(x=ms_position, color='r', linestyle='--')

    def update_position_label(self):
        minutes = int(self.current_position // 60000)
        seconds = int((self.current_position % 60000) // 1000)
        position_str = f"Current Position: {minutes:02}:{seconds:02}"
        self.position_label.setText(position_str)

    def update_markers_list(self):
        self.markers_list.clear()
        for marker in self.markers:
            self.markers_list.addItem(f"{marker[0]} ms - Picture Nr.: {marker[1]}, Channel Value: {marker[2]}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = AudioPlayerApp()
    player.setGeometry(100, 100, 800, 600)
    player.show()
    sys.exit(app.exec_())
