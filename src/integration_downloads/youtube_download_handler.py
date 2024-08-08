from flask_sse import sse
import json
import logging
import math
import os

from werkzeug.utils import secure_filename
from src.models.enums.integration_status import IntegrationStatus
from src.models.enums.integration_type import IntegrationType
from src.orm import db

from src.path import join_paths
from src.integration_downloads.handler import Handler
import yt_dlp
from flask_sse import sse
from src.utils import auth2_token
from src.models.enums.google_scopes import GoogleScopes
from src.utils import get_user_by_id


class YoutubeDownloadHandler(Handler):

    def __init__(self):
        super().__init__()
        self._previous_completed = 0
        self._channel = None
        self._user_email = None
        self._video_id = None
        from src.main import app
        self._app = app

    def _handle(self, context):
        self.context = context
        youtube_url = self._get_context_value(
            context, 'youtube_url', require=False)
        video = self._get_context_value(context, 'video')
        self._video_id = video.id
        self._channel = self._get_context_value(
            self.context, 'package_owner_user_id')
        #user_service = UserService()
        user_id = self._get_context_value(self.context, 'user_id')
        self._user_email = get_user_by_id(user_id).email

        if not youtube_url:
            return

        ydl_opts = {'age_limit': 18, 'format': 'mp4',
                    'noprogress': True, 'progress_hooks': [self.on_progress]}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            video_info = ydl.extract_info(youtube_url, download=False)
            video_title = video_info.get('title', None).decode('utf-8') if isinstance(
                video_info.get('title', None), bytes) else video_info.get('title', None)

        working_dir = self._get_context_value(context, 'working_dir')
        filename = secure_filename(video_title) + '.mp4'
        video.title = video_title
        video.file_name = filename

        video.integration_status = IntegrationStatus.DOWNLOADING.value
        db.session.commit()
        video.id = self._video_id

        ts = self._get_context_value(self.context, 'timestamp')
        message = {"id": self._video_id, "ts": ts}

        with self._app.app_context():
            sse.publish(data=json.dumps(message), type='fetch_video',
                        id=ts, channel=self._channel)

        path = os.path.join(working_dir, filename)
        ydl_opts.update({'outtmpl': path})

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        video.id = self._video_id
        video.integration_status = IntegrationStatus.COMPLETE.value

        self._set_context_value(context, 'video', video)
        self._set_context_value(context, 'video_path',
                                join_paths(working_dir, filename))

    def on_progress(self, d):
        timestamp = self._get_context_value(self.context, 'timestamp')

        """Callback function"""
        if d['status'] == 'downloading':
            total_size = d.get('total_bytes') * 1.1
            downloaded = d.get('downloaded_bytes')
            if total_size and downloaded:
                pct_completed = downloaded / total_size
                should_report = self.should_report(self._previous_completed * 100, pct_completed * 100)

                if should_report:
                    try:
                        message = json.dumps(
                            {"email": self._user_email, "type": IntegrationType.YOUTUBE.value, "id": self._video_id, "ts": timestamp, "completed": math.floor(pct_completed * 100)}, default=str)
                        with self._app.app_context():
                            sse.publish(data=message, type='third_party_download',
                                        id=timestamp, channel=self._channel)
                    except Exception as err:
                        logging.error(
                            'youtube download progress broadcast failed', err)

                self._previous_completed = pct_completed

    def should_report(self, last_reported, progress):
        return math.floor(progress) > math.floor(last_reported)
    
    @auth2_token([GoogleScopes.YOUTUBE.value],provider='youtube')
    def get_credentials(self, **kwargs):
        return kwargs.get('credentials')
