from vidstream import AudioSender
from vidstream import AudioReceiver

import threading
import socket

RECEIVER_HOST = '10.20.45.43'
REICEIVER_PORT = 2323
SENDER_HOST = '74.135.7.54'
SENDER_PORT = 9999

receiver = AudioReceiver(RECEIVER_HOST, REICEIVER_PORT)
receive_thread = threading.Thread(target=receiver.start_server)

sender = AudioSender(SENDER_HOST, SENDER_PORT)
sender_thread = threading.Thread(target=sender.start_stream)

receive_thread.start()
sender_thread.start()