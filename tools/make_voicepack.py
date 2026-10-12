#!/usr/bin/env python3
"""
Voice-Pack-Generator für die Winter-Arc-App
===========================================

Schickt jeden Satz aus der Satzliste der App durch dein eigenes Stimmmodell
und packt die Audiodateien als ZIP, das du in der App unter
Plan → Aussehen → Coach-Stimme und Voice-Pack lädst.

1. In der App: "Satzliste exportieren" → voicepack-saetze.json
2. Am PC eine der Varianten ausführen:

   Piper (https://github.com/rhasspy/piper, pip install piper-tts):
     python make_voicepack.py voicepack-saetze.json --piper meine_stimme.onnx

   Eigenes Python-Modell: eine Datei mit einer Funktion speak(text, out_path),
   die eine WAV-Datei nach out_path schreibt:
     python make_voicepack.py voicepack-saetze.json --py mein_tts.py

   Beliebiges Programm, {text} und {out} werden ersetzt:
     python make_voicepack.py voicepack-saetze.json --cmd "mein_tts --text {text} --out {out}"

Optionen:
  --name "Meine Stimme"   Name, den die App anzeigt
  --out voicepack.zip      Zieldatei
  --format ogg|mp3|wav     ogg/mp3 machen das Pack viel kleiner (braucht ffmpeg im PATH)
  --only id1,id2           nur bestimmte Clips erzeugen (zum Nachbessern)
  --keep ordner            Zwischendateien in diesem Ordner behalten; vorhandene Clips werden
                           übersprungen, so kannst du einzelne Dateien löschen und neu erzeugen

Die Texte in der JSON-Datei darfst du ändern (zum Beispiel "Pause vorbei." zu
"Steh auf, Jäger."), die IDs aber nicht: Jede ID wird zu einer Audiodatei mit
genau diesem Namen, und die App setzt daraus ihre Sätze zusammen.
"""
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile


def quote(s):
    """Text sicher für die Kommandozeile verpacken (Windows und Linux/macOS)."""
    if os.name == "nt":
        return '"' + s.replace('"', '\\"') + '"'
    import shlex
    return shlex.quote(s)


def make_engine(args):
    if args.piper:
        exe = args.piper_bin or shutil.which("piper") or "piper"

        def speak(text, out):
            subprocess.run([exe, "--model", args.piper, "--output_file", out],
                           input=text.encode("utf-8"), check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return speak
    if args.py:
        spec = importlib.util.spec_from_file_location("eigenes_tts", args.py)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "speak"):
            sys.exit("Die Datei " + args.py + " braucht eine Funktion speak(text, out_path).")
        return mod.speak
    if args.cmd:
        def speak(text, out):
            subprocess.run(args.cmd.format(text=quote(text), out=quote(out)), shell=True, check=True)
        return speak
    sys.exit("Wähle ein Stimmmodell: --piper modell.onnx, --py datei.py oder --cmd \"befehl {text} {out}\"")


def convert(src, fmt):
    if fmt == "wav":
        return src
    ff = shutil.which("ffmpeg")
    if not ff:
        print("Hinweis: ffmpeg nicht gefunden, die Clips bleiben WAV.")
        return src
    dst = os.path.splitext(src)[0] + "." + fmt
    codec = ["-c:a", "libopus", "-b:a", "48k"] if fmt == "ogg" else ["-c:a", "libmp3lame", "-q:a", "4"]
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", src] + codec + [dst], check=True)
    return dst


def main():
    ap = argparse.ArgumentParser(description="Voice-Pack für die Winter-Arc-App erzeugen")
    ap.add_argument("liste", help="voicepack-saetze.json aus der App")
    ap.add_argument("--piper", help="Pfad zu deiner Piper-Stimme (.onnx)")
    ap.add_argument("--piper-bin", help="Pfad zum piper-Programm, falls nicht im PATH")
    ap.add_argument("--py", help="Python-Datei mit speak(text, out_path)")
    ap.add_argument("--cmd", help='Befehl mit {text} und {out}')
    ap.add_argument("--name", default="Eigene Stimme")
    ap.add_argument("--out", default="voicepack.zip")
    ap.add_argument("--format", choices=["wav", "ogg", "mp3"], default="wav")
    ap.add_argument("--only", help="nur diese IDs, mit Komma getrennt")
    ap.add_argument("--keep", help="Ordner für die einzelnen Clips")
    args = ap.parse_args()

    with open(args.liste, encoding="utf-8") as f:
        data = json.load(f)
    clips = data["clips"] if isinstance(data, dict) else data
    if args.only:
        wanted = set(x.strip() for x in args.only.split(","))
        clips = [c for c in clips if c["id"] in wanted]
    speak = make_engine(args)
    work = args.keep or tempfile.mkdtemp(prefix="voicepack_")
    os.makedirs(work, exist_ok=True)

    done = []
    for i, c in enumerate(clips, 1):
        cid, text = c["id"], c["text"]
        existing = [os.path.join(work, cid + "." + e) for e in ("ogg", "mp3", "wav")]
        hit = next((p for p in existing if os.path.exists(p)), None)
        if hit and args.keep:
            done.append(hit)
            continue
        wav = os.path.join(work, cid + ".wav")
        print(f"[{i}/{len(clips)}] {cid}: {text}")
        try:
            speak(text, wav)
            done.append(convert(wav, args.format))
        except Exception as e:  # weitermachen, damit ein Fehler nicht alles stoppt
            print(f"   Fehler bei {cid}: {e}")

    # Bei --keep zusätzlich alle anderen Clips im Ordner mitnehmen (z. B. nach --only)
    if args.keep:
        names = {os.path.basename(p) for p in done}
        for fn in os.listdir(work):
            if fn.lower().endswith((".wav", ".ogg", ".mp3")) and fn not in names:
                stem = os.path.splitext(fn)[0]
                if not any(os.path.splitext(os.path.basename(p))[0] == stem for p in done):
                    done.append(os.path.join(work, fn))

    with zipfile.ZipFile(args.out, "w", zipfile.ZIP_STORED) as z:
        z.writestr("manifest.json", json.dumps({"name": args.name, "version": 1}, ensure_ascii=False))
        seen = set()
        for p in done:
            stem = os.path.splitext(os.path.basename(p))[0]
            if stem in seen:
                continue
            seen.add(stem)
            z.write(p, os.path.basename(p))
    print(f"\nFertig: {args.out} mit {len(seen)} Clips. Lade die Datei in der App unter Coach-Stimme und Voice-Pack.")
    if not args.keep:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
