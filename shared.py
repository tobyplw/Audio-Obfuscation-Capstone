from threading import Event
import socket

current_user = ""
input_device = None
output_device = None
is_muted = False

stop_transcription_event = Event()
stop_thread_event = Event()
call_end = Event()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

SERVER_HOST = '13.58.118.16'
SERVER_PORT = 12345

obfuscation_on = False

#definitly need to hide this somehow
key = (b'\x00' * 30)

Poll_Time = 1