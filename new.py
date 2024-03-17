import pyaudio

def list_audio_devices():
    p = pyaudio.PyAudio()
    print("Available audio devices:")
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        print(f"{i}: {device_info.get('name')} (Input Channels: {device_info.get('maxInputChannels')})")

list_audio_devices()