from threading import Event

current_user = ""

stop_transcription_event = Event()
stop_thread_event = Event()