from pathlib import Path
from typing import List, Dict
import io
import argparse

import numpy as np
from pydub import AudioSegment

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from src.utils import stem, Progress


client_secrets_path = Path("client_secrets.json")
scopes = ['https://www.googleapis.com/auth/drive']
folder_id_map = {
    "tracks_my": "1KqDNssfz3Js1hMT92tBg9R78iah8z1oo",
    "3sec_split_tracks": "1I-DPdGfHS_6zLX63RhhNBpo9ohEUhj2O"
}


def authenticate_with_oauth(client_secrets_path: Path, scopes: List):
    creds = None
    # Check if the token.json file exists
    token_path = Path('token.json')

    # Load credentials from the token file if it exists
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, scopes)

    # If there are no valid credentials, we need to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, scopes)
            creds = flow.run_local_server(port=0)  # This will prompt for browser authentication

        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return creds


def list_files_in_folder(folder_id, service):
    items = []
    query = f"'{folder_id}' in parents"
    page_token = None

    while True:
        results = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name)",
            pageToken=page_token
        ).execute()

        # Append the current page of files to the list
        items.extend(results.get('files', []))

        # Get the next page token
        page_token = results.get('nextPageToken')

        # If there’s no next page, break out of the loop
        if not page_token:
            break

    return items


def list_folders_in_folder(folder_id, service):
    items = []
    query = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
    page_token = None

    while True:
        results = service.files().list(
            q=query,
            fields="nextPageToken, files(name)",
            pageToken=page_token
        ).execute()

        # Append the current page of files to the list
        items.extend(results.get('files', []))

        # Get the next page token
        page_token = results.get('nextPageToken')

        # If there’s no next page, break out of the loop
        if not page_token:
            break

    item_names = [item['name'] for item in items]

    return item_names


def filter_tracks_done_from_tracks_to_do(tracks_to_do: List[Dict[str, str]], tracks_done: List[str]):
    return [item for item in tracks_to_do if stem(item['name']) not in tracks_done]


def create_track_batches(tracks_to_do: List[Dict[str, str]]):
    track_batches = np.array_split(tracks_to_do, 5)
    return track_batches


def create_drive_folder(folder_name: str, parent_folder_id: str, service):
    # Define metadata for the new folder
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id] if parent_folder_id else []
    }
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    print(f"Created Google Drive folder '{folder_name}' with ID: {folder.get('id')}")
    return folder.get('id')


def download_file(file_id, file_name, service):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()  # Create a bytes buffer to store the downloaded content

    # Create a downloader object
    downloader = MediaIoBaseDownload(fh, request)
    done = False

    # Download the file in chunks
    while done is False:
        status, done = downloader.next_chunk()
        # print(f"Download {int(status.progress() * 100)}%.")

    # Write the downloaded content to a file
    with open(Path(f"track_temp/{file_name}"), 'wb') as f:
        f.write(fh.getvalue())


def split_audio_file(file_name: str, source_path: Path, destination_path: Path, segment_length: float=3000):
    file_path = source_path.joinpath(file_name)
    audio = AudioSegment.from_file(file_path)

    for i in range(0, len(audio) - 1, segment_length):
        segment = audio[i:i + segment_length]
        segment_number = str(i // segment_length).zfill(3)
        segment_file_name = destination_path.joinpath(f'segment_{segment_number}.mp3')
        segment.export(segment_file_name, format='mp3')


def upload_segments(local_folder_path: Path, splitted_folder_id: str, service):
    # Iterate over files in the folder
    for file_path in local_folder_path.rglob('*'):
        # Skip directories and .gitkeep file
        if file_path.is_dir() or file_path.name == '.gitkeep':
            continue

        # Define file metadata and upload
        file_metadata = {
            'name': file_path.name,
            'parents': [splitted_folder_id]
        }
        media = MediaFileUpload(str(file_path), resumable=True)
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        # print(f"Uploaded '{file_path.name}' to Google Drive folder ID '{splitted_folder_id}'")


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

    # get batch number, so it defines the tracks it will split
    parser = argparse.ArgumentParser(description="Script to process and split files in batches.")

    parser.add_argument("--batch", type=str, required=True, help="The batch name to process (e.g., --batch batch1).")

    args = parser.parse_args()

    batch = int(args.batch.split('_')[-1])

    # authentication
    credentials = authenticate_with_oauth(client_secrets_path, scopes)

    # set up drive service
    drive_service = build('drive', 'v3', credentials=credentials)

    # get list of all tracks
    tracks_to_do = list_files_in_folder(folder_id_map["tracks_my"], drive_service)

    # check which tracks are already splitted
    tracks_done = list_folders_in_folder(folder_id_map["3sec_split_tracks"], drive_service)

    # filter my tracks, so only the unsplitted tracks are left
    tracks_to_do = filter_tracks_done_from_tracks_to_do(tracks_to_do, tracks_done)

    # get only the nth batch
    track_batches = create_track_batches(tracks_to_do)

    track_batch = track_batches[batch-1]

    # split my tracks
    progress = Progress()
    for track in track_batch[:100]:

        # first create new empty splitted track folder
        create_drive_folder(stem(track["name"]), folder_id_map["3sec_split_tracks"], drive_service)

        # download track
        download_file(track["id"], track["name"], drive_service)

        # split
        split_audio_file(track["name"], Path("track_temp"), Path("splitted_temp"))

        # upload all resulting track segments
        upload_segments(Path("splitted_temp"), folder_id_map["3sec_split_tracks"], drive_service)

        # clean-up temporary local temporary files
        remove_temporary_files("track_temp")

        remove_temporary_files("splitted_temp")

        # show progress
        progress.show(track, tracks_to_do)
