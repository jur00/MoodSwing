from pathlib import Path
import json
from typing import List
import io

from pydub import AudioSegment

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

client_secrets_path = Path("client_secret_595444979670-ui22j3vs7v2uav527s3vhdhalg8t6e2k.apps.googleusercontent.com.json")
scopes = ['https://www.googleapis.com/auth/drive']
folder_id_map = {
    "tracks_my": "1KqDNssfz3Js1hMT92tBg9R78iah8z1oo",
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

def list_files_in_folder(service, folder_id):
    query = f"'{folder_id}' in parents"  # Query to get files in the specified folder
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])

    return items

# Function to download a file from Google Drive
def download_file(file_id, file_name):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()  # Create a bytes buffer to store the downloaded content

    # Create a downloader object
    downloader = MediaIoBaseDownload(fh, request)
    done = False

    # Download the file in chunks
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")

    # Write the downloaded content to a file
    with open(Path(f"track_temp/{file_name}"), 'wb') as f:
        f.write(fh.getvalue())


def clear_temporary_downloads():
    # Convert the folder path to a Path object
    folder = Path('track_temp')
    # Iterate over all files and directories in the folder
    for item in folder.iterdir():
        item.unlink()

credentials = authenticate_with_oauth(client_secrets_path, scopes)

# Initialize Google Drive API
drive_service = build('drive', 'v3', credentials=credentials)

tracks = list_files_in_folder(drive_service, folder_id_map["tracks_my"])

file_id, file_name = tracks[0].values()

download_file(file_id, file_name)

clear_temporary_downloads()