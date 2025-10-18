from typing import Callable
import mido
from PySide6 import QtWidgets, QtGui, QtCore

class ChooseDev(QtWidgets.QMenu):
    def __init__(self, title:str, parent: QtWidgets.QWidget, selection_callback: Callable, backend:str="mido.backends.pygame"):
        super().__init__(title, parent)
        self.port_name = None
        self.backend = backend
        self.ports: list[tuple[str, QtGui.QAction]] = []
        self.active_notes = {}
        self.selection_callback = selection_callback
        self.alive = True
        self.mutex = QtCore.QMutex()

        mido.set_backend(self.backend)

        self.refresh_action = self.addAction("Refresh Device List")
        self.separator = self.addSeparator()
        devs = self.list_input_ports()
        if not devs:
            no_dev_action = self.addAction("No MIDI Input Devices Found")
            no_dev_action.setEnabled(False)
            return 

        for i, dev in enumerate(devs):
            print(f"Adding device: {dev}")
            action = self.addAction(dev)
            action.setData(i)
            action.triggered.connect(self.handle_device_selection)
            self.ports.append((dev, action))

    def list_input_ports(self):
        return mido.get_input_names() # pyright: ignore

    def choose_port(self, index):
        ports = self.list_input_ports()
        if 0 <= index < len(ports):
            self.port_name = ports[index]
            return self.port_name
        else:
            raise IndexError("Invalid port index")

    def handle_device_selection(self):
        action = self.sender()
        index = action.data() # type: ignore
        selected_port = self.choose_port(index)
        print(f"Selected MIDI Input Port: {selected_port}")
        pixmapi = QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton
        self.ports[index][1].setIcon(self.style().standardIcon(pixmapi))
        self.selection_callback(selected_port)

    def stop_midi_input(self):
        print("Stopping MIDI input handling.")
        self.alive = False

    def backgroundJob(self):
        if self.port_name is None:
            print("No MIDI port selected.")
            return

        print(f"Listening on MIDI port: {self.port_name}")
        try:
            with mido.open_input(self.port_name) as inport: # pyright: ignore
                for msg in inport:
                    if not self.alive:
                        print("MIDI input handling thread terminating.")
                        break

                    self.mutex.lock()
                    if msg.type == "note_on" and msg.velocity > 0:
                        freq = 440.0 * (2 ** ((msg.note - 69) / 12))
                        self.active_notes[msg.note] = freq
                        print(f"Note ON {msg.note} -> {freq:.2f} Hz")

                    elif msg.type in ("note_off", "note_on") and msg.velocity == 0:
                        if msg.note in self.active_notes:
                            print(f"Note OFF {msg.note}")
                            del self.active_notes[msg.note]
                    self.mutex.unlock()

        except Exception as e:
            print(f"Error in MIDI input handling: {e}")

# vim: set ts=4 sw=4 sts=4 et ai: 
