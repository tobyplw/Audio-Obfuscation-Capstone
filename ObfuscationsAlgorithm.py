import sys
import sounddevice as sd
import argparse
import wave
import numpy
import librosa
from soundfile import SoundFile

import queue


input_queue = queue.Queue()


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

'''
class AudioOutput:
    def __init__(self, filename = None):
        if filename == None:
            filename = 'sound.wav'
        self.filename = filename
        self.record_file = wave.open(filename,'wb')

    def record_to_file(self, record_file, data):
        self.record_file
'''

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    input_queue.put(indata)      


def obfuscateAudio(data, samplerate):

    #data = librosa.effects.pitch_shift(data, sr=samplerate, n_steps=3)

    return data


""" Main program """
# Code goes over here.
'''
parser = argparse.ArgumentParser(add_help=False)
args, remaining = parser.parse_known_args()
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    "-f", "--filename", type=str, metavar="FILENAME",
    help="audio file to store recording to")
parser.add_argument(
    "-d", "--device", type=int_or_str,
    help="input device (numeric ID or substring)")
parser.add_argument(
    "-r", "--samplerate", type=int, help="sampling rate")
'''





try:
    print("\n Audio Devices Found:")
    print(sd.query_devices())
    print("\n Please Select Input Audio Device:")
    device_input_index = int(input())
    device_info = sd.query_devices(device_input_index, "input")
    print("\n Using System Input Device: " + str(device_info) + "\n\n")
    samplerate = int(device_info["default_samplerate"])

    '''
    record_file = wave.open('sound.wav','wb')
    record_file.setnchannels(1)
    record_file.setsampwidth(2)
    record_file.setframerate(samplerate)
    '''
    record_file = SoundFile('sound.wav')


    with sd.InputStream(samplerate=samplerate, blocksize = 0, device=device_input_index,
            dtype="float32", channels=1, callback=callback):
        with SoundFile('sound.wav', mode ='w+', samplerate = samplerate, channels = 1) as f:

            print("#" * 80)
            print("Press Ctrl+C to stop recording")
            print("#" * 80)


            while True:
                data = input_queue.get()
                data= obfuscateAudio(data, samplerate)
                #print(data)
                #record_file.writeframesraw(data.tobytes())
                #sf.write('sound.wav', data, samplerate)
                f.write(data)

except KeyboardInterrupt:
    print("\nDone")
    record_file.close()
    
    #parser.exit(0)


