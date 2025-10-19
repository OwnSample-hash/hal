import numpy as np
from PySide6.QtCore import QObject, Signal
import sounddevice as sd


class SignalCommunicator(QObject):
    update_plot = Signal(tuple)


class AudioGen(QObject):
    finished = Signal()

    def __init__(self, plot_graph, device_menu, samplerate=44100):
        super().__init__()
        self.samplerate = samplerate
        self.phase = 0.0
        self.is_playing = True
        self.stream = None
        self.time_offset = [0.0]
        self.plot_graph = plot_graph
        self.device_menu = device_menu
        self.wave_multiplier = 1.0
        self.communicator = SignalCommunicator()

    def audio_callback(self, *args):
        outdata, frames, *_ = args
        t = np.arange(frames) / self.samplerate
        self.device_menu.mutex.lock()
        if self.device_menu.active_notes:
            waves = [
                np.sin(2 * np.pi * freq * (t + self.time_offset[0]))
                for freq in self.device_menu.active_notes.values()
            ]
            wave = np.sum(waves, axis=0) / len(waves)
        else:
            wave = np.zeros(frames)
        self.device_menu.mutex.unlock()
        self.communicator.update_plot.emit(
            (t + self.time_offset[0], wave * self.wave_multiplier)
        )
        outdata[:] = wave.reshape(-1, 1)
        self.time_offset[0] += frames / self.samplerate

    def start(self):
        print("Starting audio stream")
        self.is_playing = True
        self.stream = sd.OutputStream(
            callback=self.audio_callback, channels=1, samplerate=self.samplerate
        )
        self.stream.start()

    def stop(self):
        self.is_playing = False
        if self.stream:
            self.stream.stop()
            self.stream.close()


# vim: set ft=python ts=4 sw=4 sts=4 et ai:
