import json
import numpy as np
import simpleaudio as sa
import time
import sys


class SimpleNotePlayer:
    def __init__(self, json_file):
        # MIDI zu Frequenz Umrechnung
        self.midi_to_freq = lambda midi_note: 440 * 2 ** ((midi_note - 69) / 12)

        # Sample-Rate
        self.sample_rate = 44100

        # JSON Datei laden
        with open(json_file, 'r') as f:
            self.data = json.load(f)

        # Noten sortieren nach Startzeit
        self.notes = sorted(self.data['notes'], key=lambda x: x['time'])

    def generate_sine_wave(self, frequency, duration, volume=0.5):
        """Generiert einen Sinuston mit gegebener Frequenz und Dauer"""
        samples = int(duration * self.sample_rate)

        # Erzeugen der Wellenform mit Fade-in/out
        t = np.linspace(0, duration, samples, False)

        # Sinuswelle erzeugen
        audio = np.sin(2 * np.pi * frequency * t)

        # Fade-in und Fade-out anwenden (10% der Gesamtlänge)
        fade_len = int(samples * 0.1)
        fade_in = np.linspace(0, 1, fade_len)
        fade_out = np.linspace(1, 0, fade_len)

        audio[:fade_len] *= fade_in
        audio[-fade_len:] *= fade_out

        # Lautstärke anpassen und in 16-bit int konvertieren
        audio = audio * volume * 32767
        return audio.astype(np.int16)

    def play(self):
        # Startzeit merken
        print("Starte Wiedergabe...")
        start_time = time.time()
        current_note_index = 0
        active_playbacks = []

        # Hauptloop
        try:
            while current_note_index < len(self.notes):
                # Aktuelle Zeit im Stück berechnen
                elapsed = time.time() - start_time

                # Alle Noten spielen, die jetzt starten sollen
                while (current_note_index < len(self.notes) and
                       self.notes[current_note_index]['time'] <= elapsed):
                    note = self.notes[current_note_index]

                    # Frequenz aus MIDI-Note berechnen
                    freq = self.midi_to_freq(note['pitch'])

                    # Ton erzeugen und abspielen
                    audio_data = self.generate_sine_wave(freq, note['duration'])
                    play_obj = sa.play_buffer(audio_data, 1, 2, self.sample_rate)
                    active_playbacks.append(play_obj)

                    # Info ausgeben
                    print(
                        f"Zeit: {elapsed:.2f}s - Spiele Note: MIDI {note['pitch']}, Frequenz {freq:.2f}Hz, Dauer {note['duration']}s")

                    # Zum nächsten Index
                    current_note_index += 1

                # Alte Wiedergaben entfernen
                active_playbacks = [p for p in active_playbacks if p.is_playing()]

                # Kurz warten, um CPU zu schonen
                time.sleep(0.01)

            # Warten, bis alle Noten fertig sind
            print("Alle Noten gestartet. Warte auf Ende der Wiedergabe...")
            while any(p.is_playing() for p in active_playbacks):
                active_playbacks = [p for p in active_playbacks if p.is_playing()]
                time.sleep(0.1)

            print("Wiedergabe beendet.")

        except KeyboardInterrupt:
            print("\nWiedergabe abgebrochen.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        json_file = "paste.txt"  # Standard-Dateiname

    try:
        player = SimpleNotePlayer(json_file)
        player.play()
    except Exception as e:
        print(f"Fehler: {e}")