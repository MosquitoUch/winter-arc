# Eigene Stimme für den Coach

Die App kann auf drei Arten sprechen. Sie nimmt die erste, die verfügbar ist:

1. **Eigenes Piper-Modell** direkt auf dem Handy. Spricht jeden Satz frei.
2. **Voice-Pack**: fertige Audio-Clips, aus denen die App ihre Sätze zusammensetzt.
3. **Systemstimme** des Handys.

Alles findest du in der App unter **Plan → Aussehen → Coach-Stimmen und Sprüche**.
Du kannst mehrere **Stimm-Profile** anlegen (zum Beispiel Motivator und Entspannt). Jedes hat eigene Sprüche,
eine eigene Persönlichkeit für den KI-Coach und optional ein eigenes Modell oder Voice-Pack.

## 1. Piper-Modell laden

Ein Piper-Modell besteht aus zwei Dateien, `stimme.onnx` und `stimme.onnx.json`.
Kopier beide aufs Handy und wähl sie unter „Modell laden" gemeinsam aus.
Beim ersten Satz lädt die App einmalig die Sprach-Engine (etwa 30 MB), danach geht es offline.

Eine eigene Piper-Stimme trainierst du am PC mit dem Piper-Trainingscode
(github.com/rhasspy/piper, Ordner `src/python`, Anleitung TRAINING.md).
Am einfachsten ist das Feintuning eines vorhandenen deutschen Modells mit deinen eigenen Aufnahmen
oder mit Audio, das du selbst erzeugt hast und nutzen darfst.

## 2. Voice-Pack mit `make_voicepack.py`

Für Modelle, die nicht auf dem Handy laufen (XTTS, StyleTTS, alles Eigene):

1. In der App das Profil wählen, Sprüche fertig schreiben, dann „Satzliste exportieren" → `voicepack-<profil>.json`
2. Am PC:

```
python make_voicepack.py voicepack-saetze.json --piper stimme.onnx
python make_voicepack.py voicepack-saetze.json --py mein_tts.py
python make_voicepack.py voicepack-saetze.json --cmd "mein_tts --text {text} --out {out}"
```

`mein_tts.py` braucht nur eine Funktion `speak(text, out_path)`, die eine WAV-Datei schreibt.
Mit `--format ogg` (braucht ffmpeg) wird das Pack deutlich kleiner.

3. Das fertige `voicepack.zip` in der App laden.

Die Texte in der JSON-Datei darfst du ändern, zum Beispiel „Pause vorbei." zu „Steh auf, Jäger.".
Die IDs müssen bleiben, weil die App die Clips über ihre Namen findet.
Kommt eine neue Übung in deinen Plan, exportierst du die Liste neu und erzeugst nur die fehlenden Clips:

```
python make_voicepack.py voicepack-saetze.json --py mein_tts.py --keep clips
```
