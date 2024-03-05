import socket
import struct
from pylibsrtp import Policy, Session
import random
import os, fcntl
import time
import errno
import sys
import pyaudio

# CONSTANTS FOR PyAudio
FORMAT = pyaudio.paInt16
RATE = 24000
CHUNK_SIZE = 512
CHANNELS = 1

audio = pyaudio.PyAudio()
listen_stream = audio.open(format=FORMAT, 
                  channels=CHANNELS, 
                  rate=RATE, 
                  output=True, 
                  input=False,
                  frames_per_buffer=CHUNK_SIZE)

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

def incoming_buffer(buffer, rtp, seq_number, time_delta = 0):
    #print("Buffer length: " + str(len(buffer)))
    allowed_time = 100
    if (len(buffer) >=5) or (time_delta > allowed_time):
        lowest_num = random.choice(list(buffer.keys()))
        #print(buffer.keys())
        for num in buffer.keys():
            if num < lowest_num:
                lowest_num = num
        packet = buffer[lowest_num]
        del buffer[lowest_num]
        buffer[seq_number] = rtp
        return packet
    else:
        buffer[seq_number] = rtp
        return None


packet_buffer = {}
recieving_ip = '172.20.10.2'  # Replace with the destination IP address
recieving_port = 8801  # Replace with the destination port
# Create a UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
fcntl.fcntl(udp_socket, fcntl.F_SETFL, os.O_NONBLOCK)

# Bind the socket to a specific port
udp_socket.bind((recieving_ip, recieving_port))
key = (b'\x00' * 30)
rx_policy = Policy(key=key, ssrc_type=Policy.SSRC_ANY_INBOUND)
rx_session = Session(policy=rx_policy)
previous_time = 0
try: 
    while True:
        # Receive data and address of the sender
        
        try:
            data, sender_address = udp_socket.recvfrom(969)

            # unprotect RTP
            rtp = rx_session.unprotect(data)
            
            # Parse the RTP header
            rtp_header = parse_rtp_header(rtp)
            seq_num = rtp_header["sequence_number"]
            to_play = incoming_buffer(packet_buffer, rtp, seq_num)
            
            if to_play is not None:
                to_play_header = parse_rtp_header(to_play)
            else:
                continue
            listen_stream.write(to_play)
            current_time = to_play_header["timestamp"]
            elasped_time = current_time - previous_time
            # Print header information
            # print("__________________________")
            # print("RTP Header:")
            # print("Version:", to_play_header["version"])
            # print("Padding:", to_play_header["padding"])
            # print("Extension:", to_play_header["extension"])
            # print("CSRC Count:", to_play_header["csrc_count"])
            # print("Marker:", to_play_header["marker"])
            # print("Payload Type:", to_play_header["payload_type"])
            print("Sequence Number:", to_play_header["sequence_number"])
            # print("Timestamp:", to_play_header["timestamp"])
            # print("Time Delta: " + str(elasped_time) + " ms")
            # print("SSRC:", to_play_header["ssrc"])
            # print("__________________________")
            # print()
            previous_time = to_play_header["timestamp"]
        except socket.error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                time. sleep(1)
                print('No data available')
                continue
            else:
                # a "real" error occurred
                print(e)
                sys.exit(1)
    
except KeyboardInterrupt:
    # Close the socket
    udp_socket.close()
