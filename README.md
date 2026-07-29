# Pitch Visualization

An interactive MIDI pitch visualization for synchronizing generated note data with an audio recording.

The project converts MIDI note events into CSV/JSON files with Python, then loads the cleaned CSV and MP3 in a D3-powered HTML page. The current example uses `Peer Gynt Suite No. 1, Morning Mood`.

## Project Structure

```text
.
+-- assets/
|   +-- audio/              # MP3 files used by the visualization
|   +-- midi/               # Source MIDI files
+-- data/
|   +-- manifest.json       # Optional list of processed track names
|   +-- processed/
|       +-- csv/            # Generated CSV and metadata JSON files
+-- scripts/
|   +-- midi_to_csv_clean.py
+-- index.html              # D3 visualization page
+-- requirements.txt
+-- README.md
```

## Requirements

- Python 3.11+
- A modern browser
- Internet access for the D3 CDN used by `index.html`

Install Python dependencies:

```bash
python -m pip install -r requirements.txt
```

## Generate MIDI Data

Run the default conversion for the included MIDI file:

```bash
python scripts/midi_to_csv_clean.py --classical --update-manifest
```

This reads:

```text
assets/midi/peer_gynt_suite_no_1_morning_mood.mid
```

and writes:

```text
data/processed/csv/peer_gynt_suite_no_1_morning_mood_notes.csv
data/processed/csv/peer_gynt_suite_no_1_morning_mood_notes_clean.csv
data/processed/csv/peer_gynt_suite_no_1_morning_mood_info.json
```

To process another MIDI file:

```bash
python scripts/midi_to_csv_clean.py --midi assets/midi/your_file.mid --output-dir data/processed/csv
```

For classical orchestral files, add:

```bash
--classical
```

## Run the Visualization

Start a local static server from the project root:

```bash
python -m http.server 8000
```

Open:

```text
http://localhost:8000/index.html
```

The page loads:

```text
data/processed/csv/peer_gynt_suite_no_1_morning_mood_notes_clean.csv
assets/audio/peer_gynt_suite_no_1_morning_mood.mp3
```

## How It Works

1. `scripts/midi_to_csv_clean.py` parses MIDI timing, tempo, note pitch, velocity, track, and instrument data.
2. It writes raw note rows and cleaned note rows to CSV.
3. `index.html` loads the cleaned CSV with D3.
4. The MP3 playback time drives the animated pitch markers and duration bars.

## Notes

- The visualization expects the CSV and MP3 filenames to share the same base name.
- If you change the demo file, update the `filename` constant in `index.html`.
- The browser may block audio autoplay, so playback starts from the page button.
