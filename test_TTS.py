import os
import requests
import pyaudio

STREAM_AUDIO=False
MODEL_NAME = f"aura-orion-en"
CONTAINER= f"none"
ENCODING = f"linear16"
SAMPLE_RATE = 48000
DEEPGRAM_URL = f"https://api.deepgram.com/v1/speak?model={MODEL_NAME}&encoding={ENCODING}&sample_rate={SAMPLE_RATE}&container={CONTAINER}"
# Make sure to export DEEPGRAM_API_KEY=xxx with your own API key
DG_API_KEY = "5e31c0c3ca3a70e248b06ebc0917f9c8571f3d94"
TEXT = f"Hello World! This is a longer sentence"

headers = {
    "Authorization": f"Token {DG_API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "text": TEXT
}

stream = None
p = None

# set this to to what ever output device is saved in our settings.
output_device_index = 4

def init_stream():
    global stream
    global p

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # List all audio devices
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        print(f"Device {i}: {dev['name']} - Input Channels: {dev['maxInputChannels']} - Output Channels: {dev['maxOutputChannels']}")

    # Open a stream to play the audio
    stream = p.open(format=p.get_format_from_width(2),
            channels=2,
            rate=SAMPLE_RATE,
            output=True,
            output_device_index=output_device_index)
    
def close_stream():
    global stream
    global p

    if stream is not None:
        # Close the stream
        stream.stop_stream()
        stream.close()

        # Terminate PyAudio
        p.terminate()

def download_and_play_audio():
    response = requests.post(DEEPGRAM_URL, headers=headers, json=payload)
    # print (f"Response: {response}")
    if response.status_code == 200:
        data = response.content
        
        base_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_directory, f"audio.wav")
        with open(file_path, "wb") as f:
                f.write(data)
        play_raw_audio(file_path)
    else:
        print("Error in TTS request:", response.status_code, response.text)

def play_raw_audio(file_path):
    global stream

    # Open the raw file
    with open(file_path, 'rb') as raw_file:
        raw_data = raw_file.read()

    # Open the stream
    init_stream()

    # Play the audio
    stream.write(raw_data)

    # Close Stream
    close_stream()

def play_streaming_audio():
    global stream

    # Open the stream
    init_stream()

    buffer = bytearray()
    min_buffer_size = 256 * 1024  # Minimum bytes to accumulate before playback
    buffered = False
    # Stream the audio as you get it and play it
    with requests.post(DEEPGRAM_URL, stream=True, headers=headers, json=payload) as r:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                if buffered:
                    stream.write(chunk)
                else:
                    buffer.extend(chunk)
                    if len(buffer) >= min_buffer_size:
                        stream.write(bytes(buffer))
                        buffer = bytearray()
                        buffered = True

    # After the loop ends, there might still be data left in the buffer that hasn't been played yet.
    if buffer and not buffered:
        stream.write(bytes(buffer))
    
    # Close the stream
    close_stream()

# Modify the send_tts_request function to not use the global TEXT variable directly in the payload
def send_tts_request():
    global stream

    # play the audio while it is downloading
    if STREAM_AUDIO: 
        play_streaming_audio()

    # Download the audio fully and then play it
    else: 
        download_and_play_audio()


def synthesize_text(text):
    global TEXT, payload
    
    # Update the text and payload with the new text
    TEXT = text
    payload = {
        "text": TEXT
    }

    # Send the TTS request
    send_tts_request()


synthesize_text(TEXT)