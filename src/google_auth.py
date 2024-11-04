from pathlib import Path
from typing import List

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


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