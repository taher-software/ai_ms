import os

from src.models.processor import Processor
from src.path import join_paths
from src.integration_downloads.handler import Handler
from src.config import Config
from src.models.video import Video
from src.utils import save

class VideoResourceHandler(Handler):
    def __init__(self):
        self._requires_file = False

    def _handle(self, context):
        language = self._get_context_value(context, 'language')
        user_id = self._get_context_value(context, 'user_id')
        package_owner_user_id = self._get_context_value(context, 'package_owner_user_id')
        processes = self._get_context_value(context, 'processes')
        video = self._get_context_value(context, 'video')
        video_path = self._get_context_value(context, 'video_path')
        get_clips = self._get_context_value(context, 'get_clips')

        filename = os.path.basename(video_path)

        video.user_id = user_id
        video.package_owner_user_id = package_owner_user_id
        video.language = language.value

        #video_dao = CrudDao(Video)
        save(video, flush=True)

        folder = video.id

        precompute_faces_path = join_paths(os.path.sep, user_id, folder, 'faces.pkl')
        precompute_cast_path = join_paths(os.path.sep, user_id, folder, 'cast.pkl')        
        precompute_audio_path = join_paths(os.path.sep, user_id, folder, 'precompute_audio.npy')
        metadata_path = join_paths(os.path.sep, user_id, folder, 'metadata.json')   
        visual_metadata_path = join_paths(os.path.sep, user_id, folder, 'visual_metadata.json')                     
        precompute_vid_path = join_paths(os.path.sep, user_id, folder, 'precompute_vid.npy')
        precompute_shots_path = join_paths(os.path.sep, user_id, folder, 'precompute_shots.pkl')
        precompute_sub_path = join_paths(os.path.sep, user_id, folder, 'precompute_sub.npy')
        subtitles_path = join_paths(os.path.sep, user_id, folder, 'subtitles')
        transcript_path = join_paths(os.path.sep, user_id, folder, 'transcript')
        audio_path = join_paths(os.path.sep, user_id, folder, 'audio.wav')
        timestamps_path = join_paths(os.path.sep, user_id, folder, 'timestamps.json')
        gif_path = join_paths(os.path.sep, user_id, folder, 'gif.gif')
        srt_trans_path = join_paths(os.path.sep, user_id, folder, 'subtitles_translated')
        temp_folder = join_paths(os.path.sep, user_id, folder, 'temp')
        txt_path = join_paths(os.path.sep, user_id, folder, 'txts.txt')
        summary_path = join_paths(os.path.sep, user_id, folder, 'summaries.txt')
        speaker_ts_path = join_paths(os.path.sep, user_id, folder, 'spts.txt')
        speakers_path = join_paths(os.path.sep, user_id, folder, 'speakers.pkl')
        thumbnails_base_path = join_paths(os.path.sep, user_id, folder, '_thumbnails')
        topics_path = join_paths(os.path.sep, user_id, folder, 'topics.json')
        chapters_path = join_paths(os.path.sep, user_id, folder, 'chapters.json')        
        tracked_faces_path = join_paths(os.path.sep, user_id, folder, 'faces_tracking.pkl')

        video.precomp_audio_path = precompute_audio_path
        video.metadata_path = metadata_path    
        video.visual_metadata_path = visual_metadata_path                    
        video.precomp_faces_path = precompute_faces_path
        video.precomp_cast_path = precompute_cast_path
        video.precomp_vid_path = precompute_vid_path
        video.precomp_shots_path = precompute_shots_path
        video.precomp_sub_path = precompute_sub_path
        video.srt_folder = subtitles_path
        video.txt_folder = transcript_path
        video.audio_path = audio_path
        video.timestamps_path = timestamps_path
        video.base_path = Config.FILESYSTEM_ROOT_UPLOAD_DIR
        video.gif_path = gif_path
        video.srt_trans_path = srt_trans_path
        video.temp_folder = temp_folder
        video.txt_path = txt_path
        video.summary_path = summary_path
        video.speaker_ts_path = speaker_ts_path
        video.speakers_path = speakers_path
        video.thumbnails_base_path = thumbnails_base_path
        video.topics_path = topics_path
        video.chapters_path = chapters_path        
        video.tracked_faces_path = tracked_faces_path
        video.get_clips = get_clips

        video.file_name = filename
        video.file_size = os.stat(video_path).st_size / 1000 ** 3
        video.path = join_paths(os.path.sep, user_id, folder, filename)

        video.video_thumb = join_paths(user_id, folder, 'thumb.jpg')
        video.processed_au = int(Processor.Audio.value not in processes)
        video.processed_srt_gen = int(Processor.Dialog.value not in processes)
        video.processed_pc = int(Processor.Visual.value not in processes)

        title, extension = os.path.splitext(video.file_name)
        video.title = video.title or title
        video.title = str(video.title)

        if len(processes) == 3:
            video.preproc = '3'
        elif Processor.Dialog.value in processes:
            video.preproc = '1'
        elif Processor.Visual.value in processes:
            video.preproc = '2'
        else:
            video.preproc = '4'

        self._set_context_value(context, 'video', video)
