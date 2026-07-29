# -*- coding: utf-8 -*-
import argparse
import glob
import json
import math
import os
import re
import sys

import mido
import pandas as pd


MIDI_INSTRUMENT_NAMES = [
    'Acoustic Grand Piano', 'Bright Acoustic Piano', 'Electric Grand Piano', 'Honky-tonk Piano',
    'Electric Piano 1', 'Electric Piano 2', 'Harpsichord', 'Clavinet',
    'Celesta', 'Glockenspiel', 'Music Box', 'Vibraphone', 'Marimba', 'Xylophone',
    'Tubular Bells', 'Dulcimer',
    'Drawbar Organ', 'Percussive Organ', 'Rock Organ', 'Church Organ', 'Reed Organ',
    'Accordion', 'Harmonica', 'Tango Accordion',
    'Acoustic Guitar (nylon)', 'Acoustic Guitar (steel)', 'Electric Guitar (jazz)',
    'Electric Guitar (clean)', 'Electric Guitar (muted)', 'Overdriven Guitar',
    'Distortion Guitar', 'Guitar Harmonics',
    'Acoustic Bass', 'Electric Bass (finger)', 'Electric Bass (pick)', 'Fretless Bass',
    'Slap Bass 1', 'Slap Bass 2', 'Synth Bass 1', 'Synth Bass 2',
    'Violin', 'Viola', 'Cello', 'Contrabass', 'Tremolo Strings', 'Pizzicato Strings',
    'Orchestral Harp', 'Timpani',
    'String Ensemble 1', 'String Ensemble 2', 'Synth Strings 1', 'Synth Strings 2',
    'Choir Aahs', 'Voice Oohs', 'Synth Choir', 'Orchestra Hit',
    'Trumpet', 'Trombone', 'Tuba', 'Muted Trumpet', 'French Horn', 'Brass Section',
    'Synth Brass 1', 'Synth Brass 2',
    'Soprano Sax', 'Alto Sax', 'Tenor Sax', 'Baritone Sax', 'Oboe', 'English Horn',
    'Bassoon', 'Clarinet',
    'Piccolo', 'Flute', 'Recorder', 'Pan Flute', 'Blown Bottle', 'Shakuhachi',
    'Whistle', 'Ocarina',
    'Lead 1 (square)', 'Lead 2 (sawtooth)', 'Lead 3 (calliope)', 'Lead 4 (chiff)',
    'Lead 5 (charang)', 'Lead 6 (voice)', 'Lead 7 (fifths)', 'Lead 8 (bass + lead)',
    'Pad 1 (new age)', 'Pad 2 (warm)', 'Pad 3 (polysynth)', 'Pad 4 (choir)',
    'Pad 5 (bowed)', 'Pad 6 (metallic)', 'Pad 7 (halo)', 'Pad 8 (sweep)',
    'FX 1 (rain)', 'FX 2 (soundtrack)', 'FX 3 (crystal)', 'FX 4 (atmosphere)',
    'FX 5 (brightness)', 'FX 6 (goblins)', 'FX 7 (echoes)', 'FX 8 (sci-fi)',
    'Sitar', 'Banjo', 'Shamisen', 'Koto', 'Kalimba', 'Bagpipe', 'Fiddle', 'Shanai',
    'Tinkle Bell', 'Agogo', 'Steel Drums', 'Woodblock', 'Taiko Drum', 'Melodic Tom',
    'Synth Drum', 'Reverse Cymbal',
    'Guitar Fret Noise', 'Breath Noise', 'Seashore', 'Bird Tweet', 'Telephone Ring',
    'Helicopter', 'Applause', 'Gunshot',
]

VOCAL_MAP = {
    'soprano': 'Soprano',
    'alto': 'Alto',
    'tenor': 'Tenor',
    'bass': 'Bass',
    'choir': 'Choir',
    'chorus': 'Choir',
    'voice': 'Voice',
    'vocal': 'Voice',
    'satb': 'Choir',
    'aahs': 'Choir',
    'oohs': 'Choir',
}

INSTRUMENT_MAP = {
    'violin': 'Violin',
    'violini': 'Violin',
    'viola': 'Viola',
    'viole': 'Viola',
    'violoncelli': 'Cello',
    'cello': 'Cello',
    'contrabass': 'Contrabass',
    'contrabbassi': 'Contrabass',
    'pizzicatostrings': 'Pizzicato Strings',
    'pizzicato': 'Pizzicato Strings',
    'flute': 'Flute',
    'piccolo': 'Piccolo',
    'oboe': 'Oboe',
    'englishhorn': 'English Horn',
    'clarinet': 'Clarinet',
    'bassoon': 'Bassoon',
    'trumpet': 'Trumpet',
    'frenchhorn': 'French Horn',
    'trombone': 'Trombone',
    'tuba': 'Tuba',
    'harpsichord': 'Harpsichord',
    'piano': 'Piano',
    'pianoforte': 'Piano',
    'acousticgrandpiano': 'Piano',
    'electricpiano': 'Electric Piano',
    'churchorgan': 'Organ',
    'drawbarorgan': 'Organ',
    'orchestralharp': 'Harp',
    'timpani': 'Timpani',
    'saxophone': 'Saxophone',
    'sax': 'Saxophone',
    'strings': 'Strings',
    'woodwind': 'Woodwind',
    'brass': 'Brass Section',
    'keyboard': 'Keyboard',
    'percussion/kit': 'Percussion/Kit',
    'stringensemble': 'Strings',
    'synthstrings': 'Strings',
    'brasssection': 'Brass Section',
    'tremolostrings': 'Strings',
    'acousticguitar': 'Guitar',
    'electricguitar': 'Guitar',
    'synthbass': 'Bass',
    'synthbrass': 'Brass Section',
    'synthchoir': 'Choir',
    'acousticbass': 'Acoustic Bass',
    'electricbass': 'Electric Bass',
    'fretlessbass': 'Fretless Bass',
    'bassstrings': 'Strings',
}


def get_instrument_name(program_number):
    if 0 <= program_number < len(MIDI_INSTRUMENT_NAMES):
        return MIDI_INSTRUMENT_NAMES[program_number]
    return f"Instrument_{program_number}"


def get_base_instrument_name(inst_with_num):
    return re.sub(r' _ \d+$', '', inst_with_num)


def get_instrument_family(instrument_name):
    name = instrument_name.lower().replace(' ', '').replace('_', '').replace('1', '').replace('2', '')
    if any(token in name for token in ['violin', 'viola', 'cello', 'contrabass', 'strings', 'ensemble', 'pizzicato']):
        return 'strings'
    if any(token in name for token in ['flute', 'oboe', 'clarinet', 'bassoon', 'sax']):
        return 'woodwind'
    if any(token in name for token in ['trumpet', 'trombone', 'tuba', 'horn', 'brass']):
        return 'brass'
    if any(token in name for token in ['harpsichord', 'piano', 'organ', 'celesta']):
        return 'keyboard'
    if any(token in name for token in ['choir', 'voice', 'aahs', 'oohs']):
        return 'vocal'
    if any(token in name for token in ['timpani', 'drum', 'percussion', 'kit']):
        return 'percussion/kit'
    return name


def clean_instrument_name(name):
    if isinstance(name, str):
        return re.sub(r'[\s_\d-]', '', name).lower()
    return str(name).lower()


def find_keyword_match(text, instrument_map):
    if not isinstance(text, str):
        return None
    cleaned_text = re.sub(r'[\s-]', '', text).lower()
    for key, normalized_name in instrument_map.items():
        if key in cleaned_text:
            return normalized_name
    return None


def calculate_sequence_similarity(notes1_df, notes2_df):
    if notes1_df.empty or notes2_df.empty:
        return 0.0
    set1 = set(tuple(x) for x in notes1_df[['pitch', 'time_start_tick', 'duration_tick']].values)
    set2 = set(tuple(x) for x in notes2_df[['pitch', 'time_start_tick', 'duration_tick']].values)
    min_size = min(len(set1), len(set2))
    if min_size == 0:
        return 0.0
    return len(set1.intersection(set2)) / min_size


def compute_music_metrics(df, total_duration_sec):
    if df is None or df.empty:
        return {'avg_velocity': 0.0, 'timbre_complexity': 0.0, 'harmonic_complexity': 0.0}

    avg_velocity = float(df['velocity'].mean())
    inst_counts = df['instrument_raw'].value_counts()
    total_notes = inst_counts.sum()
    timbre_complexity = 0.0
    if total_notes > 0 and len(inst_counts) > 1:
        probs = inst_counts / total_notes
        entropy = -float((probs * probs.apply(math.log2)).sum())
        max_entropy = math.log2(len(inst_counts))
        if max_entropy > 0:
            timbre_complexity = entropy / max_entropy

    harmonic_complexity = float(len(df) / total_duration_sec) if total_duration_sec > 0 else 0.0
    return {
        'avg_velocity': avg_velocity,
        'timbre_complexity': timbre_complexity,
        'harmonic_complexity': harmonic_complexity,
    }


def generate_original_df(midi_file_path):
    try:
        midi = mido.MidiFile(midi_file_path)
    except Exception as exc:
        print(f"Error: could not read MIDI file {midi_file_path}. Details: {exc}")
        return None, 0, 4, 4, 0, 0

    notes_list = []
    ticks_per_beat = midi.ticks_per_beat
    tempo_changes = [(0, 500000)]
    numerator = 4
    denominator = 4
    channel_instruments = {i: 0 for i in range(16)}

    for track in midi.tracks:
        abs_tick_track = 0
        for msg in track:
            abs_tick_track += msg.time
            if msg.type == 'program_change' and hasattr(msg, 'channel'):
                channel_instruments[msg.channel] = msg.program
            if msg.is_meta:
                if msg.type == 'set_tempo':
                    tempo_changes.append((abs_tick_track, msg.tempo))
                elif msg.type == 'time_signature':
                    numerator = msg.numerator
                    denominator = msg.denominator

    tempo_changes.sort(key=lambda x: x[0])

    def get_time_sec(abs_tick):
        time_sec = 0.0
        for i, (tick_start, tempo) in enumerate(tempo_changes):
            tick_end = tempo_changes[i + 1][0] if i + 1 < len(tempo_changes) else abs_tick + 1
            ticks_to_calculate = min(abs_tick, tick_end) - tick_start
            if ticks_to_calculate > 0:
                time_sec += mido.tick2second(ticks_to_calculate, ticks_per_beat, tempo)
            if abs_tick <= tick_end:
                break
        return time_sec

    active_notes = {}
    for track_idx, track in enumerate(midi.tracks):
        track_name_raw = next((msg.name for msg in track if msg.type == 'track_name'), f"Track {track_idx}")
        track_name_clean = re.sub(r'[^\w\s-]', '', track_name_raw).strip()
        final_track_name = track_name_clean if track_name_clean else f"Track_{track_idx}"
        abs_tick_track = 0
        for msg in track:
            abs_tick_track += msg.time
            time_sec = get_time_sec(abs_tick_track)
            if msg.is_meta:
                continue
            if msg.type in ('note_on', 'note_off') and hasattr(msg, 'note'):
                channel = msg.channel
                instrument_program = channel_instruments.get(channel, 0)
                instrument_name_raw = "Drum Kit" if channel == 9 else get_instrument_name(instrument_program)
                key = (track_idx, msg.note)
                if msg.type == 'note_on' and msg.velocity > 0:
                    if key not in active_notes:
                        active_notes[key] = {
                            'time_start_sec': time_sec,
                            'time_start_tick': abs_tick_track,
                            'pitch': msg.note,
                            'velocity': msg.velocity,
                            'track': final_track_name,
                            'instrument_raw': instrument_name_raw,
                        }
                elif key in active_notes:
                    note_info = active_notes.pop(key)
                    duration_sec = time_sec - note_info['time_start_sec']
                    duration_tick = abs_tick_track - note_info['time_start_tick']
                    if duration_sec > 0.001:
                        notes_list.append({
                            'time_start_sec': note_info['time_start_sec'],
                            'duration_sec': duration_sec,
                            'pitch': note_info['pitch'],
                            'velocity': note_info['velocity'],
                            'track': note_info['track'],
                            'instrument_raw': note_info['instrument_raw'],
                            'time_start_tick': note_info['time_start_tick'],
                            'duration_tick': duration_tick,
                        })

    if not notes_list:
        print("Warning: no valid notes were found in the MIDI file.")
        return None, 0, 4, 4, 0, ticks_per_beat

    df = pd.DataFrame(notes_list)
    time_offset = df['time_start_sec'].min()
    df['time_start_sec'] = df['time_start_sec'] - time_offset

    def apply_instrument_numbering_fixed(group):
        unique_tracks_in_group = sorted(group['track'].unique())
        track_to_number = {track_name: i + 1 for i, track_name in enumerate(unique_tracks_in_group)}
        instrument_name = group.name
        return pd.Series(
            [f"{instrument_name} _ {track_to_number[track_name]}" for track_name in group['track']],
            index=group.index,
        )

    try:
        temp_series = df.groupby('instrument_raw', group_keys=False).apply(apply_instrument_numbering_fixed)
        df['instrument'] = temp_series.reindex(df.index)
    except ValueError:
        results = [apply_instrument_numbering_fixed(group) for _, group in df.groupby('instrument_raw')]
        df['instrument'] = pd.concat(results).sort_index()

    final_bpm = mido.tempo2bpm(tempo_changes[-1][1])
    return df, final_bpm, numerator, denominator, time_offset, ticks_per_beat


def normalize_classical_tracks(df_clean):
    df_clean = df_clean.copy().reset_index(drop=True)
    df_clean['instrument_base'] = df_clean['instrument'].apply(get_base_instrument_name)

    def get_normalized_name(row):
        instrument_base = row['instrument_base']
        track_name = row['track']
        cleaned_inst_key = clean_instrument_name(instrument_base)
        family_of_base_inst = get_instrument_family(instrument_base)
        if cleaned_inst_key == 'bassoon':
            return INSTRUMENT_MAP.get('bassoon')
        instrument_name_from_track = find_keyword_match(track_name, INSTRUMENT_MAP)
        if instrument_name_from_track:
            return instrument_name_from_track
        normalized_name_from_inst_exact = INSTRUMENT_MAP.get(cleaned_inst_key)
        if normalized_name_from_inst_exact:
            return normalized_name_from_inst_exact
        vocal_name_from_track = find_keyword_match(track_name, VOCAL_MAP)
        if vocal_name_from_track and family_of_base_inst == 'vocal':
            return vocal_name_from_track
        vocal_name_from_inst = find_keyword_match(instrument_base, VOCAL_MAP)
        if vocal_name_from_inst:
            return vocal_name_from_inst
        if instrument_base == "Drum Kit":
            return "Percussion/Kit"
        family_key = get_instrument_family(instrument_base)
        normalized_name_from_family = INSTRUMENT_MAP.get(family_key)
        if normalized_name_from_family:
            return normalized_name_from_family
        return instrument_base

    df_clean['instrument_normalized'] = df_clean.apply(get_normalized_name, axis=1)
    indices_to_drop = []
    final_part_names = {}

    for normalized_name, group_df in df_clean.groupby('instrument_normalized'):
        unique_parts_raw = sorted(set(group_df['instrument']))
        part_notes = {part: group_df[(group_df['instrument'] == part).values] for part in unique_parts_raw}
        processed_parts = set()
        part_groups = []

        for i, main_part in enumerate(unique_parts_raw):
            if main_part in processed_parts:
                continue
            redundant_group = [main_part]
            for other_part in unique_parts_raw[i + 1:]:
                if other_part in processed_parts:
                    continue
                similarity = calculate_sequence_similarity(part_notes[main_part], part_notes[other_part])
                if similarity > 0.99:
                    redundant_group.append(other_part)
            part_groups.append(redundant_group)
            for k, part_raw in enumerate(redundant_group):
                if k > 0:
                    indices_to_drop.extend(part_notes[part_raw].index.tolist())
                processed_parts.add(part_raw)

        kept_parts = [group[0] for group in part_groups]

        def get_original_number(part_name):
            match = re.search(r' _ (\d+)$', part_name)
            return int(match.group(1)) if match else 999

        kept_parts.sort(key=get_original_number)
        for i, part_raw in enumerate(kept_parts):
            final_name = f"{normalized_name} {i + 1}"
            generic_names = ['Strings', 'Brass Section', 'Keyboard', 'Percussion/Kit', 'Choir', 'Voice', 'Guitar']
            if len(kept_parts) == 1 and normalized_name not in generic_names:
                final_name = normalized_name
            redundant_group_to_map = next(group for group in part_groups if group[0] == part_raw)
            for part_to_map in redundant_group_to_map:
                final_part_names[part_to_map] = final_name

    df_clean['track_new'] = df_clean['instrument'].apply(lambda x: final_part_names.get(x, x))
    df_clean = df_clean.drop(indices_to_drop, errors='ignore').reset_index(drop=True)
    return df_clean, len(indices_to_drop)


def save_output_files(df, base_name, suffix, bpm_data, genre=None, artist=None, title=None, duration_sec=None):
    csv_path = f"{base_name}{suffix}.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved note data: {csv_path}")

    json_path = f"{base_name}_info.json"
    info_data = dict(bpm_data)
    if genre is not None:
        info_data["genre"] = genre
    if artist is not None:
        info_data["artist"] = artist
    if title is not None:
        info_data["title"] = title
    if duration_sec is not None:
        info_data["duration_sec"] = duration_sec
    with open(json_path, 'w', encoding='utf-8') as file:
        json.dump(info_data, file, indent=4)
    print(f"Saved metadata: {json_path}")


def update_manifest_file(manifest_path, new_entries, overwrite=False):
    if not new_entries:
        print("No new manifest entries.")
        return
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)

    if overwrite:
        manifest_list = list(dict.fromkeys(new_entries))
        with open(manifest_path, 'w', encoding='utf-8') as file:
            json.dump(manifest_list, file, ensure_ascii=False, indent=4)
        print(f"Manifest refreshed with {len(manifest_list)} entries.")
        return

    manifest_list = []
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, list):
                    manifest_list = data
                else:
                    print("Warning: manifest content is not a list; starting from an empty list.")
        except json.JSONDecodeError:
            print("Warning: manifest JSON is invalid; starting from an empty list.")

    added = 0
    for name in new_entries:
        if name not in manifest_list:
            manifest_list.append(name)
            added += 1

    if added > 0:
        with open(manifest_path, 'w', encoding='utf-8') as file:
            json.dump(manifest_list, file, ensure_ascii=False, indent=4)
        print(f"Manifest updated with {added} new entries.")
    else:
        print("Manifest already includes all entries.")


def process_midi(midi_path, output_dir, classical=False, manifest_path=None, update_manifest=False):
    os.makedirs(output_dir, exist_ok=True)
    midi_filename = os.path.basename(midi_path)
    base_name, _ = os.path.splitext(midi_filename)
    output_base_path = os.path.join(output_dir, base_name)
    name_parts = base_name.split('_')
    genre = name_parts[0] if len(name_parts) > 0 else ""
    artist = name_parts[1] if len(name_parts) > 1 else ""
    title = name_parts[-1] if len(name_parts) > 0 else ""

    print(f"Processing {midi_filename}")
    df_original, final_bpm, numerator, denominator, _, ticks_per_beat = generate_original_df(midi_path)
    if df_original is None:
        return None

    total_duration_sec = df_original['time_start_sec'].max() + df_original['duration_sec'].max()
    bpm_data = {
        'bpm': final_bpm,
        'numerator': numerator,
        'denominator': denominator,
        'ticks_per_beat': ticks_per_beat,
        **compute_music_metrics(df_original, total_duration_sec),
    }

    df_original_final = df_original.drop(columns=['instrument_raw'])
    save_output_files(df_original_final, output_base_path, '_notes', bpm_data, genre, artist, title, total_duration_sec)

    if classical:
        df_clean, dropped_count = normalize_classical_tracks(df_original)
        print(f"Removed {dropped_count} redundant note rows.")
    else:
        df_clean = df_original.copy().reset_index(drop=True)
        df_clean['track_new'] = df_clean['instrument']

    df_clean = df_clean.drop(columns=['instrument_base', 'instrument_raw', 'instrument_normalized'], errors='ignore')
    clean_column_order = [
        'time_start_sec', 'duration_sec', 'pitch', 'velocity', 'track', 'instrument',
        'track_new', 'time_start_tick', 'duration_tick',
    ]
    df_clean = df_clean[clean_column_order]
    save_output_files(df_clean, output_base_path, '_notes_clean', bpm_data, genre, artist, title, total_duration_sec)

    if update_manifest and manifest_path:
        update_manifest_file(manifest_path, [base_name])

    return {
        'base_name': base_name,
        'notes_csv': f"{output_base_path}_notes.csv",
        'clean_csv': f"{output_base_path}_notes_clean.csv",
        'info_json': f"{output_base_path}_info.json",
    }


def build_parser():
    parser = argparse.ArgumentParser(description="Convert MIDI note events to CSV/JSON files.")
    parser.add_argument("--midi", default="peer_gynt_suite_no_1_morning_mood.mid", help="Path to a MIDI file.")
    parser.add_argument("--output-dir", default=os.path.join("data", "processed"), help="Output directory.")
    parser.add_argument("--classical", action="store_true", help="Normalize classical orchestral track names.")
    parser.add_argument("--batch-dir", help="Process all .mid/.midi files in this directory.")
    parser.add_argument("--manifest", default=os.path.join("data", "manifest.json"), help="Manifest path for batch outputs.")
    parser.add_argument("--update-manifest", action="store_true", help="Append processed names to the manifest.")
    parser.add_argument("--overwrite-manifest", action="store_true", help="Replace the manifest with batch results.")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    processed_names = []

    if args.batch_dir:
        midi_files = glob.glob(os.path.join(args.batch_dir, "*.mid")) + glob.glob(os.path.join(args.batch_dir, "*.midi"))
        if not midi_files:
            print(f"No MIDI files found in {args.batch_dir}.")
            return 0
        for midi_path in midi_files:
            result = process_midi(midi_path, args.output_dir, args.classical)
            if result:
                processed_names.append(result['base_name'])
        if args.overwrite_manifest:
            update_manifest_file(args.manifest, processed_names, overwrite=True)
        elif args.update_manifest:
            update_manifest_file(args.manifest, processed_names)
        return 0

    if not os.path.exists(args.midi):
        print(f"Error: MIDI file not found: {args.midi}")
        return 1

    result = process_midi(args.midi, args.output_dir, args.classical, args.manifest, args.update_manifest)
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
