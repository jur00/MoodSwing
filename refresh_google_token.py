from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow


scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
client_secrets_path = Path("client_secrets.json")
token_path = Path('token.json')

flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, scopes)
creds = flow.run_local_server(port=0)

with open(token_path, 'w') as token:
    token.write(creds.to_json())


# after, open token.json, and copy the text into GOOGLE_DRIVE_TOKEN here:
# https://github.com/jur00/MoodSwing/settings/secrets/actions