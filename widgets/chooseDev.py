from typing import Callable
from pygame import midi
from PySide6 import QtWidgets, QtGui, QtCore
from time import sleep


class ChooseDev(QtWidgets.QMenu):
    def __init__(
        self,
        title: str,
        parent: QtWidgets.QWidget,
        selection_callback: Callable,
        backend: str = "mido.backends.pygame",
    ):
        super().__init__(title, parent)
        self.port_id = None
        self.backend = backend
        self.ports: dict[int, QtGui.QAction] = {}
        self.active_notes = {}
        self.selection_callback = selection_callback
        self.alive = True
        self.mutex = QtCore.QMutex()

        self.refresh_action = self.addAction("Refresh Device List")
        self.refresh_action.triggered.connect(self.refresh_device_list)
        self.refresh_device_list()

    def refresh_device_list(self):
        print("Refreshing MIDI device list...")
        for _, action in self.ports.items():
            self.removeAction(action)
        self.ports.clear()
        self.separator = self.addSeparator()
        devs = self.list_input_ports()
        if not devs:
            no_dev_action = self.addAction("No MIDI Input Devices Found")
            no_dev_action.setEnabled(False)
            self.ports[-1] =  no_dev_action
            return

        for i, dev in devs:
            print(f"Adding device: {dev}")
            action = self.addAction(dev)
            action.setData(i)
            action.triggered.connect(self.handle_device_selection)
            self.ports[i] = action

    def list_input_ports(self):
        midi.init()
        input_ports = []
        for i in range(midi.get_count()):
            info = midi.get_device_info(i)
            if not info:
                continue
            if info[2] == 1:  # input device
                input_ports.append((i,info[1].decode()))
        midi.quit()
        return input_ports

    def handle_device_selection(self):
        action = self.sender()
        index = action.data()  # type: ignore
        self.port_id = selected_port = index
        print(f"Selected MIDI Input Port: {selected_port}")
        pixmapi = QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton
        for i in self.ports:
            if i == index:
                self.ports[i].setIcon(self.style().standardIcon(pixmapi))
            else:
                pixmapi = QtWidgets.QStyle.StandardPixmap.SP_DialogNoButton
        self.selection_callback(selected_port)

    def stop_midi_input(self):
        print("Stopping MIDI input handling.")
        self.alive = False

    def backgroundJob(self):
        if self.port_id is None:
            print("No MIDI port selected.")
            return

        print(f"Listening on MIDI port: {self.port_id}")
        try:
            midi.init()
            inport = midi.Input(self.port_id)
            while self.alive:
                if inport.poll():
                    midi_events = inport.read(10)
                    self.mutex.lock()
                    for event in midi_events:
                        msg, _ = event
                        if msg[0] == 144 and msg[2] > 0:  # note_on
                            note = msg[1]
                            freq = 440.0 * (2 ** ((note - 69) / 12))
                            self.active_notes[note] = freq
                            print(f"Note ON {note} -> {freq:.2f} Hz")
                        elif msg[0] in (128, 144) and msg[2] == 0:  # note_off
                            note = msg[1]
                            if note in self.active_notes:
                                print(f"Note OFF {note}")
                                del self.active_notes[note]
                    self.mutex.unlock()
                sleep(0.01)  # Small delay to prevent CPU overload
            inport.close()
            midi.quit()
            print("MIDI input handling thread terminating.")
        except Exception as e:
            print(f"Error in MIDI input handling: {e}")
            raise
        # try:
        #     with mido.open_input(self.port_id) as inport:  # pyright: ignore
        #         for msg in inport:
        #             if not self.alive:
        #                 print("MIDI input handling thread terminating.")
        #                 break

        #             self.mutex.lock()
        #             if msg.type == "note_on" and msg.velocity > 0:
        #                 freq = 440.0 * (2 ** ((msg.note - 69) / 12))
        #                 self.active_notes[msg.note] = freq
        #                 print(f"Note ON {msg.note} -> {freq:.2f} Hz")

        #             elif msg.type in ("note_off", "note_on") and msg.velocity == 0:
        #                 if msg.note in self.active_notes:
        #                     print(f"Note OFF {msg.note}")
        #                     del self.active_notes[msg.note]
        #             self.mutex.unlock()

        # except Exception as e:
        #     print(f"Error in MIDI input handling: {e}")
        #     raise


# vim: set ts=4 sw=4 sts=4 et ai:
