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
from vocoder import Vocoder
import numpy as np
import database as db
import utilities
import shared
from shared import is_muted



DEBUG = 0
# CONSTANTS FOR PyAudio
FORMAT_TALK = pyaudio.paFloat32
FORMAT_LISTEN = pyaudio.paInt16
RATE = 24000
CHUNK_SIZE_SEND = 512
CHUNK_SIZE_TALK = 256
CHANNELS = 1
BUFFER_SIZE = 5

def get_user_devices(audio):
    num_devices = audio.get_device_count()

    input_devices = []
    output_devices = []

    seen_input_devices = set()  # Track seen input device names
    seen_output_devices = set()  # Track seen output device names

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

        # Filter and add output devices, avoiding duplicates
        if device['maxOutputChannels'] >= CHANNELS and device_name not in seen_output_devices:
            output_devices.append(device)
            seen_output_devices.add(device_name)  # Mark this device name as seen


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


def get_user_input():
    audio  = pyaudio.PyAudio()

    input_devices = []

    seen_input_devices = set()  # Track seen input device names

    virtual_device_keywords = ['Virtual', 'Streaming', 'Broadcast', 'NVIDIA', 'Cam', 'RTX-Audio', 'Wave']

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
    
    audio.terminate()
    return input_devices

def get_user_output():
    audio  = pyaudio.PyAudio()

    output_devices = []

    seen_output_devices = set()  # Track seen output device names

    virtual_device_keywords = ['Virtual', 'Streaming', 'Broadcast', 'NVIDIA', 'DroidCam', 'RTX-Audio', 'Wave']

    for i in range(audio.get_device_count()):
        device = audio.get_device_info_by_index(i)
        device_name = device['name']

        # Skip virtual devices based on keywords
        if any(keyword in device_name for keyword in virtual_device_keywords):
            continue

        # Filter and add output devices, avoiding duplicates
        if device['maxOutputChannels'] >= CHANNELS and device_name not in seen_output_devices:
            output_devices.append(device)
            seen_output_devices.add(device_name)  # Mark this device name as seen

    # Return devices selected by user
    audio.terminate()
    return output_devices


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

def talk(udp_socket, record_stream, callee_username, destination_ip, destination_port):
    ssrc = 5678
    payload_type = 0
    voc = Vocoder(create_random_seed=False, rate=RATE, chunk=CHUNK_SIZE_TALK, distortion=0.10)

    # Protect RTP
    tx_policy = Policy(key=shared.key, ssrc_type=Policy.SSRC_ANY_OUTBOUND)
    tx_session = Session(policy=tx_policy)
    sequence_number = 0
    print("Sending audio to " + destination_ip)
    try:
        while not shared.call_end.is_set():
            current_time_ms = int(time.time() * 1000) % (1 << 32)
            rtp_header = utilities.create_rtp_header(sequence_number, current_time_ms, ssrc, payload_type)
            raw_data = record_stream.read(CHUNK_SIZE_TALK, exception_on_overflow=False)
            in_data = np.frombuffer(raw_data, dtype=np.float32)

            if shared.obfuscation_on:
                in_data = voc.transform(in_data)
            pcm_data = voc.float2pcm(in_data)
            data = pcm_data.tobytes('C')

            packet = rtp_header + data

            # Check if microphone is muted
            if not shared.is_muted:
                srtp = tx_session.protect(packet)
                udp_socket.sendto(srtp, (destination_ip, destination_port))
            else:
                # If muted, you might want to do something (like sending silence or just skipping)
                pass

            sequence_number += 1
    except KeyboardInterrupt:
        udp_socket.close()
        record_stream.close()
    
    print("talk ending")


def listen(udp_socket, listen_stream):
    packet_buffer = {}
    rx_policy = Policy(key=shared.key, ssrc_type=Policy.SSRC_ANY_INBOUND)
    rx_session = Session(policy=rx_policy)
    previous_time = 0
    prev_play_time = 0

    try: 
        while not shared.call_end.is_set():
            try:
                data, sender_address = udp_socket.recvfrom(1046)

                # unprotect RTP
                rtp = rx_session.unprotect(data)
                
                # Parse the RTP header
                rtp_header = utilities.parse_rtp_header(rtp)
                seq_num = rtp_header["sequence_number"]
                to_play = incoming_buffer(packet_buffer, rtp, seq_num)
                #to_play = rtp
                if to_play is not None:
                    to_play_header = utilities.parse_rtp_header(to_play)
                else:
                    continue

                final = to_play[12:1036]
                print("Writing")
                listen_stream.write(final)

                current_time = to_play_header["timestamp"]
                elapsed_time = current_time - previous_time
                if DEBUG == 1:
                    utilities.print_header(to_play_header, elapsed_time)

                previous_time = to_play_header["timestamp"]

                if shared.call_end.is_set():
                    print("listen ending")


            except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    time. sleep(0.05)
                    continue
                else:
                    # an actual error occurred
                    print(f"Socket error occurred: {e}")
                    break  # Break the loop for other errors
        
    except KeyboardInterrupt:
        # Close the socket and stream
        udp_socket.close()
        listen_stream.close()

    print("listen ending")
    

def start_audio_stream(user_input_device, user_output_device, audio):
    record_stream = audio.open(format=FORMAT_TALK, 
                        rate=RATE, 
                        channels=CHANNELS,
                        frames_per_buffer=CHUNK_SIZE_TALK,
                        input=True,
                        output=False,
                        input_device_index=user_input_device["index"])
    
    listen_stream = audio.open(format=FORMAT_LISTEN, 
                channels=CHANNELS, 
                rate=RATE, 
                output=True, 
                input=False,
                frames_per_buffer=CHUNK_SIZE_SEND,
                output_device_index=user_output_device["index"])
    
    return record_stream, listen_stream









