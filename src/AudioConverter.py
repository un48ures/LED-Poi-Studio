import time
from pydub import AudioSegment
import wave
import numpy as np
import os


class AudioConverter:
    def __init__(self):
        self.starttime = 0

    def convert_mp3_to_array(self, input_file):
        print("Started WAV Conversion")
        self.starttime = time.time()
        sound = AudioSegment.from_mp3(input_file)
        sound.export('converted.wav', format="wav")
        with wave.open('./converted.wav', 'r') as wav_file:
            signal = wav_file.readframes(-1)

            width = wav_file.getsampwidth()  # Bytes pro Sample
            if width == 1:
                dtype = np.uint8
            elif width == 2:
                dtype = np.int16
            elif width == 4:
                dtype = np.int32
            else:
                raise ValueError("Unsupported sample width")

            signal = np.frombuffer(signal, dtype=dtype)

            # Get time from indices
            fs = wav_file.getframerate()
            time_x = np.linspace(0, len(signal) / 2 / fs, num=int(len(signal) / 2))
        print("Conversion of " + str(input_file) + " done!")
        duration = (int((time.time() - self.starttime) * 100)) / 100  # truncate to 2 decimals
        print("Conversion took: " + str(duration) + " s")
        print("Audio duration: " + str(int(len(signal) / fs / 60)) + ' min ' + str(int(len(signal) / fs % 60)) + ' s')
        return time_x, signal


def find_mp3_files(directory):
    mp3_files = []
    # Only list files in the given directory (no recursion)
    for file in os.listdir(directory):
        # Build full path
        full_path = os.path.join(directory, file)
        # Check if it is a file and ends with .mp3
        if os.path.isfile(full_path) and file.lower().endswith(".mp3"):
            mp3_files.append(full_path)

    # If no MP3 files found, append empty string
    if len(mp3_files) == 0:
        mp3_files.append('')

    return mp3_files
