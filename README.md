# Audio zu Noten Konverter (sniffer.py)

Dieses Tool analysiert Audio-Dateien und extrahiert die enthaltenen Noten im JSON-Format für dein Karaoke-Projekt.

## Features

- Drag & Drop-Unterstützung für einfache Verwendung
- Unterstützt gängige Audio-Formate (.wav, .mp3, .ogg, .flac)
- Benutzerfreundliche Oberfläche mit Fortschrittsanzeige
- Speichert Noten im gewünschten JSON-Format

## Installation

1. Stelle sicher, dass Python 3.7 oder höher installiert ist
2. Installiere die erforderlichen Abhängigkeiten:

```bash
pip install -r requirements.txt
```

## Verwendung

1. Starte das Programm:

```bash
python audio_to_notes.py
```

2. Ziehe eine Audio-Datei in das Fenster oder klicke auf "Datei auswählen"
3. Warte, bis die Analyse abgeschlossen ist
4. Die extrahierten Noten werden in einer JSON-Datei im selben Verzeichnis wie die Audio-Datei gespeichert

## Ausgabeformat

Die Ausgabedatei hat folgendes Format:

```json
{
  "notes": [
    {
      "time": 0.0,
      "pitch": 67,
      "duration": 0.5
    },
    ...
  ]
}
```

- `time`: Startzeit der Note in Sekunden
- `pitch`: MIDI-Tonhöhenwert (z.B. 60 = C4, 69 = A4)
- `duration`: Dauer der Note in Sekunden

## Anpassung

Du kannst die Empfindlichkeit der Notenerkennung anpassen, indem du folgende Parameter in der `extract_notes`-Funktion
änderst:

- `min_note_length`: Minimale Dauer einer Note in Sekunden
- `min_magnitude`: Minimale Lautstärke für eine gültige Note

## Problembehebung

Falls Drag & Drop nicht funktioniert, stelle sicher, dass `tkinterdnd2` korrekt installiert ist:

```bash
pip install tkinterdnd2
```

Bei Problemen mit Audiocodecs könnte die Installation von weiteren Systembibliotheken erforderlich sein.

## Systemanforderungen

- Python 3.7+
- Mindestens 4 GB RAM (für die Analyse längerer Audio-Dateien)

---

# Noten-Player (spitter.py & spitter-alt.py)

Diese Python-Anwendung liest eine JSON-Datei mit musikalischen Noten und gibt sie akustisch wieder.

## Funktionen

- Liest JSON-Dateien im Format `{notes: [{time, pitch, duration}, ...]}`
- Wandelt MIDI-Noten in hörbare Frequenzen um
- Zeigt eine visuelle Repräsentation der Noten an
- Zeigt Fortschritt und aktuell gespielte Noten an
- Piano-Roll-Visualisierung der umliegenden Noten

## Voraussetzungen

- Python 3.x
- pygame
- numpy

## Installation

1. Installiere die erforderlichen Pakete:

```
pip install -r requirements.txt
```

## Verwendung

Starte die Anwendung mit der JSON-Datei als Parameter:

```
python spitter.py notes.json
```

oder

```
python spitter-alt.py notes.json
```

Wenn kein Parameter angegeben wird, wird standardmäßig `paste.txt` im aktuellen Verzeichnis verwendet.

## Steuerung

- ESC-Taste: Beendet die Anwendung
- Das Fenster schließen: Beendet die Anwendung

## Format der JSON-Datei

Die JSON-Datei sollte folgendes Format haben:

```json
{
  "notes": [
    {
      "time": 3.0,
      // Startzeit in Sekunden
      "pitch": 82,
      // MIDI-Tonhöhe (0-127)
      "duration": 0.3
      // Dauer in Sekunden
    }
    // Weitere Noten...
  ]
}
```

## Technische Details

- Die Anwendung generiert Sinuswellen für jede Note
- MIDI-Noten werden nach der Standard-Formel in Frequenzen umgerechnet: 440 * 2^((note-69)/12)
- Die grafische Oberfläche zeigt den Fortschritt, kürzlich gespielte Noten und eine Piano-Roll-Ansicht