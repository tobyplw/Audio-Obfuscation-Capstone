import logging, verboselogs
from time import sleep
from call import send_transcription_message, talk
import queue
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

def start_speech_to_text_transcription(transcription_on, user, call_session):
    id_num = 0
    try:
        #Deepgram client setup, refer to documention for for info
        deepgram: DeepgramClient = DeepgramClient(api_key="5e31c0c3ca3a70e248b06ebc0917f9c8571f3d94")

        #Start a live transcription session with version 1 API
        dg_connection = deepgram.listen.live.v("1")
        
        #Function to handle when the socket opens
        def on_open(self, open, **kwargs):
            print(f"\n\n{open}\n\n")

        #Function to assign words to their respective speakers
        def determineSpeakers(words):
            speaker_list = {}
            for word in words:
                speaker = word['speaker']
                if speaker in speaker_list:
                    speaker_list[speaker].append(word.word)
                else:
                    speaker_list[speaker] = [word.word]

            return speaker_list

        #Function to parse incoming messages
        def parse_message(message):
            nonlocal id_num
            parsed_message = {}
            parsed_message['id'] = id_num
            parsed_message['is_final'] = message.is_final
            if message.is_final:
                id_num+=1
            parsed_message['text'] = determineSpeakers(message.channel.alternatives[0].words)
            return parsed_message

        #Function to handle incoming transcription messages
        def on_message(self, result, **kwargs):
            parsed_message = parse_message(result)
            sentence = result.channel.alternatives[0].transcript

            if len(sentence) > 0 and not user.is_muted:
                # print(parsed_message)
                send_transcription_message(call_session, user, parsed_message)
                if parsed_message['is_final']:
                    call_session.add_to_log(parsed_message["text"], external = False)
                    if user.tts_on.is_set():
                        call_session.determine_TTS(parsed_message["text"])

        #Function to handle errors during transcription
        def on_error(self, error, **kwargs):
            print(f"\n\n{error}\n\n")

        #Function to handle the closing of the transcription socket
        def on_close(self, close, **kwargs):
            print(f"\n\n{close}\n\n")

        #Register event handlers for the various transcription events
        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        dg_connection.on(LiveTranscriptionEvents.Close, on_close)

        options: LiveOptions = LiveOptions(
            model="nova-2",
            punctuate=True,
            diarize=True,
            interim_results=True,
            language=user.spoken_language,
            encoding="linear16",
            channels=1,
            sample_rate=24000,
        )
        #Start the transcription with the configured options
        dg_connection.start(options)

        # Use a loop to periodically check the stop condition
        while not call_session.call_end.is_set():
            if not call_session.audio_data.empty():
                # print(scaled_data)
                try:
                    data = call_session.audio_data.get(timeout = 5.0)
                    if data:
                        dg_connection.send(data)
                except queue.Empty:
                    continue  # Continue waiting if the queue is empty

        # Indicate that we've finished
        dg_connection.finish()
        return

    except Exception as e:
        print(f"Could not open socket: {e}")
        return
