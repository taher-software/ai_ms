import logging
import tempfile

from src.config import Config

from src.models.video import Video

from src.integration_downloads.g_drive_download_handler import GdriveDownloadHandler
from src.integration_downloads.s3_download_handler import S3DownloadHandler
from src.integration_downloads.youtube_download_handler import YoutubeDownloadHandler
from src.integration_downloads.frameio_download_handler import FrameioDownloadHandler
from src.integration_downloads.video_resource_handler import VideoResourceHandler
from src.integration_downloads.dropbox_download_handler import DropboxDownloadHandler
from src.integration_downloads.vimeo_download_handler import VimeoDownloadHandler

# from src.integration_downloads.uploads.calculate_bitrate_handler import CalculateBitrateHandler
# from src.integration_downloads.uploads.calculate_mp3_duration_handler import CalculateMp3DurationHandler
# from src.integration_downloads.uploads.calculate_mp4_duration_handler import CalculateMp4DurationHandler
# from src.integration_downloads.uploads.calculate_mov_duration_handler import CalculateMOVDurationHandler
# from src.integration_downloads.uploads.calculate_m4v_duration_handler import CalculateM4VDurationHandler
# from src.integration_downloads.uploads.copy_working_dir_to_upload_dir_handler import CopyWorkingDirToUploadDirHandler
# from src.integration_downloads.uploads.generate_mp3_gif_handler import GenerateMp3GifHandler
# from src.integration_downloads.uploads.generate_mp3_thumbnail_handler import GenerateMp3ThumbnailHandler
# from src.integration_downloads.uploads.generate_mp4_gif_handler import GenerateMp4GifHandler
# from src.integration_downloads.uploads.generate_mov_gif_handler import GenerateMOVGifHandler
# from src.integration_downloads.uploads.generate_m4v_gif_handler import GenerateM4VGifHandler
# from src.integration_downloads.uploads.generate_mp4_thumbnail_handler import GenerateMp4ThumbnailHandler
# from src.integration_downloads.uploads.generate_mov_thumbnail_handler import GenerateMOVThumbnailHandler
# from src.integration_downloads.uploads.generate_m4v_thumbnail_handler import GenerateM4VThumbnailHandler
# from src.integration_downloads.uploads.persist_handler import PersistHandler
# from src.integration_downloads.uploads.process_handler import ProcessHandler
# from src.integration_downloads.uploads.process_track_and_broadcast_handler import ProcessTrackAndBroadCastHandler
# from src.integration_downloads.uploads.size_limit_handler import SizeLimitHandler
# from src.integration_downloads.uploads.storage_limit_handler import StorageLimitHandler
# from src.integration_downloads.uploads.storage_once_limit_handler import StorageOnceLimitHandler
# from src.integration_downloads.uploads.transcription_limit_handler import TranscriptionLimitHandler
# from src.integration_downloads.uploads.transcription_monthly_limit_handler import TranscriptionMonthlyLimitHandler

class Downloader:

    handlers = [
        S3DownloadHandler,
        YoutubeDownloadHandler,
        FrameioDownloadHandler,    
        GdriveDownloadHandler,
        DropboxDownloadHandler,
        VimeoDownloadHandler,    
        # CalculateMp3DurationHandler,
        # CalculateMp4DurationHandler,
        # CalculateMOVDurationHandler,      
        # CalculateM4VDurationHandler,                  
        # GenerateMp3GifHandler,
        # GenerateMp4GifHandler,
        # GenerateMOVGifHandler, 
        # GenerateM4VGifHandler,                       
        # GenerateMp3ThumbnailHandler,
        # GenerateMp4ThumbnailHandler,
        # GenerateMOVThumbnailHandler,  
        # GenerateM4VThumbnailHandler,  
        # SizeLimitHandler,
        # StorageLimitHandler,
        # StorageOnceLimitHandler,
        # TranscriptionLimitHandler,
        # TranscriptionMonthlyLimitHandler,
        VideoResourceHandler,
        # CalculateBitrateHandler,
        # CopyWorkingDirToUploadDirHandler,
        # PersistHandler,
        # ProcessHandler,
        # ProcessTrackAndBroadCastHandler
    ]

    def download(video_id, context):
        logging.info('Starting upload process')

        video = Video().query.get(video_id)
        with tempfile.TemporaryDirectory(prefix=f"{Config.FILESYSTEM_ROOT_DIR}/temp_") as tmp_dir:
            context['working_dir'] = tmp_dir
            context['video'] = video
            for handler_class in Downloader.handlers:
                logging.info(f"handler {str(handler_class)}")
                print(f"handler {str(handler_class)}")
                handler_class().process(context)
        logging.info('Finished upload process')
        return
