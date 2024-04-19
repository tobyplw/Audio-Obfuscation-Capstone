import time
import threading
from threading import Thread
import socket
from threading import Event
from pylibsrtp import Policy, Session
import json
import queue
import time
import datetime
from googletrans import Translator
from tts import synthesize_text



translator = Translator()

class CallSession:
    # Handles the details and functionalities of a call session between two users.
    def __init__(self, caller, callee, on_transcribe_callback=None, on_mute_callback=None, on_unmute_callback=None, on_end_call=None):
        # Initialize a new call session with participant details and optional callbacks.
        self.caller = caller
        self.callee = callee
        # Network details
        self.destination_ip = ''
        self.destination_port = ''
        # Call status flags
        self.is_muted = False
        self.start_time = None
        self.end_time = None
        self.call_date = None
        self.duration = 0
        # Transcription and logging
        self.transcriptions = {}
        self.call_log = ""
        self.transcription_thread = None
        self.stop_transcription_event = Event()
        self.call_end = Event()
        # Audio data management
        self.audio_data = queue.Queue()
        self.transcription_queue = queue.Queue()
        self.obfuscation_queue = queue.Queue()
        # Callbacks
        self.update_transcription_textbox = on_transcribe_callback
        self.on_mute_callback = on_mute_callback
        self.on_unmute_callback = on_unmute_callback
        self.on_end_call = on_end_call
        # Security setup
        self.key =(b'\x00' * 30)
        self.tx_policy = Policy(key=self.key, ssrc_type=Policy.SSRC_ANY_OUTBOUND)
        self.tx_session = Session(policy=self.tx_policy)
        self.rx_policy = Policy(key=self.key, ssrc_type=Policy.SSRC_ANY_INBOUND)
        self.rx_session = Session(policy=self.rx_policy)
        # Sequence and SSRC management for RTP
        self.ssrc = 5678
        self.sequence_number = 0


    def init_deepgram(self, dg_connection):
        self.dg_connection = dg_connection
        
    def get_sequence_number(self):
        self.sequence_number +=1
        return self.sequence_number
# Function to manage the muting of the call
    def mute(self):
        # Mute the call and trigger the mute callback if set.
        self.is_muted = True
        if self.on_mute_callback:
            self.on_mute_callback()

    def unmute(self):
        # Unmute the call and trigger the unmute callback if set.
        self.is_muted = False
        if self.on_unmute_callback:
            self.on_unmute_callback()

    def end_call(self):
        # End the call, calculate duration, stop any active threads, and trigger the end call callback.
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
        self.transcription_thread = threading.Thread(target=self.transcribe, daemon=True)
        self.transcription_thread.start()

    # Decode and process the transcription data received over the network.
    def parse_transcription_message(self, data, user):
        decoded_data = data.decode('utf-8') # Convert bytes to string
        message = json.loads(decoded_data) # Parse string as JSON
        id = message['id'] # Unique identifier for the transcription message
        is_final = message['is_final'] # Boolean indicating if this is the final transcription
        text = message['text'] # Actual transcription text


        for key, words in text.items():
            id_speaker = str(id) + "." + str(key) # Create a unique speaker ID
            sentence = ""
            for word in words:
                sentence += " " + str(word) 
            if is_final:
                # Translate the sentence if it is the final version
                translation = translator.translate(sentence, dest=user.transcription_language)
                sentence = translation.text
                
            self.transcriptions[id_speaker] = sentence # Store the sentence

            if is_final:
                self.add_to_log({key: sentence}, external = True) # Log the sentence if final

        if (user.transcription_on.is_set()):
            # Update the transcription display if transcription is enabled
            self.update_transcription_textbox(self.print_transcriptions())



    def add_to_log(self, transcriptions, external):
        # Add transcriptions to the call log with a timestamp.
        for speaker, sentence in transcriptions.items():
            timestamp = time.time()
            date_object = datetime.datetime.fromtimestamp(timestamp)
            formatted_time = date_object.strftime("%m-%d-%Y %H:%M:%S")
            self.call_date = formatted_time # Update the call date
            self.call_log += "  {" + formatted_time+ "}" # Append the formatted timestamp
            if external:
                self.call_log += "[" + self.callee +" (Speaker " + str(speaker) + ")] "
                self.call_log += sentence
            else:
                self.call_log += "[" + self.caller +" (Speaker " + str(speaker) + ")] "
                for word in sentence:
                    self.call_log += word + " "

            self.call_log += "\n"
            


    def print_transcriptions(self):
        # Return the last six transcription entries as a formatted string.
        to_print = ""
        last_six_items = dict(list(self.transcriptions.items())[-6:]) # Get the last six items
        for id, sentence in last_six_items.items():
            speaker = id.split(".")[1] # Extract speaker identifier
            to_print += "[Speaker " + str(speaker) + "]"
            to_print+=sentence
            to_print+= "\n"
        
        return to_print


    # Start a new thread to listen for transcription messages.
    def start_transcription_listen_thread(self, user):
            listen_thread = Thread(
                target=self.transcription_listen_thread,
                args=(user,),
                daemon=True
            )
            listen_thread.start()
    

    def transcription_listen_thread(self, user):
        # Continuously listen for transcription messages until the call ends.
        while(not self.call_end.is_set()):
            try:
                message = self.transcription_queue.get(timeout = 10.0) # Try to get a message from the queue
                if message:
                    self.parse_transcription_message(message, user) # Process any message received
            except queue.Empty:
                continue  # Continue waiting if the queue is empty
            
    def call_duration(self):
        # Calculate and return the total call duration in a formatted string.
        total_seconds = int(self.end_time - self.start_time)
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours}h {minutes}m {seconds}s"

    
    def determine_TTS(self, message):
        # Determine the text to speech for the provided message and synthesize it.
        print("In Determine")
        text = ""
        for key, sentence in message.items():
            for word in sentence:
                text +=  word + " "
            synthesize_text(text, self) # Synthesize the combined text


    

class User:
    # Represents a user in the VoIP application, managing their session states and device settings.
    def __init__(self, username):
        # Initialize a new user with default properties.
        self.username = username
        self.input_device = None
        self.output_device = None
        self.is_muted = False
        self.obfuscation_on = Event()
        self.in_call = Event()
        self.tts_on = Event()
        self.current_call = None
        self.transcription_language = 'en'
        self.spoken_language = 'en'
        self.stop_transcription = Event()
        self.transcription_on = Event()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Assign a call session to the user and set the in-call flag.
    def start_call(self, call_session):
        self.in_call = True
        self.current_call = call_session
    # Clear the current call session and reset the in-call flag.
    def end_call(self):
        # End the current call session for the user.
        self.is_in_call = False
        self.current_call = None

    def set_input_device(self, device):
        # Set the input device for the user.
        self.input_device = device

    def set_output_device(self, device):
        # Set the output device for the user.
        self.output_device = device

    def set_transcription_language(self, language):
        # Set the transcription language for the user.
        self.transcription_language = language

    def set_spoken_language(self, language): 
        # Set the spoken language for the user.
        self.spoken_language = language

class Server:
    # Represents the server configuration and connection properties for the VoIP application.
    def __init__(self):
        # Initialize the server with fixed IP and port settings.
        self.server_host = '13.58.118.16'
        self.server_port = 12345
        self.poll_time = 1

    def get_server_host(self):
        # Return the server host IP.
        return self.server_host
    
    def get_server_port(self):
        # Return the server port number.
        return self.server_port