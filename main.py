#!/bin/env python3
import sys
from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Signal
from AsyncioPySide6 import AsyncioPySide6
import pyqtgraph as pg
import numpy as np
import widgets
import threading
import asyncio

class SimpleApp(QtWidgets.QWidget):
    samplerate = 48000
    status_signal = Signal(str)
    base_message = "Background Thread {} | Device: {} | Sample Rate: {} Hz | Wave Multiplier: {} | Audio Generator: {}"
    pixmap = QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton

    def __init__(self):
        super().__init__()
        self.status_signal.connect(self.update_staus_bar)
        self.setWindowTitle("MIDI Audio Visualizer")
        self.resize(1280, 720)

        self.plot_graph = pg.PlotWidget()
        self.plot_graph.setYRange(-10, 10)
        self.plot_graph.setLabel("left", "Amplitude")
        self.plot_graph.setLabel("bottom", "Time", units="s")
        self.plot_graph.setMouseEnabled(x=False, y=False)
        self.plot_graph.hideButtons()
        self.plot_graph.getPlotItem().setMenuEnabled(False)  # pyright: ignore

        self.fft_graph = pg.PlotWidget()
        self.fft_graph.setYRange(0, 1)
        self.fft_graph.setLabel("left", "Magnitude")
        self.fft_graph.setLabel("bottom", "Frequency", units="Hz")
        self.fft_graph.setMouseEnabled(x=False, y=False)
        self.fft_graph.hideButtons()
        self.fft_graph.getPlotItem().setMenuEnabled(False) # pyright: ignore

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.plot_graph)
        layout.addWidget(self.fft_graph)

        menu_bar = QtWidgets.QMenuBar(self)
        layout.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("File")

        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        self.device_menu = widgets.ChooseDev(
            "Devices", self, lambda _: self.start_background_job()
        )
        menu_bar.addMenu(self.device_menu)

        self.audioGen = widgets.AudioGen(
            self.device_menu, samplerate=self.samplerate
        )

        self.audioGen.communicator.update_plot.connect(
            lambda t: self.plot_graph.plot(*t, clear=True)
        )

        self.audioGen.communicator.update_plot.connect(
            lambda t: self.fft_graph.plot(
                np.fft.rfftfreq(
                    len(t[1]), d=1.0 / self.audioGen.samplerate
                ),
                np.abs(np.fft.rfft(t[1])) / len(t[1]),
                clear=True,
            )
        )

        effects = self.audioGen.audio_gens._get_available_gens()
        effect_menu = menu_bar.addMenu("Audio Generator")
        for effect in effects:
            effect_action = effect_menu.addAction(effect.replace("_", " ").title())
            effect_action.triggered.connect(self.audio_effect_changed)
            effect_action.setData(effect)
            if effect == self.audioGen.current_gen:
                effect_action.setIcon(self.style().standardIcon(self.pixmap))
                self.effect_btn = effect_action


        stop_action = file_menu.addAction("Stop MIDI Input")
        stop_action.triggered.connect(self.stop_midi_input)

        start_action = file_menu.addAction("Start MIDI Input")
        start_action.triggered.connect(self.start_background_job)

        # status bar
        self.status_bar = QtWidgets.QStatusBar(self)
        layout.addWidget(self.status_bar)
        self.status_signal.emit("Background Thread Not Running")

        # sample rate input field
        settings_menu = menu_bar.addMenu("Settings")

        wave_multiplier = settings_menu.addMenu("Wave Amplitude")
        for mult in [0.1, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0, 7.0, 10.0]:
            mult_action = wave_multiplier.addAction(str(mult))
            mult_action.triggered.connect(self.wave_multiplier_changed)
            mult_action.setData(mult)
            if mult == self.audioGen.wave_multiplier:
                mult_action.setIcon(self.style().standardIcon(self.pixmap))
                self.mult_btn = mult_action

        sr_menu = settings_menu.addMenu("Sample Rate")
        for rate in [8000, 11025, 22050, 44100, 48000, 96000]:
            sr_action = sr_menu.addAction(str(rate))
            sr_action.triggered.connect(self.update_sample_rate)
            if rate == self.samplerate:
                sr_action.setIcon(self.style().standardIcon(self.pixmap))
                self.sr_btn = sr_action

        self.bg_thread = threading.Thread(target=self.device_menu.backgroundJob, daemon=False)

    def update_staus_bar(self, message: str):
        async def update_staus_bar(self, message: str):
            self.status_bar.showMessage(message)
            await asyncio.sleep(2.5)
            self.status_bar.showMessage(
                self.base_message.format(
                    self.device_menu.alive and "Running" or "Not Running",
                    self.device_menu.port_id,
                    self.samplerate,
                    self.audioGen.wave_multiplier,
                    self.audioGen.current_gen,
                )
            )
        AsyncioPySide6.runTask(update_staus_bar(self, message))

    def closeEvent(self, event):
        self.device_menu.alive = False
        self.device_menu.stop_midi_input()
        if self.bg_thread.is_alive():
            self.bg_thread.join()
        self.audioGen.stop()
        event.accept()

    def wave_multiplier_changed(self):
        multiplier = float(self.sender().text())  # type: ignore
        self.audioGen.wave_multiplier = multiplier
        self.sender().setIcon(self.style().standardIcon(self.pixmap))  # type: ignore
        self.mult_btn.setIcon(QtGui.QIcon())  # type: ignore
        self.status_signal.emit(f"Wave Amplitude Multiplier set to {multiplier}")
        self.mult_btn = self.sender()

    def update_sample_rate(self):
        new_rate = int(self.sender().text())  # type: ignore
        pixmapi = QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton
        self.sender().setIcon(self.style().standardIcon(pixmapi))  # type: ignore
        self.sr_btn.setIcon(QtGui.QIcon()) # type: ignore
        self.samplerate = new_rate
        ag_playing = self.audioGen.is_playing
        if ag_playing:
            self.audioGen.stop()
            self.device_menu.stop_midi_input()
        self.audioGen.samplerate = new_rate
        self.audioGen.time_offset = [0.0]
        self.status_signal.emit(f"Sample Rate set to {new_rate} Hz")
        if ag_playing:
            self.audioGen.start()
            self.start_background_job()
        self.sr_btn = self.sender()

    def audio_effect_changed(self):
        effect = self.sender().data()  # type: ignore
        self.audioGen.current_gen = effect
        self.status_signal.emit(f"Audio Generator changed to {effect}")
        self.sender().setIcon(self.style().standardIcon(self.pixmap))  # type: ignore
        self.effect_btn.setIcon(QtGui.QIcon())  # type: ignore
        self.effect_btn = self.sender()


    def start_background_job(self):
        if self.device_menu.port_id is None:
            self.status_signal.emit("No MIDI Device Selected")
            return
        self.audioGen.start()
        if not self.bg_thread.is_alive():
            self.bg_thread = threading.Thread(target=self.device_menu.backgroundJob, daemon=False)
            self.bg_thread.start()

    def stop_midi_input(self):
        if self.device_menu.port_id is None:
            self.status_signal.emit("No MIDI Device Selected")
            return
        self.device_menu.stop_midi_input()
        self.audioGen.stop()
        self.status_signal.emit("MIDI Input Stopped")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    with AsyncioPySide6.use_asyncio():
        app.setFont(QtGui.QFont("Arial", 14))
        window = SimpleApp()
        window.show()
        sys.exit(app.exec())

# vim: set ts=4 sw=4 sts=4 et ai:
