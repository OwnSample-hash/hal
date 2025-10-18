import mido
from PySide6 import QtWidgets

class ChooseDev(QtWidgets.QMenu):
    def __init__(self, title:str, parent, backend="mido.backends.pygame"):
        super().__init__(title, parent)
        self.port_name = None
        self.backend = backend

        mido.set_backend(self.backend)

        self.refresh_action = self.addAction("Refresh Device List")
        self.separator = self.addSeparator()
        devs = self.list_input_ports()
        for i, dev in enumerate(devs):
            print(f"Adding device: {dev}")
            action = self.addAction(dev)
            action.setData(i)
            action.triggered.connect(self.handle_device_selection)

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
        index = action.data()
        selected_port = self.choose_port(index)
        print(f"Selected MIDI Input Port: {selected_port}")
