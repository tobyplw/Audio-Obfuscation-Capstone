import os
import requests
import pyaudio

STREAM_AUDIO=True
MODEL_NAME = f"aura-orion-en"
CONTAINER= f"none"
ENCODING = f"linear16"
SAMPLE_RATE = 24000
DEEPGRAM_URL = f"https://api.deepgram.com/v1/speak?model={MODEL_NAME}&encoding={ENCODING}&sample_rate={SAMPLE_RATE}&container={CONTAINER}"
# Make sure to export DEEPGRAM_API_KEY=xxx with your own API key
DG_API_KEY = "5e31c0c3ca3a70e248b06ebc0917f9c8571f3d94"
TEXT = f"Hello World! This is a longer sentence"

headers = {
    "Authorization": f"Token {DG_API_KEY}",
    "Content-Type": "application/json"
}


# set this to to what ever output device is saved in our settings.
output_device_index = 4


def send_streaming_audio(payload, call_session):
    print("In SYNTHESIZE")
    print(payload)
    # Stream the audio as you get it and play it
    with requests.post(DEEPGRAM_URL, stream=True, headers=headers, json=payload) as r:
        for chunk in r.iter_content(chunk_size=512):
            if chunk:
                #print("adding Chunk")
                #if len(chunk) == 512:
                call_session.obfuscation_queue.put(chunk)

    # After the loop ends, there might still be data left in the buffer that hasn't been played yet.
    


def synthesize_text(text, call_session):
    # Update the text and payload with the new text
    payload = {
        "text": text
    }
    # Send the TTS request
    send_streaming_audio(payload, call_session)

