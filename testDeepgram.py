from dotenv import load_dotenv
import logging, verboselogs
from time import sleep
from call import send_transcription_message
import pyaudio
from queue import Queue
from threading import Thread
import numpy as np


from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

DEBUG = 0
# CONSTANTS FOR PyAudio
FORMAT_TALK = pyaudio.paFloat32
FORMAT_LISTEN = pyaudio.paInt16
RATE = 24000
CHUNK_SIZE_SEND = 512
CHUNK_SIZE_TALK = 256
CHANNELS = 1
BUFFER_SIZE = 5


load_dotenv()

audio_data = Queue()

def start_speech_to_text_transcription():
    id_num = 0
    try:
        deepgram: DeepgramClient = DeepgramClient(api_key="5e31c0c3ca3a70e248b06ebc0917f9c8571f3d94")

        dg_connection = deepgram.listen.live.v("1")

        def on_open(self, open, **kwargs):
            print(f"\n\n{open}\n\n")

        def determineSpeakers(words):
            speaker_list = {}
            for word in words:
                speaker = word['speaker']
                if speaker in speaker_list:
                    speaker_list[speaker].append(word.word)
                else:
                    speaker_list[speaker] = [word.word]

            return speaker_list

        def parse_message(message):
            nonlocal id_num
            parsed_message = {}
            parsed_message['id'] = id_num
            parsed_message['is_final'] = message.is_final
            if message.is_final:
                id_num+=1
            parsed_message['text'] = determineSpeakers(message.channel.alternatives[0].words)
            return parsed_message


        def on_message(self, result, **kwargs):
            parsed_message = parse_message(result)
            sentence = result.channel.alternatives[0].transcript


            if len(sentence) > 0:
                print(parsed_message)
                #send_transcription_message(call_session, user, parsed_message)
                #update_textbox_callback(f"Speaker: {sentence}\n")
                #update_textbox_callback(f" {sentence}")

        def on_error(self, error, **kwargs):
            print(f"\n\n{error}\n\n")

        def on_close(self, close, **kwargs):
            print(f"\n\n{close}\n\n")

        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        dg_connection.on(LiveTranscriptionEvents.Close, on_close)

        options: LiveOptions = LiveOptions(
            model="nova-2",
            punctuate=True,
            diarize=True,
            interim_results=True,
            language="en-US",
            encoding="linear16",
            channels=1,
            sample_rate=24000,
        )
        dg_connection.start(options)

        while(True):
            if not audio_data.empty():
                dg_connection.send(audio_data.get())


        # Indicate that we've finished
        dg_connection.finish()
        return

    except Exception as e:
        print(f"Could not open socket: {e}")
        return


audio = pyaudio.PyAudio()
record_stream = audio.open(format=FORMAT_TALK, 
                        rate=RATE, 
                        channels=CHANNELS,
                        frames_per_buffer=CHUNK_SIZE_TALK,
                        input=True,
                        output=False)


transcription_thread = Thread(target=start_speech_to_text_transcription,daemon=True)
transcription_thread.start()
print("Listening for Audio")
while True:
    raw_data = record_stream.read(CHUNK_SIZE_SEND, exception_on_overflow=False)
    audio_np_float32 = np.frombuffer(raw_data, dtype=np.float32)
    audio_np_int16 = (audio_np_float32 * 32767).astype(np.int16)
    audio_data.put(audio_np_int16.tobytes())

