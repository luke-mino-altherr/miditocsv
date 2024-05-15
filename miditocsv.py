import os
import pandas as pd
from mido import MidiFile, MetaMessage, Message, MidiTrack
import click

@click.group()
def cli():
    """A CLI for converting MIDI files to CSV and vice versa."""
    pass

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
def mid_to_csv(input_file, output_file):
    """Convert a MIDI file to a CSV file."""
    df = pd.DataFrame()
    mid = MidiFile(input_file)

    for n_track, track in enumerate(mid.tracks):
        track_df = pd.DataFrame()
        time = 0

        for msg in track:
            msg_dict = msg.__dict__
            msg_dict["meta"] = int(isinstance(msg, MetaMessage))
            msg_dict["track"] = n_track

            if "time" not in msg_dict:
                continue

            time += int(msg_dict["time"])
            msg_dict["tick"] = time

            track_df = pd.concat([track_df, pd.DataFrame([msg_dict])], ignore_index=True)

        if df.shape[0] > 0:
            df = pd.merge(df, track_df, how="outer")
        else:
            df = track_df

    for col in df.columns:
        if df[col].dtype == "float64":
            df[col] = df[col].astype("Int64")

    df.set_index("tick", inplace=True)
    df.sort_index(inplace=True)
    df.to_csv(output_file)

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
def csv_to_mid(input_file, output_file):
    """Convert a CSV file to a MIDI file."""
    df = pd.read_csv(input_file)
    n_tracks = max(df["track"])
    mid = MidiFile()
    tracks = {i: MidiTrack() for i in range(n_tracks + 1)}

    for _, row in df.iterrows():
        msg_class = MetaMessage if row["meta"] else Message
        track = int(row["track"])
        row.drop(["meta", "track", "tick"], inplace=True)
        params = dict(row.dropna())

        for k, v in params.items():
            if type(v) is float:
                params[k] = int(v)

        tracks[track].append(msg_class(**params))

    for track in tracks.values():
        if len(track):
            mid.tracks.append(track)

    mid.save(output_file)

def main():
    cli()
