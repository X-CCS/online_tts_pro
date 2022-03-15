import os
import sys
import logging
from scipy.io import wavfile


APP_ROOT = os.path.realpath(__file__).rsplit('/', 2)[0]
from logic.tacotron.main_server import load_model, convert, stream_convert, write

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

SYNTHESIS_NAME = 'synthesis'
UPLOAD_NAME = 'upload'
TACOTRON_CHECKPOINT = os.path.join(APP_ROOT, 'logic', 'tacotron', 'tacotron_model')
VOCODER_CHECKPOINT = os.path.join(APP_ROOT, 'logic', 'tacotron', 'vocoder', 'vocoder_model.pt')
SYNTHESIS_DIR = os.path.join(APP_ROOT, 'logic', 'media', SYNTHESIS_NAME)
BACKGROUND_MUSIC = os.path.join(APP_ROOT, 'logic', 'static', 'bgm', '001.wav')
UPLOAD_DIR = os.path.join(APP_ROOT, 'logic', 'media', UPLOAD_NAME)
MAIN_PAGE = os.path.join(APP_ROOT, 'logic', 'templates', 'tts_index.html')


class TTSManager:
    def __init__(self, tacotron_checkpoint, vocoder_checkpoint,
                 output_dir, bgm_path, upload_dir):
        self.tacotron_checkpoint = tacotron_checkpoint
        self.vocoder_checkpoint = vocoder_checkpoint
        self.output_dir = output_dir
        self.bgm_path = bgm_path
        self.upload_dir = upload_dir
        self.tacotron_model = None
        self.vocoder_model = None
        self.pqmf = None

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.upload_dir, exist_ok=True)

        self.tacotron_model, self.vocoder_model, self.pqmf, self.denoiser = load_model(
            self.tacotron_checkpoint, self.vocoder_checkpoint)

    def load(self, tacotron_checkpoint=TACOTRON_CHECKPOINT,
             vocoder_checkpoint=VOCODER_CHECKPOINT):
        self.tacotron_model, self.vocoder_model, self.pqmf, self.denoiser = load_model(
            tacotron_checkpoint, vocoder_checkpoint)

    def transfer(self, text):
        data = convert(self.tacotron_model, self.vocoder_model, self.pqmf, self.denoiser, text)
        return data

    def stream_transfer(self, text):
        for data in stream_convert(self.tacotron_model,
                                   self.vocoder_model, self.pqmf, self.denoiser, text):
            yield data

    def write(self, wav, wav_name):
        write(wav, os.path.join(self.output_dir, wav_name))
        logging.info("语音合成完成，合成文件放在：".format(os.path.join(self.output_dir, wav_name)))


managerInst = TTSManager(TACOTRON_CHECKPOINT, VOCODER_CHECKPOINT,
                         SYNTHESIS_DIR, BACKGROUND_MUSIC, UPLOAD_DIR)
