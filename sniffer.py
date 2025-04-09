import json
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar
import subprocess

import librosa
import librosa.display
import numpy as np
import soundfile as sf


class AudioAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio zu Noten Konverter")
        self.root.geometry("600x400")
        self.root.configure(bg="#2C2E3B")

        # Styling
        self.text_color = "#FFFFFF"
        self.bg_color = "#2C2E3B"
        self.accent_color = "#FF5D8F"
        self.secondary_bg = "#3D3F4F"

        # Parameter für die Notenerkennung
        self.min_note_length = 0.25  # Minimale Notendauer in Sekunden
        self.min_magnitude = 1.0  # Minimale Lautstärke für eine gültige Note
        self.min_pitch = 36  # Minimale Tonhöhe (C2)
        self.max_pitch = 96  # Maximale Tonhöhe (C7)

        # StringVar-Variablen für die Eingabefelder
        self.note_length_var = tk.StringVar(root)
        self.note_length_var.set(str(self.min_note_length))

        self.magnitude_var = tk.StringVar(root)
        self.magnitude_var.set(str(self.min_magnitude))

        # Erstelle UI
        self.setup_ui()

        # Drag & Drop-Unterstützung
        self.root.drop_target_register("DND_Files")
        self.root.dnd_bind('<<Drop>>', self.drop)

        # Analysevariablen
        self.current_file = None
        self.analysis_thread = None
        self.is_analyzing = False

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg=self.secondary_bg, pady=15)
        header_frame.pack(fill=tk.X)

        title = tk.Label(header_frame, text="Audio zu Noten Konverter",
                         font=("Segoe UI", 18, "bold"), fg=self.text_color, bg=self.secondary_bg)
        title.pack()

        # Hauptbereich
        main_frame = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Einstellungen Frame
        settings_frame = tk.Frame(main_frame, bg=self.bg_color)
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # Minimale Notenlänge
        note_length_label = tk.Label(settings_frame, text="Min. Notenlänge (s):",
                                     fg=self.text_color, bg=self.bg_color)
        note_length_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)

        note_length_entry = tk.Entry(settings_frame, textvariable=self.note_length_var, width=5)
        note_length_entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)

        # Minimale Lautstärke
        magnitude_label = tk.Label(settings_frame, text="Min. Lautstärke:",
                                   fg=self.text_color, bg=self.bg_color)
        magnitude_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)

        magnitude_entry = tk.Entry(settings_frame, textvariable=self.magnitude_var, width=5)
        magnitude_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)

        # Drag & Drop-Bereich
        self.drop_frame = tk.Frame(main_frame, bg=self.secondary_bg, padx=20, pady=30)
        self.drop_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.drop_label = tk.Label(self.drop_frame,
                                   text="Ziehe eine Audio-Datei hierher oder klicke zum Auswählen",
                                   font=("Segoe UI", 12), fg=self.text_color, bg=self.secondary_bg,
                                   wraplength=500)
        self.drop_label.pack(pady=20)

        self.browse_btn = tk.Button(self.drop_frame, text="Datei auswählen",
                                    font=("Segoe UI", 10), bg=self.accent_color, fg=self.text_color,
                                    border=0, padx=15, pady=8, command=self.browse_file)
        self.browse_btn.pack(pady=10)

        # Fortschrittsbereich (zunächst versteckt)
        self.progress_frame = tk.Frame(main_frame, bg=self.bg_color, padx=20, pady=20)

        self.file_label = tk.Label(self.progress_frame, text="",
                                   font=("Segoe UI", 10), fg=self.text_color, bg=self.bg_color)
        self.file_label.pack(anchor=tk.W, pady=(0, 10))

        self.progress_bar = Progressbar(self.progress_frame, orient=tk.HORIZONTAL,
                                        length=500, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=10)

        self.status_label = tk.Label(self.progress_frame, text="",
                                     font=("Segoe UI", 10), fg=self.text_color, bg=self.bg_color)
        self.status_label.pack(anchor=tk.W, pady=5)

        # Footer-Bereich
        footer_frame = tk.Frame(self.root, bg=self.secondary_bg, pady=10)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        footer_text = tk.Label(footer_frame, text="Unterstützte Formate: .wav, .mp3, .ogg, .flac",
                               font=("Segoe UI", 8), fg=self.text_color, bg=self.secondary_bg)
        footer_text.pack()

    def drop(self, event):
        file_path = event.data
        # Bereinige den Dateipfad (je nach Betriebssystem kann dies variieren)
        if file_path.startswith("{"):
            file_path = file_path[1:]
        if file_path.endswith("}"):
            file_path = file_path[:-1]

        # Entferne Anführungszeichen, falls vorhanden
        file_path = file_path.strip('"')

        self.process_file(file_path)

    def browse_file(self):
        file_types = [
            ('Audio-Dateien', '*.wav;*.mp3;*.ogg;*.flac'),
            ('Alle Dateien', '*.*')
        ]

        file_path = filedialog.askopenfilename(filetypes=file_types)
        if file_path:
            self.process_file(file_path)

    def process_file(self, file_path):
        if not os.path.exists(file_path):
            messagebox.showerror("Fehler", f"Datei nicht gefunden: {file_path}")
            return

        # Prüfe, ob es sich um eine Audio-Datei handelt
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.wav', '.mp3', '.ogg', '.flac']:
            messagebox.showerror("Fehler", "Bitte wähle eine unterstützte Audio-Datei aus (.wav, .mp3, .ogg, .flac)")
            return

        # Aktualisiere Parameter aus der GUI
        try:
            self.min_note_length = float(self.note_length_var.get())
            self.min_magnitude = float(self.magnitude_var.get())
        except ValueError:
            messagebox.showerror("Fehler", "Ungültige Eingabe bei den Parametern. Bitte gib gültige Zahlen ein.")
            return

        self.current_file = file_path

        # UI-Update für den Analyseprozess
        self.drop_frame.pack_forget()
        self.progress_frame.pack(fill=tk.BOTH, expand=True)

        self.file_label.config(text=f"Datei: {os.path.basename(file_path)}")
        self.status_label.config(text="Analysiere Audio-Datei...")
        self.progress_bar.start(10)

        # Starte Analyse in separatem Thread
        self.is_analyzing = True
        self.analysis_thread = threading.Thread(target=self.analyze_audio)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()

    def analyze_audio(self):
        try:
            # Audio-Datei laden
            self.update_status("Lade Audio-Datei...")
            y, sr = librosa.load(self.current_file, sr=None)

            # Tonhöhe extrahieren
            self.update_status("Extrahiere Tonhöhen...")
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

            # Dominante Tonhöhen finden
            self.update_status("Identifiziere dominante Noten...")
            notes = self.extract_notes(pitches, magnitudes, sr)

            # Formatiere Ergebnis gemäß Zielformat
            self.update_status("Formatiere Ergebnis...")
            formatted_notes = self.format_notes(notes)

            # Speichere Ergebnis
            output_file = os.path.splitext(self.current_file)[0] + "_notes.json"
            with open(output_file, 'w') as f:
                json.dump(formatted_notes, f, indent=2)

            self.update_status(f"Fertig! Ergebnis gespeichert unter: {output_file}")

            # Frage, ob der Player gestartet werden soll
            def ask_to_start_player():
                if messagebox.askyesno("Erfolg",
                                       f"Noten wurden extrahiert und in {output_file} gespeichert. Möchtest du den Noten-Player starten?"):
                    self.start_player(output_file)
                else:
                    messagebox.showinfo("Erfolg", f"Noten wurden erfolgreich in {output_file} gespeichert.")

            self.root.after(0, ask_to_start_player)

            # Zurück zum Anfangsbildschirm
            self.root.after(1000, self.reset_ui)

        except Exception as e:
            self.update_status(f"Fehler: {str(e)}")
            messagebox.showerror("Fehler bei der Analyse", str(e))
            self.root.after(1000, self.reset_ui)

        self.is_analyzing = False

    def extract_notes(self, pitches, magnitudes, sr):
        # Hier werden die Noten aus den extrahierten Tonhöhen und Lautstärken ermittelt
        notes = []
        current_note = None
        current_start = 0

        # Wandle die Pitches-Matrix in dominante Tonhöhen pro Frame um
        times = librosa.times_like(pitches)

        # Verwende ein Fenster für Notenerkennung, um Rauschen zu reduzieren
        window_size = 3  # Fenster von Frames für stabilere Notenerkennung

        # Initialisiere das Fenster
        pitch_window = []
        mag_window = []

        for t, time in enumerate(times):
            # Finde die dominante Frequenz in diesem Frame
            index = magnitudes[:, t].argmax()
            freq = pitches[index, t]
            mag = magnitudes[index, t]

            # Aktualisiere das Fenster
            pitch_window.append(freq)
            mag_window.append(mag)

            # Behalte nur die letzten window_size Frames
            if len(pitch_window) > window_size:
                pitch_window.pop(0)
                mag_window.pop(0)

            # Warte, bis das Fenster gefüllt ist
            if len(pitch_window) < window_size:
                continue

            # Berechne die mittlere Frequenz und Magnitude im Fenster
            avg_freq = np.median(pitch_window)  # Median ist robuster gegen Ausreißer
            avg_mag = np.median(mag_window)

            # Ignoriere Stille oder Geräusche mit niedriger Magnitude
            if avg_freq <= 0 or avg_mag < self.min_magnitude:
                if current_note is not None:
                    # Wenn wir bereits eine Note verfolgen, füge sie hinzu
                    if time - current_start >= self.min_note_length:
                        midi_note = librosa.hz_to_midi(current_note)
                        # Nur Noten im gewünschten Bereich berücksichtigen
                        if self.min_pitch <= midi_note <= self.max_pitch:
                            notes.append({
                                'time': current_start,
                                'pitch': int(round(midi_note)),
                                'duration': time - current_start
                            })
                    current_note = None
            else:
                # Konvertiere Frequenz in MIDI-Notennummern
                midi_note = librosa.hz_to_midi(avg_freq)

                if current_note is None:
                    # Starte eine neue Note
                    current_note = avg_freq
                    current_start = time
                elif abs(librosa.hz_to_midi(current_note) - midi_note) > 0.5:  # Verringerte Toleranz für Tonwechsel
                    # Wenn sich die Note signifikant geändert hat, beende die vorherige
                    if time - current_start >= self.min_note_length:
                        midi_note_prev = librosa.hz_to_midi(current_note)
                        # Nur Noten im gewünschten Bereich berücksichtigen
                        if self.min_pitch <= midi_note_prev <= self.max_pitch:
                            notes.append({
                                'time': current_start,
                                'pitch': int(round(midi_note_prev)),
                                'duration': time - current_start
                            })
                    current_note = avg_freq
                    current_start = time

        # Füge die letzte Note hinzu, falls vorhanden
        if current_note is not None and times[-1] - current_start >= self.min_note_length:
            midi_note = librosa.hz_to_midi(current_note)
            # Nur Noten im gewünschten Bereich berücksichtigen
            if self.min_pitch <= midi_note <= self.max_pitch:
                notes.append({
                    'time': current_start,
                    'pitch': int(round(midi_note)),
                    'duration': times[-1] - current_start
                })

        return notes

    def format_notes(self, notes):
        # Runde Zeiten und Dauern auf 1 Nachkommastelle
        formatted_notes = []
        for note in notes:
            formatted_notes.append({
                'time': round(note['time'], 1),
                'pitch': note['pitch'],
                'duration': round(note['duration'], 1)
            })

        # Sortiere nach Startzeit
        formatted_notes.sort(key=lambda x: x['time'])

        # Entferne Duplikate (Noten mit gleicher Startzeit und Tonhöhe)
        unique_notes = []
        for note in formatted_notes:
            if not any(n['time'] == note['time'] and n['pitch'] == note['pitch'] for n in unique_notes):
                unique_notes.append(note)

        return {'notes': unique_notes}

    def update_status(self, text):
        self.root.after(0, lambda: self.status_label.config(text=text))

    def reset_ui(self):
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        self.drop_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def start_player(self, notes_file):
        """Startet den Noten-Player mit der erstellten JSON-Datei"""
        try:
            # Prüfe, ob spitter_gui.py existiert
            if os.path.exists("spitter_gui.py"):
                subprocess.Popen([sys.executable, "spitter_gui.py", notes_file])
            # Alternativ prüfe auf spitter.py
            elif os.path.exists("spitter.py"):
                subprocess.Popen([sys.executable, "spitter.py", notes_file])
            else:
                messagebox.showinfo("Information",
                                    f"Noten-Player nicht gefunden. Die Notendatei wurde unter '{notes_file}' gespeichert.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Starten des Players: {str(e)}")


def enable_dnd(root):
    """Aktiviert Drag & Drop für Tkinter (plattformunabhängig)"""
    if sys.platform == 'win32':
        # Windows-Implementierung
        from tkinterdnd2 import TkinterDnD
        if not isinstance(root, TkinterDnD.Tk):
            raise TypeError("root must be an instance of TkinterDnD.Tk")
    else:
        # Linux/MacOS-Implementierung
        root.tk.eval('package require tkdnd')
        root.tk.call('tkdnd::drop_target', 'register', root._w, 'DND_Files')


def main():
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except ImportError:
        # Falls tkinterdnd2 nicht verfügbar ist
        print("Hinweis: tkinterdnd2 ist nicht installiert. Drag & Drop könnte eingeschränkt sein.")
        print("Installiere es mit: pip install tkinterdnd2")
        root = tk.Tk()
        try:
            enable_dnd(root)
        except:
            print("Drag & Drop nicht verfügbar. Nutze bitte den Dateiauswahldialog.")

    app = AudioAnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()