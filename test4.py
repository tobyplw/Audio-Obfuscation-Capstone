from faster_whisper import WhisperModel
import sys
import pyaudio
import struct
import pyttsx3
from threading import Thread, Lock
import time
import os
import wave


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000



def record_chunk(p, stream, file_path, chunk_length =.2):
    frames = []

    for _ in range(0, int(RATE / CHUNK * chunk_length)):
        data = stream.read(CHUNK, exception_on_overflow = False)
        frames.append(data)

    wf = wave.open(file_path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(16000)
    wf.writeframes(b''.join(frames))
    wf.close()


def transcribe_chunk(model, file_path):
    segments, info = model.transcribe(file_path, beam_size = 7)
    transcription = ' '.join(segment.text for segment in segments)
    return transcription

def main2():

    audio = pyaudio.PyAudio()
    print("----------------------record device list---------------------")
    info = audio.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
        if (audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            print("Input Device id ", i, " - ", audio.get_device_info_by_host_api_device_index(0, i).get('name'))

    print("-------------------------------------------------------------")
    print("Input Audio Device Index: ")
    index = int(input())
    print("recording via index "+str(index))

    model_size = "large-v3"
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print("HERE")
    
    stream = audio.open(format = FORMAT, channels=CHANNELS, rate=RATE, input=True, input_device_index = index, frames_per_buffer=CHUNK)

    try:
        while True:
            chunk_file = "temp_chunk.wav"
            record_chunk(audio, stream, chunk_file)

            transcription = transcribe_chunk(model, chunk_file)
            sys.stdout.write(transcription)
            sys.stdout.flush()

            #os.remove(chunk_file)
    except KeyboardInterrupt:
        print("Stopping")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()


if __name__ == "__main__":
    main2()