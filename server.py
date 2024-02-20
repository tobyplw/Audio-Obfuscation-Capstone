import socket
import pyaudio
import threading

# CONSTANTS FOR SOCKET
HOST = '127.0.0.1'
PORT = 2323

# CONSTANTS FOR PyAudio
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK_SIZE = 4096

# Function for transferring data between clients
def transfer(sender_socket, receiver_socket):
    while True:
        data = receiver_socket.recv(CHUNK_SIZE)
        # @NOTE: Manipulate data here
        sender_socket.sendall(data)


# Create PyAudio object
audio = pyaudio.PyAudio()

# Create stream for audio output (playback)
record_stream = audio.open(format=FORMAT, 
                    channels=CHANNELS, 
                    rate=RATE, 
                    output=False,
                    input=True, 
                    frames_per_buffer=CHUNK_SIZE)

# @NOTE: Maybe channels should be increased, check docs
listen_stream = audio.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=False,
                    output=True,
                    frames_per_buffer=CHUNK_SIZE)


# Create socket object and bind to port
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))

# Listen for connections and accept
server_socket.listen(2)
print('Server started... listening for connection!')
client_socket1, addr1 = server_socket.accept()
client_socket2, addr2 = server_socket.accept()

# Create the threads
transfer_thread1 = threading.Thread(target=transfer, args=(client_socket1, client_socket2))
transfer_thread2 = threading.Thread(target=transfer, args=(client_socket2, client_socket1))

# Start the threads
transfer_thread1.start()
transfer_thread2.start()

# Wait for them to finish
# transfer_thread1.join()
# transfer_thread2.join()
        
# Close all Streams
record_stream.close()
audio.terminate()