import argparse
import queue
import sys
import sounddevice as sd
import pyttsx3
import json
from threading import Thread, Lock
from elevenlabs import set_api_key, Voice, VoiceSettings, generate, stream, play

from vosk import Model, KaldiRecognizer

q = queue.Queue()
set_api_key(api_key = "7617598e29194614ec09fe674baf47d8")
text_buffer = ""

def speak_text(lock):
    
    global text_buffer
    speaker = pyttsx3.init()
    speaker.setProperty('rate', 190)
    while True:
        if(len(text_buffer) != 0):
            lock.acquire()
            words = text_buffer
            #print("\nWords = " + words + "\n")
            text_buffer = ""
            lock.release()
            #speaker.say(words)
            #speaker.runAndWait()
            
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
#t1 = Thread(target = speak_text, args = (lock,))
#t1.start()


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    "-l", "--list-devices", action="store_true",
    help="show list of audio devices and exit")
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
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
parser.add_argument(
    "-m", "--model", type=str, help="language model; e.g. en-us, fr, nl; default is en-us")
args = parser.parse_args(remaining)

try:
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, "input")
        # soundfile expects an int, sounddevice provides a float:
        args.samplerate = int(device_info["default_samplerate"])
        
    if args.model is None:
        model = Model(lang="en-us")
    else:
        model = Model(lang=args.model)

    if args.filename:
        dump_fn = open(args.filename, "wb")
    else:
        dump_fn = None

    with sd.RawInputStream(samplerate=args.samplerate, blocksize = 8000, device=args.device,
            dtype="int16", channels=1, callback=callback):
        print("#" * 80)
        print("Press Ctrl+C to stop the recording")
        print("#" * 80)

        rec = KaldiRecognizer(model, args.samplerate)
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                #words = rec.Result()
                #print(rec.Result())
                #output = rec.Result()
                #print(output["text"])
                words = ""
                words = json.loads(rec.Result())["text"]
                text_buffer = words
                print(words)
                
                audio = generate(
                    text=words,
                    voice=Voice(
                        voice_id='EXAVITQu4vr4xnSDxMaL',
                        settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
                    )
                )
                play(audio)
                
                
            else:
                #print(rec.PartialResult())
                words = json.loads(rec.PartialResult())["partial"]
                #print(words)
                
            if dump_fn is not None:
                dump_fn.write(data)

except KeyboardInterrupt:
    print("\nDone")
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ": " + str(e))