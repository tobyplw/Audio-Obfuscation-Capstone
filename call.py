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
import json
from classes import CallSession
import queue

DEBUG = 0
FORMAT_TALK = pyaudio.paFloat32
FORMAT_LISTEN = pyaudio.paInt16
RATE = 24000
CHUNK_SIZE_SEND = 512
CHUNK_SIZE_TALK = 256
CHANNELS = 1
BUFFER_SIZE = 5

key = (b'\x00' * 30) # Hide this (it is the key to encryption / decryption)

def get_user_input():
    """
    Get the user's available input devices.
    Returns
    -------
    input_devices: List of user input devices
    """

    audio  = pyaudio.PyAudio()
    input_devices = []
    seen_input_devices = set()  # Track seen input device names
    virtual_device_keywords = ['Virtual', 'Streaming', 'Broadcast', 'NVIDIA', 'Cam', 'RTX-Audio', 'Wave']

    # Iterate through all devices
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
    """
    Get the user's available output devices.
    Returns
    -------
    output_devices: List of user output devices
    """

    audio  = pyaudio.PyAudio()
    output_devices = []
    seen_output_devices = set()  # Track seen output device names
    virtual_device_keywords = ['Virtual', 'Streaming', 'Broadcast', 'NVIDIA', 'DroidCam', 'RTX-Audio', 'Wave']

    # Iterate through all devices
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


def talk(record_stream, user, call_session):
    """
    Transmit audio packets through communication link.
    Parameters
    ----------
    record_stream : pyAudio object
        Input audio stream
    user : User object
        User on the application
    call_session : CallSession objects
        Live call on the application
    """

    payload_type = 0
    voc = Vocoder(create_random_seed=False, rate=RATE, chunk=CHUNK_SIZE_TALK, distortion=0.10)
    print("Sending audio to " + call_session.destination_ip)

    # Check if stream and socket are open
    try:

        # Loop while call is active
        while not call_session.call_end.is_set():
           
            # Read in data from open input stream
            raw_data = record_stream.read(CHUNK_SIZE_TALK, exception_on_overflow=False)
            in_data = np.frombuffer(raw_data, dtype=np.float32)

            # Obfuscate if enabled
            if not user.obfuscation_on.is_set():
                orig_data = in_data
                in_data = voc.audio_effects(in_data)

            # Convert to pcm
            pcm_data = voc.float2pcm(in_data)
            data = pcm_data.tobytes('C')

            # Put data into queue
            if not user.is_muted:
                if not user.obfuscation_on.is_set():
                    pcm_data = voc.float2pcm(orig_data)
                    clear_data = pcm_data.tobytes('C')
                    call_session.audio_data.put(clear_data)
                else:
                    call_session.audio_data.put(data)
                
                if user.tts_on.is_set():
                    try:
                        data = call_session.obfuscation_queue.get(timeout = 0.01)
                        if data:
                            current_time_ms = int(time.time() * 1000) % (1 << 32)
                            rtp_header = utilities.create_rtp_header(call_session.get_sequence_number(), current_time_ms, call_session.ssrc, payload_type = 0)
                            packet = rtp_header + data

                            # Encrypt data before sending
                            srtp = call_session.tx_session.protect(packet)
                            user.client_socket.sendto(srtp, (call_session.destination_ip, call_session.destination_port))
                    except queue.Empty:
                        continue
                else:
                    current_time_ms = int(time.time() * 1000) % (1 << 32)
                    rtp_header = utilities.create_rtp_header(call_session.get_sequence_number(), current_time_ms, call_session.ssrc, payload_type = 0)
                    packet = rtp_header + data
                    srtp = call_session.tx_session.protect(packet)
                    user.client_socket.sendto(srtp, (call_session.destination_ip, call_session.destination_port))
            else:
                pass

    except KeyboardInterrupt:
        user.client_socket.close()
        record_stream.close()
    
    i = 0
    while i < 10:
        rtp_header = utilities.create_rtp_header(call_session.get_sequence_number(), current_time_ms, call_session.ssrc, payload_type = 2)
        data = bytes(1024)
        packet = rtp_header + data
        srtp = call_session.tx_session.protect(packet)
        user.client_socket.sendto(srtp, (call_session.destination_ip, call_session.destination_port))
        i+=1
    print("Talk Ending")


def listen(listen_stream, user, hang_up_button, call_session):
    """
    Receive and handle audio packets.
    Parameters
    ----------
    listen_stream : pyAudio object
        Output audio stream
    user : User object
        User on the application
    hang_up_button : Function
        Handles when a call is ended
    call_session : CallSession object
        Live call on the application
    """
    packet_buffer = {}
    previous_time = 0

    # Check if stream and socket are open
    try: 

        # Loop while call is active
        while not call_session.call_end.is_set():
            try:
                data, sender_address = user.client_socket.recvfrom(1036)

                # Decrypt data
                try:
                    rtp = call_session.rx_session.unprotect(data)
                except:
                    continue
                
                # Parse the RTP header
                rtp_header = utilities.parse_rtp_header(rtp)

                # Handle different payload options
                if rtp_header["payload_type"] == 2:
                    print("Callee Hung Up")
                    call_session.call_end.set()
                    hang_up_button.invoke()
                    return
                if rtp_header["payload_type"] == 1:
                    call_session.transcription_queue.put(rtp[12:])
                    continue

                seq_num = rtp_header["sequence_number"]
                to_play = incoming_buffer(packet_buffer, rtp, seq_num)

                if to_play is not None:
                    to_play_header = utilities.parse_rtp_header(to_play)
                else:
                    continue
                
                # Extract body of audio packet
                final = to_play[12:1036]
                listen_stream.write(final)
                current_time = to_play_header["timestamp"]
                elapsed_time = current_time - previous_time

                if DEBUG == 1:
                    utilities.print_header(to_play_header, elapsed_time)

                previous_time = to_play_header["timestamp"]
                if call_session.call_end.is_set():
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
        user.client_socket.close()
        listen_stream.close()

    print("listen ending")
    

def send_transcription_message(call_session, user, message):
    """
    Transmits transcription messages to user on the other end of a communication link.
    Parameters
    ----------
    call_session : CallSession object
        Live call on the application
    user : User object
        User on the application
    message : String
        Text to be transmitted
    """
    current_time_ms = int(time.time() * 1000) % (1 << 32)
    rtp_header = utilities.create_rtp_header(call_session.get_sequence_number(), current_time_ms, call_session.ssrc, payload_type = 1)

    # Get ready to send packet
    data = json.dumps(message)
    encoded_data = data.encode('utf-8')
    packet = rtp_header + encoded_data
    srtp = call_session.tx_session.protect(packet) # Encrypt packet
    
    # Send to other user
    user.client_socket.sendto(srtp, (call_session.destination_ip, call_session.destination_port))


def start_audio_stream(user_input_device, user_output_device, audio):
    """
    Opens the input and output streams to allow for talking and listening.
    Parameters
    ----------
    user_input_device : Dictionary
        Device used as a microphone
    user_output_device : Dictionary
        Device used as speakers/headphones
    audio : pyAudio object
        Port audio
    Returns
    -------
    record_stream : Stream
        Stream to record
    listen_stream : Stream
        Stream to listen
    """
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