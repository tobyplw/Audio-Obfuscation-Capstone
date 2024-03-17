import socket
import struct
import time
import sys
from pylibsrtp import Policy, Session
import pyaudio
import random
# import os, fcntl
import errno
import threading
# from vocoder import Vocoder
import numpy as np

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

def get_user_devices(audio):
    num_devices = audio.get_device_count()

    # Separate input and output devices into two lists
    input_devices = []
    output_devices = []
    for i in range(num_devices):
        device = audio.get_device_info_by_index(i)
        if device['maxInputChannels'] > 0 and device['maxOutputChannels'] == 0 and device['maxInputChannels'] == CHANNELS:
            input_devices.append(device)
        elif device['maxInputChannels'] == 0 and device['maxOutputChannels'] > 0:
            output_devices.append(device)

    # Prompt the user for input device
    for i in range(len(input_devices)):
        print(i, ': ', input_devices[i]['name'])

    user_input_index = int(input('Please select an input device: '))
    user_input_device = input_devices[user_input_index]['index']

    # Prompt the user for output device
    for i in range(len(output_devices)):
        print(i, ': ', output_devices[i]['name'])

    user_output_index = int(input('Please select an output device: '))
    user_output_device = output_devices[user_output_index]['index']

    # Return devices selected by user
    return user_input_device, user_output_device


def create_rtp_header(sequence_number, timestamp, ssrc, payload_type):
    version = 2  # RTP version
    padding = 0
    extension = 0
    csrc_count = 0 
    marker = 0
    payload_type = payload_type 
    header = struct.pack('!BBHII', (version << 6) | (padding << 5) | (extension << 4) | csrc_count,
                         (marker << 7) | payload_type, sequence_number, timestamp, ssrc)
    return header


def parse_rtp_header(data):
    # Parse the RTP header
    version = (data[0] & 0xC0) >> 6
    padding = (data[0] & 0x20) >> 5
    extension = (data[0] & 0x10) >> 4
    csrc_count = data[0] & 0x0F
    marker = (data[1] & 0x80) >> 7
    payload_type = data[1] & 0x7F
    sequence_number = struct.unpack('!H', data[2:4])[0]
    timestamp = struct.unpack('!I', data[4:8])[0]
    ssrc = struct.unpack('!I', data[8:12])[0]

    return {
        "version": version,
        "padding": padding,
        "extension": extension,
        "csrc_count": csrc_count,
        "marker": marker,
        "payload_type": payload_type,
        "sequence_number": sequence_number,
        "timestamp": timestamp,
        "ssrc": ssrc
    }

def print_header(header, elapsed_time):
    print("__________________________")
    print("RTP Header:")
    print("Version:", header["version"])
    print("Padding:", header["padding"])
    print("Extension:", header["extension"])
    print("CSRC Count:", header["csrc_count"])
    print("Marker:", header["marker"])
    print("Payload Type:", header["payload_type"])
    print("Sequence Number:", header["sequence_number"])
    print("Timestamp:", header["timestamp"])
    print("Time Delta: " + str(elapsed_time) + " ms")
    print("SSRC:", header["ssrc"])
    print("__________________________")
    print()

def incoming_buffer(buffer, rtp, seq_number, time_delta = 0):
    allowed_time = 100
    if (len(buffer) >= BUFFER_SIZE) or (time_delta > allowed_time):
        keys = buffer.keys()
        lowest_num = random.choice(list(keys))
        for num in keys:
            if num < lowest_num:
                lowest_num = num
        packet = buffer[lowest_num]
        del buffer[lowest_num]
        buffer[seq_number] = rtp
        return packet
    else:
        buffer[seq_number] = rtp
        return None

def talk(udp_socket, record_stream, destination_ip, destination_port):
    ssrc = 5678 
    payload_type = 0  
    # voc = Vocoder(create_random_seed = False, rate = RATE, chunk = CHUNK_SIZE_TALK, distortion=0.10)

    # protect RTP
    key = (b'\x00' * 30) #should change the key
    tx_policy = Policy(key=key, ssrc_type=Policy.SSRC_ANY_OUTBOUND)
    tx_session = Session(policy=tx_policy)
    sequence_number = 0
    print("Sending audio to " + destination_ip)
    try:
        while True:
            current_time_ms = int(time.time() * 1000) % (1 << 32)
            rtp_header = create_rtp_header(sequence_number, current_time_ms, ssrc, payload_type)
            raw_data = record_stream.read(CHUNK_SIZE_TALK)
            in_data = np.frombuffer(raw_data, dtype=np.float32)


            #in_data = voc.transform(in_data)
            # pcm_data = voc.float2pcm(in_data)
            # data = pcm_data.tobytes('C')
    
            packet = rtp_header + data
            srtp = tx_session.protect(packet)
            udp_socket.sendto(srtp, (destination_ip, destination_port))
            sequence_number+=1
    except KeyboardInterrupt:
        udp_socket.close()
        record_stream.close()

def listen(udp_socket, listen_stream):
    packet_buffer = {}
    key = (b'\x00' * 30)
    rx_policy = Policy(key=key, ssrc_type=Policy.SSRC_ANY_INBOUND)
    rx_session = Session(policy=rx_policy)
    previous_time = 0
    prev_play_time = 0
    print("Recieving audio on " + receiving_ip)
    try: 
        while True:
            try:
                data, sender_address = udp_socket.recvfrom(1046)

                # unprotect RTP
                rtp = rx_session.unprotect(data)
                
                # Parse the RTP header
                rtp_header = parse_rtp_header(rtp)
                seq_num = rtp_header["sequence_number"]
                to_play = incoming_buffer(packet_buffer, rtp, seq_num)
                #to_play = rtp
                if to_play is not None:
                    to_play_header = parse_rtp_header(to_play)
                else:
                    continue

                #play_time = int(time.time() * 1000)
                #prev_play_time = play_time

                final = to_play[12:1036]
                listen_stream.write(final)

                current_time = to_play_header["timestamp"]
                elapsed_time = current_time - previous_time
                if DEBUG == 1:
                    print_header(to_play_header, elapsed_time)

                previous_time = to_play_header["timestamp"]


            except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    time. sleep(0.05)
                    continue
                else:
                    # an actual error occurred
                    print(e)
                    sys.exit(1)
        
    except KeyboardInterrupt:
        # Close the socket and stream
        udp_socket.close()
        listen_stream.close()


def listen_for_conn(receiving_ip, receiving_port):
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.bind((receiving_ip, receiving_port))
    listen_socket.listen(1)
    while True:
        print("Waiting for connections")
        client_socket, client_address = listen_socket.accept()  # Accept incoming connection
        print(f"Incoming connection from {client_address}")
        # Handle the connection in a new thread
        client_thread = threading.Thread(target=accept_call, args=(client_socket,client_address))
        client_thread.start()

#take in initial info, make sure this is a connection coming from our platform, 
#determine the current state of the user (i.e. already in a call)
#if all good to start call, then confirm with TCP, then start the other threads
def accept_call(conn, addr):
    # Check the ip here
    # conn.close() if ip unknown (not in database)
    with conn:
        print(f"Connected to client at {addr}")
        message = input("Enter yes to begin communication (anything else to end): ")
        
        if message.lower() == 'yes':
            conn.sendall(message.encode())
            print('Communication Starting!!!!!')
            listen_thread.start()
            talk_thread.start()
        else:
            return
        
            
#wait for caller to initiate a call
#i.e. for terminal, wait for "call X" on command line
def call_user(destination_ip, destination_port):

    print("Trying to call: " + destination_ip)
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        tcp_socket.connect((destination_ip, destination_port))

        data = tcp_socket.recv(1024)
        message = data.decode()
        
        if message == 'yes':
            print('\n\nCommunication Starting!!!!!')
            listen_thread.start()
            talk_thread.start()
            
    except Exception as e:
        print(f"Error connecting: {e}")
        raise ConnectionRefusedError
    return



name = sys.argv[1].lower()
if name == 'tyler':
    destination_ip = '74.135.7.54'
    destination_tcp_port = 9998  # Replace with the destination port
    destination_udp_port = 9999  # Replace with the destination port
    receiving_tcp_port = 2324
    receiving_udp_port = 2323
    receiving_ip = '10.20.45.43' # Tyler local ipv4

elif name == 'toby':
    destination_ip = '23.244.15.222'
    destination_tcp_port = 2324
    destination_udp_port = 2323
    receiving_tcp_port = 9998
    receiving_udp_port = 9999
    hostname = socket.gethostname()
    receiving_ip = socket.gethostbyname(hostname)

elif name == 'send': #for localhost testing
    destination_ip = '127.0.0.1'
    receiving_ip = '127.0.0.1'
    destination_port = 2323
    receiving_port = 9999

elif name == 'receive': #for localhost testing
    receiving_ip = '127.0.0.1'
    destination_port = 9999  
    destination_ip = '127.0.0.1'
    receiving_port = 2323

# Create a UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
fcntl.fcntl(udp_socket, fcntl.F_SETFL, os.O_NONBLOCK)


# Bind the socket to a specific port
udp_socket.bind((receiving_ip, receiving_udp_port))

audio = pyaudio.PyAudio()

user_input_device, user_output_device = get_user_devices(audio)

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

listen_thread = threading.Thread(target=listen, args=(udp_socket, listen_stream))
talk_thread = threading.Thread(target=talk, args=(udp_socket, record_stream, destination_ip, destination_udp_port))

listening_thread = threading.Thread(target=listen_for_conn)
# listening_thread.start()

# while True:
#     user_input = input('Enter the user id of the person you want to call: ')
#     if user_input == 'call':
#         call_user(destination_ip, destination_tcp_port)



if name == 'receive':
    listen_thread.start()
elif name == 'send':
    talk_thread.start()
else:
    listen_thread.start()
    talk_thread.start()






'''
User logs on
- Immediately updates its external ip address, external port numbers
- Program starts to listen for other applications trying to connect with it

User makes a call
- Use the username to get the other users IP address and port
- Start a TCP Connection with the other user to determine if that callee wants to accept the call
- If they do want to accept the call, start the talk/listen threads with UDP connection

User accepts a call
- The listen function gets a connection
- User then decides if they want to accept, displays relevant info in initial TCP Packet
- Once accepted, tart the talk/listen threads with UDP connection

User ends call:
- Send TCP packet to other caller signifying end of call
- Shut down talk/listen threads
- Log the call on both ends with relevant data
- End TCP connection



For listening:
- Create a thread upon logging in that is listening
- If a user makes a call, that thread can continue to listen, but if there is another connection, it should first check 
if the user is already in a call and signify the user of a new call
- If a connection occurs, then start the call process

'''





