import numpy as np
from PySide6.QtCore import QObject, Signal
import sounddevice as sd


class AudioGens:
    def __getitem__(self, name):
        match name:
            case "sine":
                return self.sine
            case "sine_vibrato":
                return self.sine_vibrato
            case "square":
                return self.square
            case "sawtooth":
                return self.sawtooth
            case _:
                raise KeyError(f"Audio generator '{name}' not found.")

    def _get_available_gens(self):
        return [func for func in dir(self) if not func.startswith("_") and callable(getattr(self, func))]

    def sine(self, t, active_notes, time_offset, mod_wheel=0):
        return [
                np.sin(2 * np.pi * freq * (t + time_offset[0]))
                for freq in active_notes.values()
            ]

    def sine_vibrato(self, t, active_notes, time_offset, mod_wheel=0):
        vibrato_depth = 5.0  # Hz
        vibrato_rate = 5.0   # Hz
        vibrato = (mod_wheel / 127.0) * vibrato_depth * np.sin(2 * np.pi * vibrato_rate * (t + time_offset[0]))
        return [
            np.sin(2 * np.pi * freq * (t + time_offset[0]) + vibrato)
            for freq in active_notes.values()
        ]

    def square(self, t, active_notes, time_offset, mod_wheel=0):
        return [
            np.sign(np.sin(2 * np.pi * freq * (t + time_offset[0])))
            for freq in active_notes.values()
        ]

    def sawtooth(self, t, active_notes, time_offset, mod_wheel=0):
        return [
            2 * (t * freq - np.floor(0.5 + t * freq))
            for freq in active_notes.values()
        ]


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
        self.audio_gens = AudioGens()
        self.current_gen = "sine"

    def audio_callback(self, *args):
        outdata, frames, *_ = args
        t = np.arange(frames) / self.samplerate
        self.device_menu.mutex.lock()
        if self.device_menu.active_notes:
            waves = self.audio_gens[self.current_gen](t, self.device_menu.active_notes, self.time_offset, self.device_menu.mod_wheel )
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
