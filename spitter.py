import json
import sys
import time

import numpy as np
import pygame
from pygame.mixer import Sound, get_init, pre_init


class NotePlayer:
    def __init__(self, json_file):
        # MIDI zu Frequenz Umrechnung
        self.midi_to_freq = lambda midi_note: 440 * 2 ** ((midi_note - 69) / 12)

        # Pygame initialisieren
        pre_init(44100, -16, 1, 1024)
        pygame.init()
        pygame.mixer.init()

        # UI-Farben
        self.background_color = (44, 46, 59)  # #2C2E3B
        self.text_color = (255, 255, 255)
        self.accent_color = (75, 140, 205)

        # JSON Datei laden
        with open(json_file, 'r') as f:
            self.data = json.load(f)

        # Noten sortieren nach Startzeit
        self.notes = sorted(self.data['notes'], key=lambda x: x['time'])

        # Display einrichten
        self.width, self.height = 800, 400
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Note Player")
        self.font = pygame.font.SysFont('Arial', 20)
        self.small_font = pygame.font.SysFont('Arial', 16)

        # Berechnung der max. Zeit für die Fortschrittsanzeige
        self.total_time = max(note['time'] + note['duration'] for note in self.notes)

    def generate_sine_wave(self, frequency, duration, volume=0.5):
        """Generiert einen Sinuston mit gegebener Frequenz und Dauer"""
        sample_rate = pygame.mixer.get_init()[0]
        samples = int(duration * sample_rate)

        # Erzeugen der Wellenform mit Fade-in/out
        buf = np.zeros((samples, 1), dtype=np.float32)
        t = np.linspace(0, duration, samples, False)

        # Sinuswelle erzeugen
        buf[:, 0] = np.sin(2 * np.pi * frequency * t)

        # Fade-in und Fade-out anwenden (10% der Gesamtlänge)
        fade_len = int(samples * 0.1)
        fade_in = np.linspace(0, 1, fade_len)
        fade_out = np.linspace(1, 0, fade_len)

        buf[:fade_len, 0] *= fade_in
        buf[-fade_len:, 0] *= fade_out

        # Lautstärke anpassen
        buf *= volume

        return Sound(buf)

    def play(self):
        # Startzeit merken
        start_time = time.time()
        current_note_index = 0
        running = True

        # Hauptloop
        while running and current_note_index < len(self.notes):
            # Events verarbeiten
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False

            # Aktuelle Zeit im Stück berechnen
            elapsed = time.time() - start_time

            # Alle Noten spielen, die jetzt starten sollen
            while (current_note_index < len(self.notes) and
                   self.notes[current_note_index]['time'] <= elapsed):
                note = self.notes[current_note_index]

                # Frequenz aus MIDI-Note berechnen
                freq = self.midi_to_freq(note['pitch'])

                # Ton erzeugen und abspielen
                sound = self.generate_sine_wave(freq, note['duration'])
                sound.play()

                # Info ausgeben
                print(f"Spiele Note: MIDI {note['pitch']}, Frequenz {freq:.2f}Hz, Dauer {note['duration']}s")

                # Zum nächsten Index
                current_note_index += 1

            # UI zeichnen
            self.draw_ui(elapsed, current_note_index)

            # Kurz warten, um CPU zu schonen
            time.sleep(0.01)

        # Warten, bis die letzte Note fertig ist
        if current_note_index > 0 and running:
            last_note = self.notes[current_note_index - 1]
            remaining_time = (last_note['time'] + last_note['duration']) - elapsed
            if remaining_time > 0:
                time.sleep(remaining_time)

        pygame.quit()

    def draw_ui(self, current_time, current_note_index):
        # Hintergrund
        self.screen.fill(self.background_color)

        # Fortschrittsbalken
        progress_width = int((current_time / self.total_time) * self.width)
        pygame.draw.rect(self.screen, self.accent_color, (0, 30, progress_width, 10))

        # Aktuelle Zeit / Gesamtzeit
        time_text = self.font.render(f"Zeit: {current_time:.1f}s / {self.total_time:.1f}s", True, self.text_color)
        self.screen.blit(time_text, (20, 50))

        # Aktuelle Note / Gesamtzahl der Noten
        note_count_text = self.font.render(f"Note: {current_note_index}/{len(self.notes)}", True, self.text_color)
        self.screen.blit(note_count_text, (20, 80))

        # Anzeige der letzten 5 gespielten Noten
        if current_note_index > 0:
            start_idx = max(0, current_note_index - 5)
            recent_notes = self.notes[start_idx:current_note_index]

            self.screen.blit(self.font.render("Zuletzt gespielte Noten:", True, self.text_color), (20, 120))

            for i, note in enumerate(reversed(recent_notes)):
                freq = self.midi_to_freq(note['pitch'])
                note_text = self.small_font.render(
                    f"MIDI: {note['pitch']}, Freq: {freq:.2f}Hz, Dauer: {note['duration']}s",
                    True, self.text_color
                )
                self.screen.blit(note_text, (40, 150 + i * 25))

        # Piano Roll Visualisierung im unteren Bereich
        piano_roll_height = 150
        piano_roll_top = self.height - piano_roll_height

        # Horizontale Linien für einige MIDI-Noten
        for midi_note in range(50, 105, 5):
            y_pos = piano_roll_top + piano_roll_height - int((midi_note - 50) / 55 * piano_roll_height)
            line_color = (100, 100, 120)
            pygame.draw.line(self.screen, line_color, (0, y_pos), (self.width, y_pos), 1)
            note_label = self.small_font.render(str(midi_note), True, (180, 180, 200))
            self.screen.blit(note_label, (5, y_pos - 8))

        # Noten zeichnen
        visible_duration = 5.0  # 5 Sekunden sichtbar
        start_time = max(0, current_time - visible_duration / 2)
        end_time = start_time + visible_duration

        for note in self.notes:
            # Nur Noten im sichtbaren Bereich zeichnen
            if note['time'] + note['duration'] < start_time or note['time'] > end_time:
                continue

            # Position berechnen
            x_start = int((note['time'] - start_time) / visible_duration * self.width)
            x_width = int(note['duration'] / visible_duration * self.width)
            y_pos = piano_roll_top + piano_roll_height - int((note['pitch'] - 50) / 55 * piano_roll_height)

            # Farbe basierend auf der Tonhöhe
            hue = (note['pitch'] % 12) / 12
            # HSV zu RGB konvertieren für interessantere Farben
            import colorsys
            r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
            note_color = (int(r * 255), int(g * 255), int(b * 255))

            # Note zeichnen
            pygame.draw.rect(self.screen, note_color, (x_start, y_pos - 5, max(x_width, 3), 10))

        # Aktuelle Zeitposition anzeigen
        time_marker_x = int(visible_duration / 2 / visible_duration * self.width)
        pygame.draw.line(self.screen, (255, 0, 0), (time_marker_x, piano_roll_top),
                         (time_marker_x, self.height), 2)

        pygame.display.flip()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        json_file = "paste.txt"  # Standard-Dateiname

    try:
        player = NotePlayer(json_file)
        player.play()
    except Exception as e:
        print(f"Fehler: {e}")
        pygame.quit()
