from pvrecorder import PvRecorder
import pvcheetah
import sys
import pyaudio
import struct
import pyttsx3
from threading import Thread, Lock
import time


speaker = pyttsx3.init()
#speaker.startLoop(False)
#speaker.setProperty('rate', 200)  # Speed of speech (words per minute)
#speaker.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
#speaker.say("This is a test")
#speaker.runAndWait()
#speaker.startLoop()

CHUNK = 512
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

audio = pyaudio.PyAudio()

text_buffer = ""
print(len(text_buffer))

def speak_text(lock):
    
    global text_buffer
    speaker = pyttsx3.init()
    speaker.setProperty('rate', 180)
    while True:
        if(len(text_buffer) != 0):
            lock.acquire()
            words = text_buffer
            #print("\nWords = " + words + "\n")
            text_buffer = ""
            lock.release()

            try:
                speaker.endLoop()
                del speaker
                speaker = pyttsx3.init()
            except:
                pass
                speaker.startLoop()
                speaker.setProperty('rate', 190)
                speaker.say(words)


lock = Lock()
t1 = Thread(target = speak_text, args = (lock,))
t1.start()



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




key = "cZ1H05llkv2/fED0OfOT3eymL576/wHi9W9qghIAsflUH2S4SQ7i8w=="


cheetah = pvcheetah.create(access_key = key, endpoint_duration_sec = .09)
print("sample rate: " + str(cheetah.sample_rate))
print("frame length: " + str(cheetah.frame_length))

try:
    #recorder = PvRecorder(frame_length = cheetah.frame_length, device_index = 1)
    #recorder.start()
    stream = audio.open(format = FORMAT, channels=CHANNELS, rate=RATE, input=True, input_device_index = index, frames_per_buffer=CHUNK)
    print('Listening...')
    full = ""
    try:
        while True:
            #sys.stdout.flush()
            frame = stream.read(CHUNK, exception_on_overflow = False)
            result = []

            for items in struct.iter_unpack(f'<h', frame):
                result.append( items[0])

            
            partial_transcript, is_endpoint = cheetah.process(result)
            #sys.stdout.write(str(is_endpoint))
            #sys.stdout.write(partial_transcript)


            sys.stdout.flush()


            if is_endpoint:

                flush = cheetah.flush()
                lock.acquire()
                text_buffer += flush
                lock.release()
                sys.stdout.write(flush)
                sys.stdout.flush()
            
    finally:
        print()


except KeyboardInterrupt:
    pass


finally:
    cheetah.delete()
    stream.stop_stream()
    stream.close()
    audio.terminate()
    speaker.stop()

