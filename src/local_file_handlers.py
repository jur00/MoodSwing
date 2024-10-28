from pathlib import Path
import os
from typing import List

from pydub import AudioSegment

from src.utils import stem, Progress

source_path = Path("D:\\Data Science\\Lake\\music\\tracks_my")
destination_path = Path("D:\\Data Science\\Lake\\music\\tracks_my_splitted")

def list_items_in_folder(folder_path: Path):
    return [str(item).split('\\')[-1] for item in folder_path.iterdir()]

def remove_tracks_done_from_tracks_to_do(tracks_to_do: List, tracks_done: List):
    return [track for track in tracks_to_do if stem(track) not in tracks_done]

def create_folder(destination_path: Path, file_name: str):
    segment_folder_path = destination_path.joinpath(stem(file_name))
    segment_folder_path.mkdir(parents=True, exist_ok=True)
    return segment_folder_path

def split_audio_file(file_name: str, source_path: Path, destination_path: Path, segment_length: float=3000):
    file_path = source_path.joinpath(file_name)
    audio = AudioSegment.from_file(file_path)

    for i in range(0, len(audio) - 1, segment_length):
        segment = audio[i:i + segment_length]
        segment_number = str(i // segment_length).zfill(3)
        segment_file_name = destination_path.joinpath(f'segment_{segment_number}.mp3')
        segment.export(segment_file_name, format='mp3')

tracks_to_do = list_items_in_folder(source_path)
tracks_done = list_items_in_folder(destination_path)
tracks_to_do_filtered = remove_tracks_done_from_tracks_to_do(tracks_to_do, tracks_done)

progress = Progress()
for file_name in tracks_to_do_filtered:
    segment_folder_path = create_folder(destination_path, file_name)
    split_audio_file(file_name, source_path, segment_folder_path)

    progress.show(file_name, tracks_to_do_filtered)