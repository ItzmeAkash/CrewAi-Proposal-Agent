import os
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import re
from crewai_tools import BaseTool
from dotenv import load_dotenv


#load enviroment variables from .env file
load_dotenv()

# Define the scopes required for accessing Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def extract_folder_id(folder_link):
    match = re.search(r'/folders/([^/?]+)', folder_link)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid Google Drive folder link.")

def extract_folder_name(service, folder_id):
    folder = service.files().get(fileId=folder_id, fields='name').execute()
    return folder.get('name')

def download_file_from_google_drive(file_id, destination):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params={'id': file_id}, stream=True)
    confirmation_token = get_confirm_token(response)
    if confirmation_token:
        params = {'id': file_id, 'confirm': confirmation_token}
        response = session.get(URL, params=params, stream=True)
    save_response_content(response, destination)

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def save_response_content(response, destination):
    CHUNK_SIZE = 32768
    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:
                f.write(chunk)

class GoogleDriveDownloaderTool(BaseTool):
    name: str = "Google Drive Downloader"
    description: str = "Downloads all files from a specified Google Drive folder."

    def _run(self, folder_link: str) -> str:
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json')

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                client_secrets = {
                    "installed": {
                        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                        "project_id": os.getenv('GOOGLE_PROJECT_ID'),
                        "auth_uri": os.getenv('GOOGLE_AUTH_URI'),
                        "token_uri": os.getenv('GOOGLE_TOKEN_URI'),
                        "auth_provider_x509_cert_url": os.getenv('GOOGLE_AUTH_PROVIDER_X509_CERT_URL'),
                        "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                        "redirect_uris": [os.getenv('GOOGLE_REDIRECT_URI')],
                        "refresh_token": os.getenv('GOOGLE_REFRESH_TOKEN')
                    }
                }
                flow = InstalledAppFlow.from_client_config(client_secrets,SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        service = build('drive', 'v3', credentials=creds)
        folder_id = extract_folder_id(folder_link)
        folder_name = extract_folder_name(service, folder_id)

        # Define the new path in the previous directory (one level up from current directory)
        # parent_directory = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))
        parent_directory = os.path.abspath(os.path.join(os.getcwd(),))
        base_destination_folder = os.path.join(parent_directory, 'downloaded')
        if not os.path.exists(base_destination_folder):
            os.makedirs(base_destination_folder)
        destination_folder = os.path.join(base_destination_folder, folder_name)
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        results = service.files().list(
            q=f"'{folder_id}' in parents",
            fields="files(id, name)"
        ).execute()

        for file in results.get('files', []):
            file_id = file.get('id')
            file_name = file.get('name')
            destination_path = os.path.join(destination_folder, file_name)
            download_file_from_google_drive(file_id, destination_path)
        
        return f"Files downloaded to {destination_folder}"

# Example usage within the CrewAI framework
# tool = GoogleDriveDownloaderTool()
# result = tool.run('https://drive.google.com/drive/folders/1Nv2u6tJKxiMMONVN16YbZtwYmokn1NnP?usp=sharing')
# print(result)
