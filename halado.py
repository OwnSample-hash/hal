import mido
mido.set_backend('mido.backends.pygame')
import numpy as np
import sounddevice as sd
import threading
import time
import urwid

loop = urwid.MainLoop(urwid.SolidFill(), handle_mouse=False)

# MIDI note -> frekvencia (Hz)
def midi_to_freq(note):
    return 440.0 * (2 ** ((note - 69) / 12))

# Aktív hangok (note -> frekvencia)
active_notes = {}

# Hanggenerátor callback – folyamatosan fut
def audio_callback(outdata, frames, time_info, status):
    t = np.arange(frames) / samplerate
    if active_notes:
        waves = [0.3 * np.sin(2 * np.pi * freq * (t + time_offset[0])) for freq in active_notes.values()]
        wave = np.sum(waves, axis=0) / len(waves)
    else:
        wave = np.zeros(frames)
    outdata[:] = wave.reshape(-1, 1)
    time_offset[0] += frames / samplerate

samplerate = 44100
time_offset = [0.0]

# Hangstream indítása
stream = sd.OutputStream(channels=1, callback=audio_callback, samplerate=samplerate)
stream.start()

print("Elérhető MIDI portok:")
for i, name in enumerate(mido.get_input_names()):
    print(f"{i}: {name}")

port_name = mido.get_input_names()[0]
print(f"\nCsatlakozva: {port_name}")
print("🎹 Több hang egyszerre játszható (Ctrl+C kilépés)")

try:
    with mido.open_input(port_name) as inport:
        for msg in inport:
            if msg.type == "note_on" and msg.velocity > 0:
                freq = midi_to_freq(msg.note)
                active_notes[msg.note] = freq
                print(f"▶️ Note ON {msg.note} -> {freq:.2f} Hz")

            elif msg.type in ("note_off", "note_on") and msg.velocity == 0:
                if msg.note in active_notes:
                    print(f"⏹ Note OFF {msg.note}")
                    del active_notes[msg.note]

except KeyboardInterrupt:
    print("\nLeállítva.")
finally:
    stream.stop()
    stream.close()
