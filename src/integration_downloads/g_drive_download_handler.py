import json
import logging
import math
import os
from werkzeug.utils import secure_filename

from src.models.enums.google_scopes import GoogleScopes
from src.models.enums.integration_status import IntegrationStatus
from src.models.enums.integration_type import IntegrationType
from src.orm import db
from src.path import join_paths
from src.utils import get_user_by_id
from src.integration_downloads.handler import Handler
from src.orm import session
from src.models.gdrive import GDrive
from src.utils import auth2_token
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from werkzeug.exceptions import NotFound
import io

from flask_sse import sse
import shutil


class GdriveDownloadHandler(Handler):

    def __init__(self):
        super().__init__()
        self._progress = 0
        self._previous_completed = 0
        self._channel = None
        self._video_id = None
        from src.main import app
        self._app = app

    def _handle(self, context):
        gdrive_data = self._get_context_value(context, 'gdrive', require=False)
        self._channel = self._get_context_value(
            context, 'package_owner_user_id')
        video = self._get_context_value(context, 'video')
        self._video_id = video.id

        if not (gdrive_data
                and 'gdrive_account_id' in gdrive_data
                and 'file_id' in gdrive_data):
            return

        gdrive_account_id = gdrive_data.get('gdrive_account_id')
        file_id = gdrive_data.get('file_id')
        filename = gdrive_data.get('file_name')

        # get gdrive account
        gdrive_account = session.query(GDrive).get(gdrive_account_id)
        # retrieve the filename of the video

        working_dir = self._get_context_value(context, 'working_dir')

        video_path = join_paths(working_dir, secure_filename(filename))
        os.makedirs(os.path.dirname(video_path), exist_ok=True)

        # get user credentials
        credentials = self.get_credentials(
            access_token=gdrive_account.access_token, refresh_token=gdrive_account.refresh_token)
        drive_service = build('drive', 'v3', credentials=credentials)

        timestamp = self._get_context_value(context, 'timestamp')
        #user_service = UserService()
        user_email = get_user_by_id(
            self._get_context_value(context, 'user_id')).email

        video.integration_status = IntegrationStatus.DOWNLOADING.value
        db.session.commit()
        video.id = self._video_id
        self._set_context_value(context, 'video', video)
        ts = self._get_context_value(context, 'timestamp')
        message = {"id": self._video_id, "ts": ts}
        with self._app.app_context():
            sse.publish(data=json.dumps(message), type='fetch_video',
                        id=ts, channel=self._channel)

        # Download the video
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.FileIO(video_path, mode='wb')
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while done is False:
            try:
                status, done = downloader.next_chunk()
                self.gdrive_progress_callback(
                    user_email, timestamp, int(status.progress() * 100))
            except Exception as err:
                print('Error downloading', err)

        timestamp = self._get_context_value(context, 'timestamp')
        #user_service = UserService()
        user_email = get_user_by_id(
            self._get_context_value(context, 'user_id')).email

        video = self._get_context_value(context, 'video')
        video.file_name = filename

        title, _ = os.path.splitext(filename)

        video.title = title
        video.integration_status = IntegrationStatus.COMPLETE.value
        self._set_context_value(context, 'video_path', video_path)
        self._set_context_value(context, 'video', video)

    @auth2_token([GoogleScopes.GDRIVE.value],provider='gdrive')
    def get_credentials(self, **kwargs):
        return kwargs.get('credentials')

    def gdrive_progress_callback(self, user_email, timestamp, progress):
        from src.main import app
        try:
            message = json.dumps(
                {"email": user_email, "id": self._video_id, "type": IntegrationType.GDRIVE.value, "ts": timestamp, "completed": math.floor(progress)}, default=str)
            with app.app_context():
                sse.publish(data=message, type='third_party_download',
                            id=timestamp, channel=self._channel)
        except Exception as err:
            logging.error('Third party download broadcast failed: ' + str(err))
