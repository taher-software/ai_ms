import json
import logging
import math
import os
from werkzeug.utils import secure_filename

from src.models.enums.google_scopes import GoogleScopes
from src.enums.integration_status import IntegrationStatus
from src.enums.integration_type import IntegrationType
from src.orm import db
from src.path import join_paths
#from src.services.user_service import UserService
from src.integration_downloads.handler import Handler
from src.orm import session
from src.models.vimeo import Vimeo
from src.utils import auth2_token
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from flask_sse import sse
from werkzeug.exceptions import ExpectationFailed
import requests
from src.utils import get_user_by_id


class VimeoDownloadHandler(Handler):

    def __init__(self):
        super().__init__()
        self._progress = 0
        self._previous_completed = 0
        self._channel = None
        self._video_id = None
        from src.main import app
        self._app = app

    def _handle(self, context):
        vimeo_data = self._get_context_value(context, 'vimeo', require=False)
        self._channel = self._get_context_value(
            context, 'package_owner_user_id')
        video = self._get_context_value(context, 'video')
        self._video_id = video.id
      
        if not (vimeo_data
                and 'vimeo_account_id' in vimeo_data
                and 'vimeo_file_id' in vimeo_data):
            return

        vimeo_account_id = vimeo_data.get('vimeo_account_id')
        file_id = vimeo_data.get('vimeo_file_id')
        filename = vimeo_data.get('vimeo_file_name')

        # get vimeo account
        vimeo_account = session.query(Vimeo).get(vimeo_account_id)
        # retrieve the filename of the video

        working_dir = self._get_context_value(context, 'working_dir')

        video_path = join_paths(working_dir, secure_filename(filename))
      
        os.makedirs(os.path.dirname(video_path), exist_ok=True)

        
        access_token = vimeo_account.access_token

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
            
        
        video_uri = f'https://api.vimeo.com/videos/{file_id}'
        response = requests.get(video_uri, headers={'Authorization': f'Bearer {access_token}'})
        
        
        # response = v.get(video_uri)
        if response.status_code != 200:
            raise ExpectationFailed(f"Failed to get video info: {response.json()}")
        video_data = response.json()
        
        if 'download' not in video_data:
            raise ExpectationFailed('Download information not available for this video')
        download_link = video_data['download']
        
        response = requests.head(download_link)
        total_size = int(response.headers.get('content-length', 0))
        
        response = requests.get(download_link, stream=True)

        if response.status_code == 200:
                downloaded_size = 0
                with open(video_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            progress = downloaded_size/total_size
                    
                            self.progress_callback(user_email,ts,progress)
        
        # #timestamp = self._get_context_value(context, 'timestamp')
       
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


    def progress_callback(self, user_email, timestamp, progress):
        from src.main import app
        try:
            message = json.dumps(
                {"email": user_email, "id": self._video_id, "type": IntegrationType.Vimeo.value, "ts": timestamp, "completed": math.floor(progress)}, default=str)
            with app.app_context():
                sse.publish(data=message, type='third_party_download',
                            id=timestamp, channel=self._channel)
        except Exception as err:
            logging.error('search progress broadcast failed: ' + str(err))
