import os
import requests
import pyaudio

STREAM_AUDIO=True
MODEL_NAME = f"aura-athena-en"
CONTAINER= f"none"
ENCODING = f"linear16"
SAMPLE_RATE = 24000
DEEPGRAM_URL = f"https://api.deepgram.com/v1/speak?model={MODEL_NAME}&encoding={ENCODING}&sample_rate={SAMPLE_RATE}&container={CONTAINER}"
DG_API_KEY = "5e31c0c3ca3a70e248b06ebc0917f9c8571f3d94" #Refer to documentation about this API key
TEXT = f"Hello World! This is a longer sentence"

headers = {
    "Authorization": f"Token {DG_API_KEY}",
    "Content-Type": "application/json"
}


#Function that send audio chunks to be other caller
def send_streaming_audio(payload, call_session):
    #Debugging statements
    print("In SYNTHESIZE")
    print(payload)
    # Stream the audio as you get it and play it
    with requests.post(DEEPGRAM_URL, stream=True, headers=headers, json=payload) as r:
        for chunk in r.iter_content(chunk_size=512):
            if chunk:
                call_session.obfuscation_queue.put(chunk)

    

def send_streaming_audio(payload, call_session):
    print("In SYNTHESIZE")
    print(payload)

    buffer = bytearray()
    min_buffer_size = 256 * 512  # Minimum bytes to accumulate before playback
    chunk_size = 512  # Define the chunk size
    buffered = False

    with requests.post(DEEPGRAM_URL, stream=True, headers=headers, json=payload) as r:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                if buffered:
                    call_session.obfuscation_queue.put(chunk)
                else:
                    buffer.extend(chunk)
                    if len(buffer) >= min_buffer_size:
                        # Send full chunks of 512 bytes
                        while len(buffer) >= chunk_size:
                            call_session.obfuscation_queue.put(bytes(buffer[:chunk_size]))
                            buffer = buffer[chunk_size:]
                        buffered = True

    # After the loop ends, manage any leftover buffer
    if buffer:
        # Send any remaining full chunks
        while len(buffer) >= chunk_size:
            call_session.obfuscation_queue.put(bytes(buffer[:chunk_size]))
            buffer = buffer[chunk_size:]

        # If there's any data left in the buffer that's less than 512 bytes
        if buffer:
            call_session.obfuscation_queue.put(bytes(buffer))

    # Close the stream


def synthesize_text(text, call_session):
    # Update the text and payload with the new text
    payload = {
        "text": text
    }
    # Send the TTS request
    send_streaming_audio(payload, call_session)

