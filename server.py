import socket
import pyaudio
import threading

# @NOTE: Use 2 threads 
# https://stackoverflow.com/questions/33434007/python-socket-send-receive-messages-at-the-same-time
# CONSTANTS FOR SOCKET
HOST = '127.0.0.1'
PORT = 2323

# CONSTANTS FOR PyAudio
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK_SIZE = 1024

# Function for the listening thread
def listen():
    return

# Function for the talking thread
def talk():
    return

# Create the threads
listen_thread = threading.Thread(target=listen)
talk_thread = threading.Thread(target=talk)


# Create PyAudio object
audio = pyaudio.PyAudio()

# Create stream for audio output (playback)
play = audio.open(format=FORMAT, 
                  channels=CHANNELS, 
                  rate=RATE, 
                  output=True, 
                  frames_per_buffer=CHUNK_SIZE)

# @NOTE: Maybe channels should be increased, check docs
record = audio.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE)


# Create socket object and bind to port
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))

# Listen for connections and accept
server_socket.listen(1)
print('Server started... listening for connection!')
conn, addr = server_socket.accept()

# Connected
with conn:
    print('Connection established with client: ', addr)

    # Send and receive voice data
    while True:
        audio_data = conn.recv(CHUNK_SIZE)
        # voice_data = record.read(CHUNK_SIZE, exception_on_overflow=False)

        # TODO: MANIPULATE DATA HERE
        # NOTE: Check IP of caller to ensure only their voice is altered
        
        # TODO: SEND TO OTHER CLIENT
        # conn.sendall(voice_data)
        play.write(audio_data)

        
# Close all Streams @NOTE: They are unreachable with current imp
record.stop_stream()
record.close()
play.close()
audio.terminate()