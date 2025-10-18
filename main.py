#!/bin/env python3
from PySide6 import QtWidgets, QtCore, QtGui 
import widgets

class SimpleApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple PySide6 App")
        self.resize(400, 300)
         

        label = QtWidgets.QLabel("Hello, PySide6!", parent=self)
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(label)

        menu_bar = QtWidgets.QMenuBar(self)
        layout.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("File")
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        device_menu = widgets.ChooseDev("Devices", self)
        dev_menu = menu_bar.addMenu(device_menu)



if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    available_fonts = QtGui.QFontDatabase.families()
    print("Available Fonts:", available_fonts)
    app.setFont(QtGui.QFont("Arial", 14))
    window = SimpleApp()
    window.show()
    app.exec()
