from faster_whisper import WhisperModel

import sys
import pyaudio
import struct
import pyttsx3
from threading import Thread, Lock
import time

model_size = "large-v3"

# Run on GPU with FP16
model = WhisperModel(model_size, device="cpu", compute_type="int8")

stream = audio.open(format = FORMAT, channels=CHANNELS, rate=RATE, input=True, input_device_index = index, frames_per_buffer=CHUNK)

# or run on GPU with INT8
# model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
# or run on CPU with INT8
# model = WhisperModel(model_size, device="cpu", compute_type="int8")

segments, info = model.transcribe("audio.mp3", beam_size=5)

print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))