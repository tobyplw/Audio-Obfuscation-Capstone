import socket
import pyaudio
import threading

# CONSTANTS FOR SOCKET
HOST = '74.135.7.54'
PORT = 9999

# CONSTANTS FOR PyAudio
FORMAT = pyaudio.paInt16
RATE = 24000
CHUNK_SIZE = 512
CHANNELS = 1

# Function for listening thread
def listen(socket, data_stream):
    while True:
        data, addr = socket.recvfrom(CHUNK_SIZE)
        data_stream.write(data)

# Function for talking thread
def talk(socket, data_stream):
    while True:
        data = data_stream.read(CHUNK_SIZE)
        socket.sendto(data, (HOST, PORT))

# Create audio object and play and record
audio = pyaudio.PyAudio()

# Create client socket
# @NOTE: AF_INET specifies the ipv4 address family.
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SOCKET_SIZE = 8192
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKET_SIZE)
client_socket.bind(('10.20.45.43', 2323))

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