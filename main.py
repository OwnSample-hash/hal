#!/bin/env python3
import sys
from PySide6 import QtWidgets, QtGui
import pyqtgraph as pg
import widgets
import threading


class SimpleApp(QtWidgets.QWidget):
    samplerate = 44100

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIDI Audio Visualizer")
        self.resize(800, 600)

        self.plot_graph = pg.PlotWidget()
        self.plot_graph.setYRange(-10, 10)
        self.plot_graph.setLabel("left", "Amplitude", units="dB")
        self.plot_graph.setLabel("bottom", "Time", units="s")
        self.plot_graph.setMouseEnabled(x=False, y=False)
        self.plot_graph.hideButtons()
        self.plot_graph.getPlotItem().setMenuEnabled(False)  # pyright: ignore

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.plot_graph)

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
            self.plot_graph, self.device_menu, samplerate=self.samplerate
        )

        self.audioGen.communicator.update_plot.connect(
            lambda t: self.plot_graph.plot(*t, clear=True)
        )

        stop_action = file_menu.addAction("Stop MIDI Input")
        stop_action.triggered.connect(self.stop_midi_input)

        # status bar
        self.status_bar = QtWidgets.QStatusBar(self)
        layout.addWidget(self.status_bar)
        self.status_bar.showMessage("Background Thread Not Running")

        # sample rate input field
        self.pixmapi = QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton
        settings_menu = menu_bar.addMenu("Settings")

        wave_multiplier = settings_menu.addMenu("Wave Amplitude")
        for mult in [0.1, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0, 7.0, 10.0]:
            mult_action = wave_multiplier.addAction(str(mult))
            mult_action.triggered.connect(self.wave_multiplier_changed)
            mult_action.setData(mult)
            if mult == self.audioGen.wave_multiplier:
                mult_action.setIcon(self.style().standardIcon(self.pixmapi))
                self.mult_btn = mult_action

        sr_menu = settings_menu.addMenu("Sample Rate")
        for rate in [22050, 44100, 48000, 96000]:
            sr_action = sr_menu.addAction(str(rate))
            sr_action.triggered.connect(self.update_sample_rate)
            if rate == self.samplerate:
                sr_action.setIcon(self.style().standardIcon(self.pixmapi))

        self.bg_job = threading.Thread(
            target=self.device_menu.backgroundJob, daemon=False
        )

        if self.device_menu.port_id:
            self.bg_job.start()
            self.status_bar.showMessage(
                f"Background Thread Running | Device: {self.device_menu.port_id} | Sample Rate: {self.samplerate} Hz | Wave Multiplier: {self.audioGen.wave_multiplier}"
            )
            self.audioGen.start()

    def wave_multiplier_changed(self):
        multiplier = float(self.sender().text())  # type: ignore
        self.audioGen.wave_multiplier = multiplier
        self.sender().setIcon(self.style().standardIcon(self.pixmapi))  # type: ignore
        self.mult_btn.setIcon(QtGui.QIcon())
        self.status_bar.showMessage(
            f"Background Thread Running | Device: {self.device_menu.port_id} | Sample Rate: {self.samplerate} Hz | Wave Multiplier: {self.audioGen.wave_multiplier}"
        )

    def closeEvent(self, event):
        self.device_menu.alive = False
        if self.bg_job.is_alive():
            self.bg_job.join(0.1)
        self.audioGen.stop()
        event.accept()

    def update_sample_rate(self):
        new_rate = int(self.sender().text())  # type: ignore
        pixmapi = QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton
        self.sender().setIcon(self.style().standardIcon(pixmapi))  # type: ignore
        self.samplerate = new_rate
        self.audioGen.stop()
        self.audioGen.samplerate = new_rate
        self.audioGen.time_offset = [0.0]
        self.status_bar.showMessage(f"Sample Rate set to {new_rate} Hz")

    def start_background_job(self):
        if not self.bg_job.is_alive():
            self.bg_job = threading.Thread(
                target=self.device_menu.backgroundJob, daemon=False
            )
            self.bg_job.start()
            self.audioGen.start()
            self.status_bar.showMessage(
                f"Background Thread Running | Device: {self.device_menu.port_id} | Sample Rate: {self.samplerate} Hz | Wave Multiplier: {self.audioGen.wave_multiplier}"
            )

    def stop_midi_input(self):
        self.device_menu.stop_midi_input()
        self.audioGen.stop()
        self.status_bar.showMessage("MIDI Input Stopped")


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setFont(QtGui.QFont("Arial", 14))
    window = SimpleApp()
    window.show()
    sys.exit(app.exec())

# vim: set ts=4 sw=4 sts=4 et ai:
