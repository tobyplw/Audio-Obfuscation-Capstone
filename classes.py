import time
import threading
import socket
from threading import Event

class CallSession:
    def __init__(self, caller, callee, on_mute_callback=None, on_unmute_callback=None, on_end_call=None):
        self.caller = caller
        self.callee = callee
        self.is_muted = False
        self.start_time = time.time()
        self.duration = 0
        self.transcription = ""
        self.transcription_thread = None
        self.stop_transcription_event = Event()
        self.call_end = Event()
        # Callbacks
        self.on_mute_callback = on_mute_callback
        self.on_unmute_callback = on_unmute_callback
        self.on_end_call = on_end_call

    def mute(self):
        self.is_muted = True
        if self.on_mute_callback:
            self.on_mute_callback()

    def unmute(self):
        self.is_muted = False
        if self.on_unmute_callback:
            self.on_unmute_callback()

    def end_call(self):
        self.duration = time.time() - self.start_time
        # Stop transcription thread if it's running
        if self.transcription_thread is not None:
            self.stop_transcription_event.set()
            self.transcription_thread.join()  # Wait for the transcription thread to finish
        if self.on_end_call:
            self.on_end_call()

    def start_transcription(self):
        # Reset the stop event in case this is being reused
        self.stop_transcription_event.clear()
        # Initialize and start transcription thread
        self.transcription_thread = threading.Thread(target=self.transcribe)
        self.transcription_thread.start()

    def transcribe(self):
        while not self.stop_transcription_event.is_set():
            # Add transcription logic here
            # Update self.transcription as transcription progresses
            pass

class User:
    def __init__(self, username):
        self.username = username
        self.input_device = None
        self.output_device = None
        self.is_muted = False
        self.obfuscation_on = Event()
        self.in_call = Event()
        self.tts_on = Event()
        self.current_call = None
        self.transcription_language = 'English'
        self.spoken_language = 'English'
        self.stop_transcription = Event()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # def mute(self):
    #     self.is_muted = not self.is_muted
    #     return self.is_muted

    def start_call(self, call_session):
        self.in_call = True
        self.current_call = call_session

    def end_call(self):
        self.is_in_call = False
        self.current_call = None

    def set_input_device(self, device):
        self.input_device = device

    def set_output_device(self, device):
        self.output_device = device

    def set_transcription_language(self, language):
        self.transcription_language = language

    def set_spoken_language(self, language): 
        self.spoken_language = language

class Server:
    def __init__(self):
        self.server_host = '13.58.118.16'
        self.server_port = 12345
        self.poll_time = 1

    def get_server_host(self):
        return self.server_host
    
    def get_server_port(self):
        return self.server_port