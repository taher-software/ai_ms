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
#from src.services.user_service import UserService
from src.integration_downloads.handler import Handler
from src.orm import session
from src.models.dropbox import Dropbox
from src.utils import get_user_by_id
from src.utils import auth2_token

from flask_sse import sse
import dropbox


class DropboxDownloadHandler(Handler):

    def __init__(self):
        super().__init__()
        self._channel = None
        self._video_id = None
        from app import app
        self._app = app

    def _handle(self, context):
        dropbox_data = self._get_context_value(context, 'dropbox', require=False)
        self._channel = self._get_context_value(
            context, 'package_owner_user_id')
        video = self._get_context_value(context, 'video')
        self._video_id = video.id

        if not (dropbox_data
                and 'dropbox_account_id' in dropbox_data
                and 'dropbox_file_id' in dropbox_data):
            return

        dropbox_account_id = dropbox_data.get('dropbox_account_id')
        file_id = dropbox_data.get('dropbox_file_id')
        filename = dropbox_data.get('dropbox_file_name')

        # get dropbox account
        dropbox_account = session.query(Dropbox).get(dropbox_account_id)
        # retrieve the filename of the video
        working_dir = self._get_context_value(context, 'working_dir')

        video_path = join_paths(working_dir, secure_filename(filename))
        os.makedirs(os.path.dirname(video_path), exist_ok=True)
        print(f'old access token: {dropbox_account.access_token}')
        # get user credentials
        access_token = self.get_credentials(
            access_token=dropbox_account.access_token, refresh_token=dropbox_account.refresh_token)

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

                
        self.download_video(file_id,video_path,access_token,user_email,timestamp)

        video = self._get_context_value(context, 'video')
        video.file_name = filename

        title, _ = os.path.splitext(filename)

        video.title = title
        video.integration_status = IntegrationStatus.COMPLETE.value
        self._set_context_value(context, 'video_path', video_path)
        self._set_context_value(context, 'video', video)

    @auth2_token(None,provider='dropbox')
    def get_credentials(self, **kwargs):
        print(f'new access token: {kwargs.get("access_token")}')
        return kwargs.get('access_token')
    
    def download_video(self,filename_id, output_file,access_token,user_email,timestamp):
        dbx = dropbox.Dropbox(access_token)
        with open(output_file, 'wb') as f:
            metadata, res = dbx.files_download(filename_id)
            total_bytes = metadata.size
            downloaded_bytes = 0
            for chunk in res.iter_content(chunk_size=4096):
                if chunk:
                    f.write(chunk)
                    downloaded_bytes += len(chunk)
                    self.progress_callback(downloaded_bytes, total_bytes,user_email,timestamp)
                    
    def progress_callback(self,current, total,user_email,timestamp):
        progress = (current/total) * 100
        from app import app 
        try:
            message = json.dumps(
                {"email": user_email, "id": self._video_id, "type": IntegrationType.GDRIVE.value, "ts": timestamp, "completed": math.floor(progress)}, default=str)
            with app.app_context():
                sse.publish(data=message, type='third_party_download',
                            id=timestamp, channel=self._channel)
        except Exception as err:
            logging.error('Third party broadcast failed: ' + str(err))

