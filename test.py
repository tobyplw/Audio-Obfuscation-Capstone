import pyaudio

audio  = pyaudio.PyAudio()

input_devices = []
CHANNELS = 1

seen_input_devices = set()  # Track seen input device names

virtual_device_keywords = ['Virtual', 'Streaming', 'Broadcast', 'NVIDIA', 'DroidCam', 'RTX-Audio', 'Wave']

for i in range(audio.get_device_count()):
    device = audio.get_device_info_by_index(i)
    device_name = device['name']

    # Skip virtual devices based on keywords
    if any(keyword in device_name for keyword in virtual_device_keywords):
        continue

    # Filter and add input devices, avoiding duplicates
    if device['maxInputChannels'] >= CHANNELS and device_name not in seen_input_devices:
        input_devices.append(device)
        seen_input_devices.add(device_name)  # Mark this device name as seen

for x in range(len(input_devices)):
    print input_devices[x]