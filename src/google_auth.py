from pathlib import Path
from typing import List

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

client_secrets_path = Path("client_secrets.json")
scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def authenticate_with_oauth(client_secrets_path: Path, scopes: List):
    creds = None
    # Check if the token.json file exists
    token_path = Path('token.json')

    # Load credentials from the token file if it exists
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, scopes)

    # If there are no valid credentials, we need to log in
    if not creds or not creds.valid:
        raise ValueError('Refresh Google API token with refresh_google_token.py')

    return creds