import socket
import struct
import time
import sys
from pylibsrtp import Policy, Session
import pyaudio
import random
import os, fcntl
import errno
import threading
from vocoder import Vocoder
import numpy as np

DEBUG = 0
# CONSTANTS FOR PyAudio
#FORMAT = pyaudio.paFloat32
FORMAT_TALK = pyaudio.paFloat32
FORMAT_LISTEN = pyaudio.paInt16
RATE = 16000
CHUNK_SIZE_SEND = 512
CHUNK_SIZE_TALK = 256
CHANNELS = 1

BUFFER_SIZE = 5

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
    voc = Vocoder(create_random_seed = False, rate = RATE, chunk = CHUNK_SIZE_TALK, distortion=0.1)

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


            in_data = voc.transform(in_data)
            pcm_data = voc.float2pcm(in_data)
            data = pcm_data.tobytes('C')
    
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
    print("Recieving audio on " + recieving_ip)
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

name = sys.argv[1].lower()
if name == 'tyler':
    destination_ip = '74.135.7.54'
    #destination_ip = 'localhost'  # Replace with the destination IP address
    destination_port = 9999  # Replace with the destination port
    recieving_port = 2323

elif name == 'toby':
    destination_ip = '23.244.15.222'
    destination_port = 2323
    recieving_port = 9999

destination_ip = '127.0.0.1'
hostname = socket.gethostname()
recieving_ip = socket.gethostbyname(hostname)
recieving_ip = '127.0.0.1'
# recieving_ip = '10.20.45.43' # Tyler local ipv4
#recieving_ip = '0.0.0.0'
#recieving_ip = 'localhost'



# Create a UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
fcntl.fcntl(udp_socket, fcntl.F_SETFL, os.O_NONBLOCK)

# Bind the socket to a specific port
udp_socket.bind((recieving_ip, recieving_port))

audio = pyaudio.PyAudio()
record_stream = audio.open(format=FORMAT_TALK, 
                    rate=RATE, 
                    channels=CHANNELS,
                    frames_per_buffer=CHUNK_SIZE_TALK,
                    input=True,
                    output=False)

listen_stream = audio.open(format=FORMAT_LISTEN, 
                  channels=CHANNELS, 
                  rate=RATE, 
                  output=True, 
                  input=False,
                  frames_per_buffer=CHUNK_SIZE_SEND)


listen_thread = threading.Thread(target=listen, args=(udp_socket, listen_stream))

talk_thread = threading.Thread(target=talk, args=(udp_socket, record_stream, destination_ip, destination_port))

if name == 'tyler':
    listen_thread.start()
if name == 'toby':
    talk_thread.start()
