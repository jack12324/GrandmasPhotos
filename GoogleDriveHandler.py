import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from UploadHandler import UploadHandler


class GoogleDriveHandler(UploadHandler):
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/drive']
    FOLDER = 'Grandmas Photos'

    #Uploads a single image to drive. the upload location will be the app folder path FOLDER plus
    # any path of the original file following the Tif directory. ie. file C:test/foo/Jpg/bar/photo.jpg
    # will be uploaded to FOLDER/bar/photo.jpg on google drive.
    # this function will create any folders it needs along the path
    def upload_image(self, file: str) -> None:
        """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """
        creds = self.__authenticate()
        (folder_path, file_name) = os.path.split(file)
        if "Tif\\" in folder_path:
            file_path = folder_path.split("Jpg/")[1]
        else:
            file_path = ""
        full_path = os.path.join(self.FOLDER, file_path)
        print(full_path, file_name)
        try:
            # create drive api client
            service = build('drive', 'v3', credentials=creds)
            parent_folder = self.create_or_get_folder_path(service, full_path)

            file_metadata = {
                'name': file_name,
                'parents': [parent_folder]
            }
            media = MediaFileUpload(file, mimetype='image/jpg',
                                    resumable=True)
            # pylint: disable=maybe-no-member
            file = service.files().create(body=file_metadata, media_body=media,
                                          fields='id').execute()
            print(F'File with ID: "{file.get("id")}" has been uploaded.')

        except HttpError as error:
            print(F'An error occurred: {error}')
            return None

    def create_or_get_folder_path(self, service, folder):
        parent_folder = service.files().get(fileId='root').execute()['id']
        folders = folder.strip("\\").split("\\")
        print(folders)
        while len(folders) > 0:
            print(parent_folder)
            parent_folder = self.create_or_get_folder(service, folders.pop(0), parent_folder)
        return parent_folder

    def create_or_get_folder(self, service, folder, parent_folder):
        folder_id = self.get_folder(service, folder, parent_folder)
        if folder_id is None:
            return self.create_folder(service, folder, parent_folder)
        else:
            return folder_id


    # Given a folder path, creates the folder
    # Returns the id of the created folder
    def create_folder(self, service, folder: str, parent_folder: str) -> str:
        file_metadata = {
            'name': folder,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder]
        }

        # pylint: disable=maybe-no-member
        file = service.files().create(body=file_metadata, fields='id'
                                      ).execute()
        print(F'Created Folder: "{folder}"Folder ID: "{file.get("id")}".')

        return file.get('id')

    #Takes a path to a folder, returns the id of the folder if it exists, None if it doesn't
    def get_folder(self, service, folder: str, parent_folder: str = None) -> str:

        query = "mimeType='application/vnd.google-apps.folder' and '{}' in parents and name = '{}' and trashed = false".format(parent_folder, folder)
        page_token = None
        while True:
            # pylint: disable=maybe-no-member
            response = service.files().list(q=query,
                                            spaces='drive',
                                            fields='nextPageToken, '
                                                   'files(id, name, parents)',
                                            pageToken=page_token).execute()
            files = response.get('files', [])
            if len(files) > 0:
                print(F'Found file: {files[0].get("name")}, {files[0].get("id")}, {files[0].get("parents")}')
                return files[0].get("id")
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return None



    def __authenticate(self) -> Credentials:
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return creds
