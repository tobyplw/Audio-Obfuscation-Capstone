import pyaudio

DEBUG = 0
# CONSTANTS FOR PyAudio
#FORMAT = pyaudio.paFloat32
FORMAT_TALK = pyaudio.paFloat32
FORMAT_LISTEN = pyaudio.paInt16
RATE = 24000
CHUNK_SIZE_SEND = 512
CHUNK_SIZE_TALK = 256
CHANNELS = 1

BUFFER_SIZE = 5

audio = pyaudio.PyAudio()


num_devices = audio.get_device_count()

input_devices = []
output_devices = []
for i in range(num_devices):
    device = audio.get_device_info_by_index(i)
    if device['maxInputChannels'] > 0 and device['maxOutputChannels'] == 0:
        input_devices.append(device)
    elif device['maxInputChannels'] == 0 and device['maxOutputChannels'] > 0:
        output_devices.append(device)


for i in range(len(input_devices)):
    print(i, ': ', input_devices[i]['name'])

user_input_index = int(input('Please select an input device: '))
user_input_device = input_devices[user_input_index]['index']

for i in range(len(output_devices)):
    print(i, ': ', output_devices[i]['name'])

user_output_index = int(input('Please select an output device: '))
user_output_device = output_devices[user_output_index]['index']

record_stream = audio.open(format=FORMAT_TALK, 
                    rate=RATE, 
                    channels=CHANNELS,
                    frames_per_buffer=CHUNK_SIZE_TALK,
                    input=True,
                    output=False,
                    input_device_index=user_input_device)

listen_stream = audio.open(format=FORMAT_LISTEN, 
                  channels=CHANNELS, 
                  rate=RATE, 
                  output=True, 
                  input=False,
                  frames_per_buffer=CHUNK_SIZE_SEND,
                  output_device_index=user_output_device)

