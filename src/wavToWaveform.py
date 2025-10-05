import matplotlib.pyplot as plt
import numpy as np
import wave

file = 'test_song.wav'

with wave.open(file, 'r') as wav_file:
    # Extract Raw Audio from Wav File
    signal = wav_file.readframes(-1)
    signal = np.fromstring(signal,'int32')

    # Split the data into channels
    channels = [[] for channel in range(wav_file.getnchannels())]
    for index, datum in enumerate(signal):
        channels[index % len(channels)].append(datum)

    # Get time from indices
    fs = wav_file.getframerate()
    Time = np.linspace(0, len(signal) / len(channels) / fs, num=int(len(signal) / len(channels)))

    # Plot
    # plt.figure(1)
    # plt.title('Signal Wave...')
    # for channel in channels:
    #     plt.plot(Time, channel)
    # plt.show()


class CursorClass(object):
    def __init__(self, ax, x, y):
        self.ax = ax
        self.ly = ax.axvline(color='yellow', alpha=0.5)
        #self.marker, = ax.plot([0], [0], marker="o", color="red", zorder=3)
        self.x = x
        self.y = y
        #self.txt = ax.text(0.7, 0.9, '')


    def mouse_event(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            indx = np.searchsorted(self.x, [x])[0]
            x = self.x[indx]
            y = self.y[indx]
            self.ly.set_xdata(x)
            #self.marker.set_data([x], [y])
            #self.txt.set_text('x=%1.2f, y=%1.2f' % (x, y))
            #self.txt.set_position((x, y))
            self.ax.figure.canvas.draw_idle()
        else:
            return


fig, ax = plt.subplots()
cursor = CursorClass(ax, Time, channels[0])
cid = plt.connect('motion_notify_event', cursor.mouse_event)
ax.plot(Time, channels[0], lw=0.5, color='grey')
plt.show()
