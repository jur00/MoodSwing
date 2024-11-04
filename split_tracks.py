from pathlib import Path
from typing import List, Dict
import logging

from pydub import AudioSegment

from googleapiclient.discovery import build

from src.utils import normalize, Progress
from src.google_auth import authenticate_with_oauth
from src.google_drive import list_files_in_folder, create_drive_folder, download_one, upload_many
from src.google_sheets import read_sheet, add_value_to_sheet


client_secrets_path = Path("client_secrets.json")
scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

folder_id_map = {
    "tracks_my": "1KqDNssfz3Js1hMT92tBg9R78iah8z1oo",
    "3sec_split_tracks": "1tY4fO2b08nMceIji957Dbm4YkLlmHYjr"
}

file_id_map = {
    "tracks_splitted": "18PnYJ5E_bJtWBUphjEom5FNjWVbZwnA1-8blHmekF6s"
}

def filter_tracks_done_from_tracks_to_do(tracks_to_do: List[Dict[str, str]], tracks_done: List[str]):
    return [item for item in tracks_to_do if normalize(item['name']) not in tracks_done]


def split_audio_file(file_name: str, source_path: Path, destination_path: Path, segment_length: float=3000):
    file_path = source_path.joinpath(file_name)
    audio = AudioSegment.from_file(file_path)

    for i in range(0, len(audio) - 1, segment_length):
        segment = audio[i:i + segment_length]
        segment_number = str(i // segment_length).zfill(3)
        segment_file_name = destination_path.joinpath(f'segment_{segment_number}.mp3')
        segment.export(segment_file_name, format='mp3')


def remove_temporary_files(folder_name: str):
    # Convert the folder path to a Path object
    folder = Path(folder_name)
    # Iterate over all files and directories in the folder
    for item in folder.iterdir():
        item_name = str(item).split('\\')[-1]
        if item_name == '.gitkeep':
            continue
        item.unlink()


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # authentication
    credentials = authenticate_with_oauth(client_secrets_path, scopes)

    # set up drive service
    drive_service = build('drive', 'v3', credentials=credentials)

    # set up google sheets service
    sheets_service = build('sheets', 'v4', credentials=credentials)

    # get list of all tracks
    tracks_to_do = list_files_in_folder(folder_id_map["tracks_my"], drive_service)

    # check which tracks are already splitted
    tracks_done = read_sheet(file_id_map["tracks_splitted"], sheets_service)

    # filter my tracks, so only the unsplitted tracks are left
    tracks_to_do = filter_tracks_done_from_tracks_to_do(tracks_to_do, tracks_done)

    n_tracks_to_do = len(tracks_to_do)

    logging.info(f'Still {n_tracks_to_do} tracks to split')

    # split my tracks
    progress = Progress()
    for track in tracks_to_do[:20]:

        # first create new empty splitted track folder
        splitted_folder_id = create_drive_folder(normalize(track["name"]), folder_id_map["3sec_split_tracks"], drive_service)

        # download track
        download_one(track["id"], Path(f"track_temp/{track['name']}"), drive_service)

        # split
        split_audio_file(track["name"], Path("track_temp"), Path("splitted_temp"))

        # upload all resulting track segments
        upload_many(splitted_folder_id, Path("splitted_temp"), drive_service)

        # log the completed folder name to sheets logging
        add_value_to_sheet(normalize(track["name"]), file_id_map["tracks_splitted"], sheets_service)

        # clean-up temporary local temporary files
        remove_temporary_files("track_temp")

        remove_temporary_files("splitted_temp")

        # log progress
        progress.log(track, tracks_to_do)
