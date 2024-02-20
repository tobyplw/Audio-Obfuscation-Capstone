import socket
import pyaudio
import threading

# CONSTANTS FOR SOCKET
HOST = '127.0.0.1'
PORT = 2323

# CONSTANTS FOR PyAudio
FORMAT = pyaudio.paInt16
RATE = 44100
CHUNK_SIZE = 4096
CHANNELS = 1

# Function for listening thread
def listen(socket, data_stream):
    while True:
        data = socket.recv(CHUNK_SIZE)
        data_stream.write(data)

# Function for talking thread
def talk(socket, data_stream):
    while True:
        data = data_stream.read(CHUNK_SIZE)
        socket.sendall(data)

# Create audio object and play and record
audio = pyaudio.PyAudio()

# Create client socket
# @NOTE: AF_INET specifies the ipv4 address family.
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to server
client_socket.connect((HOST, PORT))
print("Connected to server")

# @NOTE: Not used currently
listen_stream = audio.open(format=FORMAT, 
                  channels=CHANNELS, 
                  rate=RATE, 
                  output=True, 
                  input=False,
                  frames_per_buffer=CHUNK_SIZE)

record_stream = audio.open(format=FORMAT, 
                    rate=RATE, 
                    channels=CHANNELS,
                    frames_per_buffer=CHUNK_SIZE,
                    input=True,
                    output=False)



# Create the threads
listen_thread = threading.Thread(target=listen, args=(client_socket, listen_stream))
talk_thread = threading.Thread(target=talk, args=(client_socket, record_stream))

listen_thread.start()
talk_thread.start()

# Wait for the threads to finish execution
# listen_thread.join()
# talk_thread.join()