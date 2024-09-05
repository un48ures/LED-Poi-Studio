import time
from pydub import AudioSegment
import wave
import numpy as np


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
