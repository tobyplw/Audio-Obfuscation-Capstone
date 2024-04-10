from dotenv import load_dotenv
import logging, verboselogs
from time import sleep
from call import send_transcription_message, talk


from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

# global dg_connection

load_dotenv()

def start_speech_to_text_transcription(update_textbox_callback, stop_event, user, call_session):
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
                send_transcription_message(call_session, user, parsed_message)
                #update_textbox_callback(f"Speaker: {sentence}\n")
                #update_textbox_callback(f" {sentence}")


        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

        def on_error(self, error, **kwargs):
            print(f"\n\n{error}\n\n")

        def on_close(self, close, **kwargs):
            print(f"\n\n{close}\n\n")

        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        # dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        dg_connection.on(LiveTranscriptionEvents.Close, on_close)

        options: LiveOptions = LiveOptions(
            model="nova-2",
            interim_results=True,
            language=user.spoken_language,
            sample_rate=16000,
            channels=1,

            # This is how deepgram devs initialize (we get an error)
            #: Exception in AsyncLiveClient._listening: 'speaker'
            #: Exception in LiveClient._listening: 'speaker'
            # model="nova-2",
            # punctuate=True,
            # language="en-US",
            # encoding="linear16",
            # channels=1,
            # sample_rate=16000,
            # # To get UtteranceEnd, the following must be set:
            # interim_results=True,
            # utterance_end_ms="1000",
            # vad_events=True,
        )
        dg_connection.start(options)

        # Open a microphone stream on the default input device

        # microphone = Microphone(dg_connection.send)

        # start microphone
        # microphone.start()
        

        # Use a loop to periodically check the stop condition
        while not stop_event.is_set():
            if not call_session.audio_data.empty():
                # print(scaled_data)
                dg_connection.send(call_session.audio_data.get())
                # print(call_session.audio_data.qsize())
            # sleep(0.1)  # Wait briefly before checking again to reduce CPU usage

        # Wait for the microphone to close
        # microphone.finish()
        # Indicate that we've finished
        dg_connection.finish()
        return

    except Exception as e:
        print(f"Could not open socket: {e}")
        return