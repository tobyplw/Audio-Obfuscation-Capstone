from threading import Event
import socket

current_user = ""
input_device = None
output_device = None
is_muted = False
transcription_language = 'english'
spoken_language = 'english'

stop_transcription_event = Event()
stop_thread_event = Event()
call_end = Event()
in_call = Event()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

SERVER_HOST = '13.58.118.16'
SERVER_PORT = 12345

obfuscation_on = Event()

#definitly need to hide this somehow
key = (b'\x00' * 30)

Poll_Time = 1

languages = {
    'Czech' : 'cs',
    'Danish' : 'da',
    'Dutch' : 'nl',
    'English' : 'en',
    'French' : 'fr',
    'German' : 'de',
    'Greek' : 'el',
    'Hindi' : 'hi',
    'Indonesian' : 'id',
    'Italian' : 'it',
    'Japanese' : 'ja',
    'Korean' : 'ko',
    'Malay' : 'ms',
    'Norwegian' : 'no',
    'Polish' : 'pl',
    'Portuguese' : 'pt',
    'Russian' : 'ru',
    'Spanish' : 'es',
    'Swedish' : 'sv',
    'Turkish' : 'tr',
    'Ukrainian' : 'uk',
    'Vietnamese' : 'vi'
}