import json
import logging
import math
import boto3
import os
from werkzeug.utils import secure_filename
from src.models.enums.integration_status import IntegrationStatus

from src.orm import db
from src.path import join_paths
from src.utils import get_user_by_id
from src.integration_downloads.handler import Handler

from flask_sse import sse

from src.enums.integration_type import IntegrationType


class S3DownloadHandler(Handler):

    def __init__(self):
        super().__init__()
        self._progress = 0
        self._previous_completed = 0
        self._channel = None
        self._video_id = None
        from src.main import app
        self._app = app

    def _handle(self, context):
        self.context = context
        s3_config = self._get_context_value(context, 's3', require=False)
        self._channel = self._get_context_value(
            context, 'package_owner_user_id')
        video = self._get_context_value(context, 'video')
        self._video_id = video.id

        if not (s3_config
                and 'access_key' in s3_config
                and 'secret_key' in s3_config
                and 'bucket_name' in s3_config and 'bucket_file' in s3_config):
            return

        access_key = s3_config.get('access_key')
        secret_key = s3_config.get('secret_key')
        bucket_name = s3_config.get('bucket_name')
        bucket_file = s3_config.get('bucket_file')
        working_dir = self._get_context_value(context, 'working_dir')
        filename = bucket_file.split("/")[-1]
        video_path = join_paths(working_dir, secure_filename(filename))
        os.makedirs(os.path.dirname(video_path), exist_ok=True)

        s3_client = boto3.client(
            's3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        response = s3_client.head_object(Bucket=bucket_name, Key=bucket_file)
        total_size = response['ContentLength'] * 1.1

        timestamp = self._get_context_value(context, 'timestamp')
        user_email = get_user_by_id(
            self._get_context_value(context, 'user_id')).email
        
        video.integration_status = IntegrationStatus.DOWNLOADING.value
        db.session.commit()
        video.id = self._video_id
        self._set_context_value(context, 'video', video)
        ts = self._get_context_value(self.context, 'timestamp')
        message = {"id": self._video_id, "ts": ts}

        with self._app.app_context():
            sse.publish(data=json.dumps(message), type='fetch_video',
                        id=ts, channel=self._channel)

        def callback(bytes_transferred):
            self.s3_download_progress_callback(
                user_email, timestamp, bytes_transferred, total_size)

        # Download the file directly to disk with the progress callback
        with open(video_path, 'wb') as f:
            s3_client.download_fileobj(
                bucket_name, bucket_file, f, Callback=callback)

        video.file_name = bucket_file
        title, extension = os.path.splitext(filename)
        video.title = title
        video.integration_status = IntegrationStatus.COMPLETE.value
        self._set_context_value(context, 'video_path', video_path)
        self._set_context_value(context, 'video', video)

    def s3_download_progress_callback(self, user_email, timestamp, bytes_transferred, total_size):
        self._progress += bytes_transferred
        pct_completed = (self._progress / total_size) * 100

        if self.should_report(self._previous_completed, pct_completed):
            try:
                message = json.dumps(
                    {"email": user_email, "id": self._video_id, "type": IntegrationType.AWS.value, "ts": timestamp, "completed": math.floor(pct_completed)}, default=str)
                with self._app.app_context():
                    sse.publish(data=message, type='third_party_download',
                                id=timestamp, channel=self._channel)
            except Exception as err:
                logging.error('Third party download broadcast failed: ' + str(err))
        self._previous_completed = pct_completed
        return

    def should_report(self, last_reported, progress):
        return math.floor(progress) > math.floor(last_reported)
