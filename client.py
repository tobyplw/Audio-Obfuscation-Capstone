import socket
import pyaudio
from threading import Thread

# CONSTANTS FOR SOCKET
HOST = '127.0.0.1'
PORT = 2323

# CONSTANTS FOR PyAudio
FORMAT = pyaudio.paInt16
RATE = 44100
CHUNK_SIZE = 1024
CHANNELS = 1

# Function for listening thread
def listen(conn):
    return

# Function for talking thread
def talk():
    return

# Create the threads
listen_thread = Thread(target=listen)
talk_thread = Thread(target=talk)

# Create audio object and play and record
audio = pyaudio.PyAudio()

# @NOTE: Not used currently
play = audio.open(format=FORMAT, 
                  channels=CHANNELS, 
                  rate=RATE, 
                  output=True, 
                  frames_per_buffer=CHUNK_SIZE)

record = audio.open(format=FORMAT, 
                    rate=RATE, 
                    channels=CHANNELS,
                    frames_per_buffer=CHUNK_SIZE,
                    input=True)

# Create client socket
# @NOTE: AF_INET specifies the ipv4 address family.
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to server
client_socket.connect((HOST, PORT))
print("Connected to server")

# Stream audio from microphone to server

while True:
    data = record.read(CHUNK_SIZE, exception_on_overflow=False)
    client_socket.sendall(data)


# UNREACHABLE
record.stop_stream()
record.close()
audio.terminate()