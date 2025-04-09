import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import subprocess


class NotePlayerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Noten-Player")
        self.root.geometry("600x400")
        self.root.configure(bg="#2C2E3B")

        # Styling
        self.text_color = "#FFFFFF"
        self.bg_color = "#2C2E3B"
        self.accent_color = "#FF5D8F"
        self.secondary_bg = "#3D3F4F"

        # Erstelle UI
        self.setup_ui()

        # Drag & Drop-Unterstützung
        self.root.drop_target_register("DND_Files")
        self.root.dnd_bind('<<Drop>>', self.drop)

        # Player-Variablen
        self.current_file = None
        self.player_thread = None
        self.is_playing = False
        self.player_mode = "spitter"  # Default: visueller Player

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg=self.secondary_bg, pady=15)
        header_frame.pack(fill=tk.X)

        title = tk.Label(header_frame, text="Noten-Player",
                         font=("Segoe UI", 18, "bold"), fg=self.text_color, bg=self.secondary_bg)
        title.pack()

        # Hauptbereich
        main_frame = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Modus-Auswahl
        mode_frame = tk.Frame(main_frame, bg=self.bg_color)
        mode_frame.pack(pady=(0, 10))

        mode_label = tk.Label(mode_frame, text="Player-Modus:",
                              font=("Segoe UI", 10), fg=self.text_color, bg=self.bg_color)
        mode_label.pack(side=tk.LEFT, padx=(0, 10))

        self.mode_var = tk.StringVar(value="spitter")

        visual_rb = tk.Radiobutton(mode_frame, text="Visuell (spitter)",
                                   variable=self.mode_var, value="spitter",
                                   font=("Segoe UI", 10), fg=self.text_color, bg=self.bg_color,
                                   selectcolor=self.secondary_bg, command=self.update_mode)
        visual_rb.pack(side=tk.LEFT, padx=5)

        simple_rb = tk.Radiobutton(mode_frame, text="Einfach (spitter-alt)",
                                   variable=self.mode_var, value="spitter-alt",
                                   font=("Segoe UI", 10), fg=self.text_color, bg=self.bg_color,
                                   selectcolor=self.secondary_bg, command=self.update_mode)
        simple_rb.pack(side=tk.LEFT, padx=5)

        # Drag & Drop-Bereich
        self.drop_frame = tk.Frame(main_frame, bg=self.secondary_bg, padx=20, pady=30)
        self.drop_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.drop_label = tk.Label(self.drop_frame,
                                   text="Ziehe eine JSON-Notendatei hierher oder klicke zum Auswählen",
                                   font=("Segoe UI", 12), fg=self.text_color, bg=self.secondary_bg,
                                   wraplength=500)
        self.drop_label.pack(pady=20)

        button_frame = tk.Frame(self.drop_frame, bg=self.secondary_bg)
        button_frame.pack(pady=10)

        self.browse_btn = tk.Button(button_frame, text="Datei auswählen",
                                    font=("Segoe UI", 10), bg=self.accent_color, fg=self.text_color,
                                    border=0, padx=15, pady=8, command=self.browse_file)
        self.browse_btn.pack(side=tk.LEFT, padx=5)

        # Status-Bereich
        self.status_frame = tk.Frame(main_frame, bg=self.bg_color, pady=10)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = tk.Label(self.status_frame, text="Bereit",
                                     font=("Segoe UI", 10), fg=self.text_color, bg=self.bg_color)
        self.status_label.pack(anchor=tk.W)

        # Footer-Bereich
        footer_frame = tk.Frame(self.root, bg=self.secondary_bg, pady=10)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        footer_text = tk.Label(footer_frame, text="Unterstütztes Format: JSON mit Noteneinträgen",
                               font=("Segoe UI", 8), fg=self.text_color, bg=self.secondary_bg)
        footer_text.pack()

    def update_mode(self):
        self.player_mode = self.mode_var.get()
        self.status_label.config(text=f"Modus gewechselt zu: {self.player_mode}")

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
            ('JSON-Dateien', '*.json;*.txt'),
            ('Alle Dateien', '*.*')
        ]

        file_path = filedialog.askopenfilename(filetypes=file_types)
        if file_path:
            self.process_file(file_path)

    def process_file(self, file_path):
        if not os.path.exists(file_path):
            messagebox.showerror("Fehler", f"Datei nicht gefunden: {file_path}")
            return

        # Prüfe, ob es sich um eine JSON-Datei handelt
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if 'notes' not in data:
                    messagebox.showerror("Fehler", "Die Datei enthält kein gültiges Notenformat (kein 'notes'-Feld)")
                    return
        except json.JSONDecodeError:
            messagebox.showerror("Fehler", "Die Datei enthält kein gültiges JSON-Format")
            return
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Lesen der Datei: {str(e)}")
            return

        self.current_file = file_path
        self.status_label.config(text=f"Datei geladen: {os.path.basename(file_path)}")

        # Starte Player in separatem Thread
        if self.is_playing:
            messagebox.showinfo("Info", "Es läuft bereits eine Wiedergabe. Bitte warten.")
            return

        self.is_playing = True
        self.player_thread = threading.Thread(target=self.play_notes)
        self.player_thread.daemon = True
        self.player_thread.start()

    def play_notes(self):
        try:
            self.status_label.config(text=f"Spiele {os.path.basename(self.current_file)} mit {self.player_mode}...")

            # Wähle das richtige Skript basierend auf dem Modus
            script_name = f"{self.player_mode}.py"

            # Starte den Player als Subprocess
            process = subprocess.Popen([sys.executable, script_name, self.current_file],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Warte auf Beendigung
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8')
                self.root.after(0, lambda: messagebox.showerror("Fehler", f"Fehler bei der Wiedergabe: {error_msg}"))
                self.root.after(0, lambda: self.status_label.config(text="Fehler bei der Wiedergabe"))
            else:
                self.root.after(0, lambda: self.status_label.config(text="Wiedergabe abgeschlossen"))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Fehler", f"Fehler: {str(e)}"))
            self.root.after(0, lambda: self.status_label.config(text=f"Fehler: {str(e)}"))

        self.is_playing = False


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

    app = NotePlayerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()