import os
import logging
import time
import yaml
from sys import path as sys_path
import torch
import numpy as np
from scipy.signal import resample
import librosa
dir_path = os.path.split(os.path.realpath(__file__))[0]
sys_path.append(dir_path)

from text import text_to_sequence

from frontend.text_analyze import TextAnalysis
import gen_audio
from utils.tools import get_mask_from_lengths, pad
dir_path = os.path.join(os.path.split(os.path.realpath(__file__))[0], 'vocoder')
sys_path.append(dir_path)

sampling_rate = 22050
MAX_WAV_VALUE = 32768.0
SILENCE_LEN = 3000

text_analysis = TextAnalysis(user_dict=os.path.realpath('./logic/tacotron/frontend/extra_data/cut_dict.txt'))


def load_model(tacotron_checkpoint, vocoder_checkpoint_path):
    # tacotron
    acoustic_model = torch.load(tacotron_checkpoint, map_location=torch.device('cpu'))

    # vocoder
    vocoder_model = torch.load(vocoder_checkpoint_path, map_location=torch.device('cpu'))

    # print('model', model)
    # print('vocoder', vocoder)
    torch.set_num_threads(1)
    return acoustic_model, vocoder_model, None, None


def convert(acoustic_model, vocoder_model, pqmf, denoiser, text, text_path=None, 
            pitch_control = 1.0, energy_control = 1.0, duration_control = 1.0):
    rate = 16000/sampling_rate
    sentences = text_analysis.stream_text_to_pinyin(text=text)
    speaker = 0

    acc_acoustic = 0.0
    acc_vocoder= 0.0
    audio_output = np.array([]).astype('int16')
    for i, t in enumerate(sentences):
        check_begin = time.time()
        sequence = np.array(text_to_sequence(t, ['basic_cleaners']))[None, :]
        sequence = [torch.LongTensor([speaker]), torch.autograd.Variable(torch.from_numpy(sequence)).long(), torch.LongTensor([len(sequence[0])]), len(sequence[0])]
        sequence = [i_seq.cuda() if torch.cuda.is_available() else i_seq for i_seq in sequence]

        with torch.no_grad():
            for idx, output in enumerate(acoustic_model(*sequence,
                                                        p_control=pitch_control,
                                                        e_control=energy_control,
                                                        d_control=duration_control)):
                check_mid = time.time()
                acc_acoustic += check_mid - check_begin
                output[1][0,:,30:40] += 0.2
                output[1][0,:,40:65] += 0.4
                output[1][0,:,65:75] += 0.2

                audio = vocoder_model(output[1].transpose(1, 2))
                audio = audio.squeeze()
                audio = audio.cpu().numpy()
                audio = gen_audio.audio_process(idx, audio)
                audio, _ = librosa.effects.trim(audio, top_db=43, frame_length=2048, hop_length=300)
                audio = resample(audio, np.int32(audio.shape[0]*rate))
                if idx == 0:
                    audio = gen_audio.audio_edge(audio, True)
                audio = np.clip((audio*(MAX_WAV_VALUE-1)*2.1), -MAX_WAV_VALUE, MAX_WAV_VALUE-1)
                audio_output = np.concatenate((audio_output, audio))

                check_end = check_begin = time.time()
                acc_vocoder += check_end - check_mid

        sil_data = np.array([0]*SILENCE_LEN)
        # audio_output = gen_audio.audio_edge(audio_output, False)
        audio_output = np.concatenate((audio_output, sil_data))

    logging.info("total acoustic time:{} total vocoder time:{}".format(acc_acoustic, acc_vocoder))
    return audio_output.astype(np.int16)


def stream_convert(acoustic_model, vocoder_model, pqmf, denoiser, text, text_path=None, 
                   pitch_control = 1.0, energy_control = 1.0, duration_control = 1.0):
    rate = 16000/sampling_rate
    sentences = text_analysis.stream_text_to_pinyin(text=text)
    speaker = 0

    acc_acoustic = 0.0
    acc_vocoder= 0.0
    for i, t in enumerate(sentences):
        check_begin = time.time()
        sequence = np.array(text_to_sequence(t, ['basic_cleaners']))[None, :]
        sequence = [torch.LongTensor([speaker]), torch.autograd.Variable(torch.from_numpy(sequence)).long(), torch.LongTensor([len(sequence[0])]), len(sequence[0])]
        sequence = [i_seq.cuda() if torch.cuda.is_available() else i_seq for i_seq in sequence]

        with torch.no_grad():
            for idx, output in enumerate(acoustic_model(*sequence,
                                                        p_control=pitch_control,
                                                        e_control=energy_control,
                                                        d_control=duration_control)):
                check_mid = time.time()
                acc_acoustic += check_mid - check_begin
                output[1][0,:,30:40] += 0.2
                output[1][0,:,40:65] += 0.4
                output[1][0,:,65:75] += 0.2

                audio = vocoder_model(output[1].transpose(1, 2))
                audio = audio.squeeze()
                audio = audio.cpu().numpy()
                audio = gen_audio.audio_process(idx, audio)
                audio, _ = librosa.effects.trim(audio, top_db=43, frame_length=2048, hop_length=300)
                audio = resample(audio, np.int32(audio.shape[0]*rate))
                if idx == 0:
                    audio = gen_audio.audio_edge(audio, True)
                audio = np.clip((audio*(MAX_WAV_VALUE-1)*2.1), -MAX_WAV_VALUE, MAX_WAV_VALUE-1)
                yield audio.astype(np.int16)

                check_end = check_begin = time.time()
                acc_vocoder += check_end - check_mid

        sil_data = np.array([0]*SILENCE_LEN)
        # audio = gen_audio.audio_edge(audio, False)
        yield sil_data.astype(np.int16)

    logging.info("total acoustic time:{} total vocoder time:{}".format(acc_acoustic, acc_vocoder))


def write(wav, wav_path):
    from scipy.io import wavfile
    wavfile.write(wav_path, 16000, wav)


def get_sample_rate():
    _sample_rate = sampling_rate
    return _sample_rate
