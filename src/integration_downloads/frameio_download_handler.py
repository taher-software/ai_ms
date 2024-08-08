from flask_sse import sse
import json
import logging
import math
import os
import requests

from werkzeug.utils import secure_filename
from src.models.enums.integration_status import IntegrationStatus
from src.models.enums.integration_type import IntegrationType
from src.orm import db

from src.path import join_paths
from src.integration_downloads.handler import Handler

from flask_sse import sse
from src.utils import get_user_by_id


class FrameioDownloadHandler(Handler):

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
        frameio_config = self._get_context_value(
            context, 'frame_io', require=False)
        video = self._get_context_value(context, 'video')
        self._video_id = video.id
        self._channel = self._get_context_value(
            self.context, 'package_owner_user_id')
        user_id = self._get_context_value(self.context, 'user_id')
        self._user_email = get_user_by_id(user_id).email
        
        if not (frameio_config
                and 'frameio_asset_id' in frameio_config
                and 'frameio_dev_token' in frameio_config):
            return

        frameio_asset_id = frameio_config.get('frameio_asset_id')
        frameio_dev_token = frameio_config.get('frameio_dev_token')

        url = "https://api.frame.io/v2/assets/" + frameio_asset_id

        query = { "include_deleted": "true","type": "file"}

        headers = {"Authorization": f"Bearer {frameio_dev_token}"}

        response = requests.get(url, headers=headers, params=query)

        asset = response.json()

        asset_name = asset['name']    
        downloads = asset['downloads']    
        valid_entries = {key: value for key, value in downloads.items() if key.startswith('h264') and value is not None}
        max_resolution_key = max(valid_entries.keys(), key=lambda x: int(x.split('_')[1]))
        asset_link = valid_entries[max_resolution_key]
        asset_size = asset['transcode_statuses'][max_resolution_key]['filesize']
        asset_link_original = asset['original']
        asset_size_original = asset['filesize']
        
        working_dir = self._get_context_value(context, 'working_dir')
        video_title = asset_name.split('.mp4')[0]
        filename = secure_filename(asset_name)
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

        video_path = os.path.join(working_dir, filename)

        response = requests.get(asset_link, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        downloaded_bytes = 0  # Keep track of downloaded bytes

        with open(video_path, 'wb') as file:
            for data in response.iter_content(chunk_size=4096):
                file.write(data)
                downloaded_bytes += len(data)  # Update downloaded bytes
                # Call on_progress to broadcast progress
                self.on_progress({
                    'status': 'downloading',
                    'total_bytes': total_size,
                    'downloaded_bytes': downloaded_bytes
                })
    
        video.id = self._video_id
        video.integration_status = IntegrationStatus.COMPLETE.value

        self._set_context_value(context, 'video', video)
        self._set_context_value(context, 'video_path', video_path)

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
                            {"email": self._user_email, "type": IntegrationType.FRAMEIO.value, "id": self._video_id, "ts": timestamp, "completed": math.floor(pct_completed * 100)}, default=str)
                        with self._app.app_context():
                            sse.publish(data=message, type='third_party_download',
                                        id=timestamp, channel=self._channel)
                    except Exception as err:
                        logging.error(
                            'frame.io download progress broadcast failed', err)

                self._previous_completed = pct_completed

    def should_report(self, last_reported, progress):
        return math.floor(progress) > math.floor(last_reported)
