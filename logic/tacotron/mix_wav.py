# -*- coding: utf-8 -*-
import os
import wave
import numpy as np
import pyaudio
import argparse
import logging

'''
How to use
python concat_wav.py --speech \
../tacotron/tacotron_output/logs-eval/wavs/eval_batch_000.wav \
--bgm ./bgm.wav --output ./output.wav

if speech or bgm is mp3 file, use ffmpeg convert to wav. For example
ffmpeg -i bgm.mp3 -ar 16000 -ac 1 bgm.wav
'''

def mix_wav(wav1_wave_data, wav2_path, snr=-10):
  wav2_bin = wave.open(wav2_path, 'rb')
  
  # 音频wav的数据
  nframes1 = len(wav1_wave_data)

  # 音频bgm的数据
  wav2_params = wav2_bin.getparams()
  nchannels2, sampwidth2, framerate2, nframes2, comptype2, compname2 = wav2_params[:6]
  logging.info("bgm channel:{} sample width:{} frame rate:{} frames:{} comtype:{} "
        "compname:{}".format(nchannels2, sampwidth2, framerate2, nframes2,
        comptype2, compname2)
       )
  wav2_str_data = wav2_bin.readframes(nframes2)
  wav2_bin.close()
  wav2_wave_data = np.fromstring(wav2_str_data, dtype=np.int16)
 
  # 对不同长度的音频用数据零对齐补位
  length = abs(nframes2 - nframes1)
  temp_array = np.zeros(length, dtype=np.int16)
  if nframes1 < nframes2:
    wav1 = wav1_wave_data
    wav2 = wav2_wave_data[:nframes1]
  elif nframes1 > nframes2:
    wav1 = wav1_wave_data
    wav2 = np.concatenate((wav2_wave_data, temp_array))
  else:
    wav1 = wav1_wave_data
    wav2 = wav2_wave_data

  new_wave_data = wav1 + (wav2*(10**(snr/20))).astype(np.int16)
  return new_wave_data

def mix_wav_v2(wav1_path, wav2_path, output_path, snr=-10):
  wav1_bin = wave.open(wav1_path, 'rb')
  wav2_bin = wave.open(wav2_path, 'rb')
 
  # 音频wav1的数据
  wav1_params = wav1_bin.getparams()
  nchannels1, sampwidth1, framerate1, nframes1, comptype1, compname1 = wav1_params[:6]
  logging.info(nchannels1, sampwidth1, framerate1, nframes1, comptype1, compname1)
  wav1_str_data = wav1_bin.readframes(nframes1)
  wav1_bin.close()
  wav1_wave_data = np.fromstring(wav1_str_data, dtype=np.int16)
  
  # 音频bgm的数据
  wav2_params = wav2_bin.getparams()
  nchannels2, sampwidth2, framerate2, nframes2, comptype2, compname2 = wav2_params[:6]
  logging.info(nchannels2, sampwidth2, framerate2, nframes2, comptype2, compname2)
  wav2_str_data = wav2_bin.readframes(nframes2)
  wav2_bin.close()
  wav2_wave_data = np.fromstring(wav2_str_data, dtype=np.int16)
 
  # 对不同长度的音频用数据零对齐补位
  length = abs(nframes2 - nframes1)
  temp_array = np.zeros(length, dtype=np.int16)
  if nframes1 < nframes2:
    wav1 = wav1_wave_data
    wav2 = wav2_wave_data[:nframes1]
  elif nframes1 > nframes2:
    wav1 = wav1_wave_data
    wav2 = np.concatenate((wav2_wave_data, temp_array))
  else:
    wav1 = wav1_wave_data
    wav2 = wav2_wave_data

  # ================================
  # 合并1和2的数据
  new_wave_data = wav1 + (wav2*(10**(snr/20))).astype(np.int16)
  new_wave = new_wave_data.tostring()
  record(new_wave, output_path)

def record(re_frames, WAVE_OUTPUT_FILENAME):
  p = pyaudio.PyAudio()
  CHANNELS = 1
  FORMAT = pyaudio.paInt16
  RATE = 16000
  logging.info("开始录音")
  wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
  wf.setnchannels(CHANNELS)
  wf.setsampwidth(p.get_sample_size(FORMAT))
  wf.setframerate(RATE)
  wf.writeframes(re_frames)
  wf.close()
  logging.info("关闭录音")

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--speech', default='', help='Path to the speech wav path')
  parser.add_argument('--bgm', default='', help='Path to the background wav path')
  parser.add_argument('--output', default='', help='Path to output wav')
  args = parser.parse_args()
  speech_path = os.path.normpath(args.speech)
  bgm_path = os.path.normpath(args.bgm)
  output_path = os.path.normpath(args.output)
  assert os.path.exists(speech_path)
  assert os.path.exists(bgm_path)
  assert os.path.normpath(args.output)
  if os.path.exists(output_path):
    logging.info('output path({}) is exists. replace it.'.format(args.output))
  mix_wav_v2(speech_path, bgm_path, output_path)

if __name__ == '__main__':
  main()

