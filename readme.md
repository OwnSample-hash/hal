# Audio Midi Vizualiáció

## Használt csomagok:

| Csomag      | Használat                                                      |
| ----------- | -------------------------------------------------------------- |
| pyside6     | Grafikus megjelenítés                                          |
| pyqtgraph   | Grafikon plotolás ui-on                                        |
| pygame      | midi device interface                                          |
| numpy       | Hang adat kiszámtása tárlása                                   |
| sounddevice | Hang adat lejátszása                                           |
| widgtes     | Saját csomag, audio generálás és a midi eszköz kezelés szolgás |

## Osztályok

### `main.py`

#### `SimpleApp(QtWidgets.QWidget)`

A fő osztály ami a qt6 os ui-t írja le. Tartalmaz egy `menubar`, `statusbar`, és kettő grafikont. Egyet a fft-nek a másikat pedig időszerint.

### `widgets/audioGen.py`

#### `AudioGens`

Otthont add a audio generátoroknak. Ha példányosítjuk az osztályt akkor el lehet érni a különbzö generátorokat a `["sine"]` modón. A `__getitem__` metódus segítségével érji el.

#### `SignalCommunicator(QObject)`

Jel kummonikátor osztály ami tartalmazza a `update_plot` Jelet ami egy tupelt vár. A fő ui feliratkozik erre és az `AudioGen` osztály meg `emit`-el kibocsálytja az új hang jelet.

#### `AudioGen(QObject)`

Össze fűzi a `SignalCommunicator`-t meg a `AudioGen`-t és hangot állít elő.

### `widgets/chooseDev.py`

#### `ChooseDev(QtWidgets.QMenu)`

Egy egész menu elemet definiál. Lehet midi eszközt választani és ki olvassa a midi üzeneteket.
