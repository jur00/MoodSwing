from pathlib import Path
import io
import time
import ssl

from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload


def list_files_in_folder(folder_id: str, drive_service):
    items = []
    query = f"'{folder_id}' in parents"
    page_token = None

    while True:
        results = drive_service.files().list(
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

def list_folders_in_folder(folder_id: str, drive_service):
    items = []
    query = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
    page_token = None

    while True:
        results = drive_service.files().list(
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

def create_drive_folder(folder_name: str, parent_folder_id: str, drive_service):
    # Define metadata for the new folder
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id] if parent_folder_id else []
    }
    folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
    # print(f"Created Google Drive folder '{folder_name}' with ID: {folder.get('id')}")
    return folder.get('id')

def download_one(drive_file_id: str, local_file_path: Path, drive_service):
    request = drive_service.files().get_media(fileId=drive_file_id)
    fh = io.BytesIO()  # Create a bytes buffer to store the downloaded content

    # Create a downloader object
    downloader = MediaIoBaseDownload(fh, request)
    done = False

    # Download the file in chunks
    while done is False:
        status, done = downloader.next_chunk()
        # print(f"Download {int(status.progress() * 100)}%.")

    # Write the downloaded content to a file
    with open(local_file_path, 'wb') as f:
        f.write(fh.getvalue())

def upload_many(drive_folder_id: str, local_folder_path: Path, drive_service):
    # Iterate over files in the folder
    for file_path in local_folder_path.rglob('*'):
        # Skip directories and .gitkeep file
        if file_path.is_dir() or file_path.name == '.gitkeep':
            continue

        # Define file metadata and upload
        file_metadata = {
            'name': file_path.name,
            'parents': [drive_folder_id]
        }

        media = MediaFileUpload(str(file_path), resumable=True)

        try:
            drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        except ssl.SSLEOFError as e:
            try:
                drive_service.files().delete(fileId=drive_folder_id).execute()
                raise ValueError('API limits were exceeded, folder successfully deleted.')
            except ssl.SSLEOFError as e:
                raise ValueError('API limits were exceeded, but folder was not deleted.')


        time.sleep(.5)
