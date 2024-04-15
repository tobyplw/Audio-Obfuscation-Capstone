import time
import threading
import socket
from threading import Event
from pylibsrtp import Policy, Session
import json
from queue import Queue
import time

class CallSession:
    def __init__(self, caller, callee, on_transcribe_callback=None, on_mute_callback=None, on_unmute_callback=None, on_end_call=None):
        self.caller = caller
        self.callee = callee
        self.destination_ip = ''
        self.destination_port = ''
        self.is_muted = False
        self.start_time = time.time()
        self.duration = 0
        self.transcriptions = {}
        self.call_log = ""
        self.transcription_thread = None
        self.stop_transcription_event = Event()
        self.call_end = Event()
        self.audio_data = Queue()
        # Callbacks
        self.update_transcription_textbox = on_transcribe_callback
        self.on_mute_callback = on_mute_callback
        self.on_unmute_callback = on_unmute_callback
        self.on_end_call = on_end_call
        self.key =(b'\x00' * 30)
        self.tx_policy = Policy(key=self.key, ssrc_type=Policy.SSRC_ANY_OUTBOUND)
        self.tx_session = Session(policy=self.tx_policy)
        self.rx_policy = Policy(key=self.key, ssrc_type=Policy.SSRC_ANY_INBOUND)
        self.rx_session = Session(policy=self.rx_policy)
        self.ssrc = 5678
        self.sequence_number = 0


    def init_deepgram(self, dg_connection):
        self.dg_connection = dg_connection
        
    def get_sequence_number(self):
        self.sequence_number +=1
        return self.sequence_number

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

    def parse_transcription_message(self, data, user):
        #print(data)
        decoded_data = data.decode('utf-8')
        message = json.loads(decoded_data)
        id = message['id']
        is_final = message['is_final']
        text = message['text']
        # if is_final:
        #     self.add_to_log(text)

        for key, value in text.items():
            id_speaker = str(id) + "." + str(key)
            self.transcriptions[id_speaker] = value
        
        if (user.transcription_on.is_set()):
            print(self.print_transcriptions())
            self.update_transcription_textbox(self.print_transcriptions())


        #print(message)
        #print("transcriptions below")
        #print(self.transcriptions)
        print(self.print_transcriptions())


    def add_to_log(self, text, external):
        for speaker, words in text.items():
            if external:
                self.call_log += "[External Speaker" + str(speaker) + "]"
            else:
                self.call_log += "[Speaker" + str(speaker) + "]"
            for word in words:
                self.call_log += " " + word
            self.call_log += "  {" + str(time.time()) + "}\n"


    def print_transcriptions(self):
        to_print = ""
        for id, words in self.transcriptions.items():
            speaker = id.split(".")[1]
            to_print += "[Speaker " + str(speaker) + "]"
            for word in words:
                to_print+= " " + word
            to_print+= "\n"
        
        return to_print
    

class User:
    def __init__(self, username):
        self.username = username
        self.input_device = None
        self.output_device = None
        self.is_muted = False
        self.obfuscation_on = Event()
        self.in_call = Event()
        self.current_call = None
        self.transcription_language = 'en'
        self.spoken_language = 'en'
        self.stop_transcription = Event()
        self.transcription_on = Event()
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