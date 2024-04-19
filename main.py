# Imports for front-end
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk, Toplevel  # Import messagebox for showing dialog messages
from PIL import Image # from tkinter import PhotoImage

# Imports for time
from datetime import datetime  # Import datetime to fetch the current time
import time

# Imports for main utilities
import threading
from threading import Thread
import pyaudio
import socket
import stun
import json
from googletrans import Translator
import pyperclip

# Imports from other files
import database
from stt import start_speech_to_text_transcription
import call
from call import get_user_input,get_user_output
from classes import User, CallSession, Server

# Create user, server, and call session objects
global user
user = User('')
global server
server = Server()
global call_session
call_session = CallSession('', '')
import time

# Dictionary for available spoken and transcribed languages
LANGUAGES = {
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
# Import the Translator class for language translation functionalities.
translator = Translator()
# Initialize global variables for tracking the last spoken words, and device mappings.
global last_words
last_words = ""
global input_device_name_to_info_mapping
input_device_name_to_info_mapping = {}

global output_device_name_to_info_mapping
output_device_name_to_info_mapping = {}

# Initialize global variables for audio streams and threading.
global input_stream, output_stream, audio, start_call_thread, listen_call_thread
input_stream = None
output_stream = None
audio = pyaudio.PyAudio() # Initialize the PyAudio object to manage audio.

global hang_up_button
hang_up_button = None
def check_NAT():
    # Attempt to determine the type of NAT used by making an STUN request.
    try:
        nat_type, external_ip, external_port = stun.get_ip_info()
        print("Nat Type: " + str(nat_type))
        # Warn if detected NAT type may hinder service functionality.
        if nat_type == "Symmetric NAT":
            print("NAT is Symmetric. This service may not work")
    except:
        # Silently ignore any exceptions that occur during the NAT check.
        pass

def get_internal_address():
    # Initially, try to obtain the internal IP and port from the client socket.
    internal_ip, internal_port = user.client_socket.getsockname()
    # Re-attempt obtaining the internal IP using hostname resolution for reliability.
    internal_ip = socket.gethostbyname(socket.gethostname()) #sometimes the first one gets the wrong internal ip or something
    return internal_ip, internal_port

def server_connection():
    # Start the process of connecting to an external server and continuously polling it.
    print("Connecting to external server...")
    check_NAT() # Check for any NAT issues that may affect connectivity.
    poll_time = 0
    # Retrieve and store the internal IP and port.
    internal_ip, internal_port = get_internal_address()
    while True:
        time.sleep(.5)
        curr_time = time.time()
        # Send a polling message to the server at the configured intervals.
        if curr_time > poll_time + server.poll_time:
            poll_time = curr_time
            message = {"Action" : "Poll", "From_Username" : user.username, "Internal_IP" : internal_ip, "Internal_Port" : internal_port, "Time" : time.time()}
            user.client_socket.sendto(json.dumps(message).encode(), (server.get_server_host(), server.get_server_port()))

def send_call_message(user_input):
    # Notify the user and send a call initiation message to the specified username.
    print("Calling ", user_input)
    message = {"Action" : "Calling","From_Username" : user.username, "To_Username" : user_input, "Time" : time.time()}
    user.client_socket.sendto(json.dumps(message).encode(), (server.get_server_host(), server.get_server_port()))

def recieve_messages():
    # Continuously listen for messages from the server while not in an active call.
    while True:
        time.sleep(0.1)
        if not user.in_call.is_set():
            data = None
            try:
                # Attempt to receive a message.
                data, server_address = user.client_socket.recvfrom(1024)
            except BlockingIOError:
                # Ignore blocking IO errors typically caused by non-blocking sockets.
                pass
            if data is not None:
                try:
                    # Decode and process the JSON message received.
                    inc_message = json.loads(data.decode())
                    print("Recieved message: " + str(inc_message))
                    action = inc_message["Action"]
                    # Determine the type of action and handle accordingly.
                    if action == "POKE":
                        callee_username = inc_message["From_Username"]
                        incoming_call_request(callee_username)
                    elif action == "ERROR":
                        callee_username = inc_message["To_Username"]
                        handle_error_message(callee_username)
                    elif action == "CALL": 
                        destination_ip = inc_message["Destination_IP"]
                        destination_port = inc_message["Destination_Port"]
                        callee_username = inc_message["From_Username"]
                        handle_call(destination_ip, destination_port, callee_username, user)
                        user.in_call.set()
                    elif action == "DECLINED":
                        callee_username = inc_message["To_Username"]
                        print(f"{callee_username} Declined Your Call")
                except UnicodeDecodeError as e: #this occurs for leftover packets from the audio stream
                    # Handle decode errors silently, typically caused by non-text data in the stream.
                    pass

def handle_error_message(callee_username):
    # add these messages to gui interface
    # print(f"There was an error contacting {callee_username}. Either does not exist or is not logged in.")
    # print("Try Again: Enter username you are trying to reach: ")
    pass

def handle_call(destination_ip, destination_port, callee_username, user):
    # Set up global variables to manage audio streams and threads for call operations.
    global input_stream, output_stream, start_call_thread, listen_call_thread
    # Initialize a new call session with empty IP and port which will be updated shortly.
    call_session = CallSession('', '')
    # Record the start time of the call.
    call_session.start_time = time.time()
    # Set the caller and callee usernames.
    call_session.caller = user.username
    call_session.callee = callee_username
    # Set the destination IP and port for the call.
    call_session.destination_ip = destination_ip
    call_session.destination_port = destination_port

    # Open a UI window to manage the call, showing details of the callee and session.
    open_call_window(callee_username, call_session)
    # Initialize audio streams for input and output using the user's device settings.
    input_stream, output_stream = call.start_audio_stream(user.input_device, user.output_device, audio)
    # Set up and start a thread for sending audio data.
    start_call_thread = threading.Thread(target=call.talk, args=(input_stream, user, call_session), daemon=True)
    # Set up and start a thread for receiving audio data.
    listen_call_thread = threading.Thread(target=call.listen, args=(output_stream, user, hang_up_button, call_session),daemon=True)
    # If transcription is enabled, set up and start a thread for speech-to-text transcription.
    transcription_send_thread = Thread(target=start_speech_to_text_transcription, args=(user.transcription_on, user, call_session),daemon=True)
    transcription_send_thread.start()
    # Begin monitoring and updating the call transcription if enabled.
    call_session.start_transcription_listen_thread(user)

    # Start the audio communication threads.
    start_call_thread.start()
    listen_call_thread.start()

def incoming_call_request(callee_username):
    #create box and wait for input
    call_from = callee_username
    # Display messagebox asking if user wants to accept the call
    accept_call = messagebox.askyesno("Incoming Call", f"Incoming call from {call_from}. \nAnswer it?")
    
    if accept_call:
        # User accepted the call
        print("Call accepted.")
        # Here goes accepting call logic
        message = {"Action" : "Accept", "From_Username" : user.username, "To_Username" : callee_username,  "Time" : time.time()}
        user.client_socket.sendto(json.dumps(message).encode(), (server.get_server_host(), server.get_server_port()))
        
    else:
        # User denied the call
        print("Call denied.")
        # Add logic for what happens when a call is denied
        message = {"Action" : "Decline", "From_Username" : user.username, "To_Username" : callee_username,  "Time" : time.time()}
        user.client_socket.sendto(json.dumps(message).encode(), (server.get_server_host(), server.get_server_port()))

def connect_with_server():
    # Configure the user's client socket for non-blocking network communication.
    user.client_socket.bind(('0.0.0.0', 0))
    user.client_socket.setblocking(0)
    # Set up and start threads for continuous server polling and message receiving.
    server_polling_thread = threading.Thread(target=server_connection,daemon=True)
    server_responding_thread = threading.Thread(target=recieve_messages,daemon=True)
    server_polling_thread.start()
    server_responding_thread.start()

# Initialize the main application window
app = ctk.CTk()
app.title('Ombra Audio Obfuscation Platform')
# Get screen width and height
screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()
app.geometry('700x700')
# app.attributes('-fullscreen', True)
app.iconbitmap('assets/NewLogo.ico')  # Set icon/logo
# To exit fullscreen with the Escape key
def exit_fullscreen(event=None):
    app.attributes('-fullscreen', False)

app.bind('<Escape>', exit_fullscreen)
# Configure the grid to expand the frame to fit the window
app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(0, weight=1)

# Function to update the clock
def update_clock():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")  # Format time in 24-hour format
    clock_label.configure(text=current_time)  # Use 'configure' instead of 'config'
    clock_label.after(1000, update_clock)  # Schedule the update_clock function to be called after 1000ms (1 second)

# Function to raise a frame to the top (make it visible)
def raise_frame(frame):
    frame.tkraise()

# Create frames for each page
log_in_frame = ctk.CTkFrame(app, fg_color= 'transparent')
sign_up_frame = ctk.CTkFrame(app)
main_frame = ctk.CTkFrame(app)
call_frame = ctk.CTkFrame(app)
logs_frame = ctk.CTkFrame(app)  # Frame for logs
settings_frame = ctk.CTkFrame(app)  # Create settings frame

# Loop through each frame involved in the UI to configure their layout properties uniformly.
for frame in (log_in_frame, sign_up_frame, main_frame, call_frame, logs_frame, settings_frame):
    # Place each frame in the same grid position, making them stack and switchable.
    frame.grid(row=0, column=0, sticky='nsew')

# Define clock font settings with the correct parameters for customtkinter
clock_font_family = "Helvetica"  # Font family
clock_font_size = 120  # Font size



# Main Frame Content

# Create a content frame within the main frame with a transparent background for visual appeal.
main_frame_content = ctk.CTkFrame(main_frame, fg_color='transparent')
# Pack the content frame with padding, allowing it to expand to fill space.
main_frame_content.pack(pady=20, padx=20, expand=True)

# Load the sponsor's logo image
logo_image = ctk.CTkImage(light_image=Image.open('assets/ombra-logo.png'), 
                          dark_image=Image.open('assets/ombra-logo-inverted.png'), 
                          size=(250,250))

# Display the logo image above the clock
logo_label = ctk.CTkLabel(main_frame_content, image=logo_image, text="")
logo_label.pack(pady=(10, 0))

# Clock Label
# clock_font = ("Helvetica", 24, "bold")
clock_label = ctk.CTkLabel(main_frame_content, text="", font=(clock_font_family, clock_font_size), bg_color="transparent")#, text_font_weight=clock_font_weight)
clock_label.pack(pady=(10, 20))  # Add some vertical padding for spacing
update_clock()  # Initialize clock update

# Buttons Frame for centering Start Call and Access Logs buttons
button_frame = ctk.CTkFrame(main_frame_content)
button_frame.pack(expand=True)

def on_start_call_button_clicked():
    raise_frame(call_frame)  # Show the call frame

# Create a 'Start Call' button within a predefined button frame, linking it to the event handler for click.
start_call_button = ctk.CTkButton(button_frame, text="Start Call", command=on_start_call_button_clicked, width=200, height=40)
start_call_button.pack(side='left', padx=10, pady=10, anchor='center')
# Create an 'Access Logs' button, also within the button frame, to switch to the logs frame when clicked.
access_logs_button = ctk.CTkButton(button_frame, text="Access Logs", command=lambda: raise_frame(logs_frame), width=200, height=40)
access_logs_button.pack(side='left', padx=10, pady=10, anchor='center')
# Create a 'Settings' button in the main content frame to navigate to the settings frame.
navigate_settings_button = ctk.CTkButton(main_frame_content, text="Settings", command=lambda: raise_frame(settings_frame), width=200, height=40, fg_color='grey', hover_color='#6f6e70')
navigate_settings_button.pack(pady=10)



# Settings Frame Content

# Add a label for settings on the settings frame, styled with a custom font.
settings_label = ctk.CTkLabel(settings_frame, text="Settings", font=(clock_font_family, 35))
settings_label.pack(pady=20)

# Define functions to switch between light and dark UI themes.
def switch_to_light_mode():
    ctk.set_appearance_mode('light')  # Set the appearance to light mode
    light_button.configure(text='Dark Mode', command=switch_to_dark_mode)  # Update button to switch to dark mode next

def switch_to_dark_mode():
    ctk.set_appearance_mode('dark')  # Set the appearance to dark mode
    light_button.configure(text='Light Mode', command=switch_to_light_mode)  # Update button to switch to light mode next

# Initialize the appearance toggle button with appropriate mode settings.
def initialize_button():
    global light_button
    light_button = ctk.CTkButton(settings_frame, text='Light Mode', command=switch_to_light_mode, width=200, height=40)
    light_button.pack(padx=10, pady=10)

    # Check and apply the initial appearance mode based on user settings or defaults.
    initial_mode = ctk.get_appearance_mode()
    if initial_mode == 'light':
        switch_to_light_mode()
    else:
        switch_to_dark_mode()
# Call the function to set up the theme toggle button on UI load.
initialize_button()
# Callback function definitions for handling input and output device selections.
def comboboxin_callback(choice):
    # If the selected device is mapped, update the user's input device preference and save settings.
    if choice in input_device_name_to_info_mapping:
        user.input_device = input_device_name_to_info_mapping[choice]
        database.save_settings(user.username, choice, user.output_device)
        print(f"Device selected: {user.input_device}")
    else:
        print("Selected device not found in mapping.")

def comboboxout_callback(choice):
    # Similar to input, update and save the output device preference if mapped.
    if choice in output_device_name_to_info_mapping:
        user.output_device = output_device_name_to_info_mapping[choice]
        database.save_settings(user.username, user.input_device, choice)
        print(f"Device selected: {user.output_device}")

# Add a label to the settings frame for user languages configuration.
translation_label = ctk.CTkLabel(settings_frame, text="User Languages:", font=("Arial", 22))
translation_label.pack(pady=(30,20) , padx=20)

# Update transcription language dropdown
def transcription_language_callback(choice):
    user.transcription_language = LANGUAGES[choice]
    print(f"Transcription language selected: {choice}")

# Create the button
translate_label = ctk.CTkLabel(settings_frame, text="Transcription Language:", font=("Arial", 15))
translate_label.pack(padx=20)
combobox_translation = ctk.CTkOptionMenu(settings_frame, values=list(LANGUAGES.keys()), command=transcription_language_callback, width=200)
combobox_translation.set("English")
combobox_translation.pack(pady=10)

# Update spoken language dropdown
def spoken_language_callback(choice):
    user.spoken_language = LANGUAGES[choice]
    print(f"Spoken language selected: {choice}")

# Create the button
spoken_label = ctk.CTkLabel(settings_frame, text="Spoken Language:", font=("Arial", 15))
spoken_label.pack(padx=20)
combobox_spoken = ctk.CTkOptionMenu(settings_frame, values=list(LANGUAGES.keys()), command=spoken_language_callback, width=200)
combobox_spoken.set("English")
combobox_spoken.pack(pady=10)

def update_input_devices_combobox():
    # Access global variables for combobox and device mapping.
    global comboboxin, device_name_to_info_mapping
    input_devices = get_user_input()
    device_names = [device['name'] for device in input_devices]  # Extract device names
    update_input_device_name_to_info_mapping(input_devices)  # Update the mapping

    # Destroy the existing combobox (if it exists)
    if 'comboboxin' in globals():
        comboboxin.destroy()

    # Recreate the combobox with the new values
    comboboxin = ctk.CTkOptionMenu(settings_frame, values=device_names, height=40, width=200, command=comboboxin_callback)
    output_label = ctk.CTkLabel(settings_frame, text="User Devices:", font=("Arial", 22))
    output_label.pack(pady=(30,20) , padx=20)
    input_label = ctk.CTkLabel(settings_frame, text="Input Device:", font=("Arial", 15))
    input_label.pack(padx=20)
    comboboxin.pack(pady=10)
    comboboxin.set(device_names[0])  # Optionally set a default value
    user.input_device = input_device_name_to_info_mapping[device_names[0]]

def update_output_devices_combobox():
    # Access global variables for combobox and device mapping.
    global comboboxout, output_device_name_to_info_mapping
    # Fetch the list of output devices.
    output_devices = get_user_output()
    device_names = [device['name'] for device in output_devices]  # Extract device names
    update_output_device_name_to_info_mapping(output_devices)  # Update the mapping

    # Destroy the existing combobox (if it exists)
    if 'comboboxout' in globals():
        comboboxout.destroy()

    # Recreate the combobox with the new values
    comboboxout = ctk.CTkOptionMenu(settings_frame, values=device_names, height=40, width=200, command=comboboxout_callback)
    output_label = ctk.CTkLabel(settings_frame, text="Output Device:", font=("Arial", 15))
    output_label.pack(padx=20)
    comboboxout.pack(pady=10)
    comboboxout.set(device_names[0])  # Optionally set a default value
    user.output_device = output_device_name_to_info_mapping[device_names[0]]
    # Back button in settings frame to return to main frame
    back_button_settings = ctk.CTkButton(settings_frame, text="Back to Main", command=lambda: raise_frame(main_frame))
    back_button_settings.pack(pady=20)

def update_input_device_name_to_info_mapping(devices):
    # Update the mapping dictionary for input devices with new data.
    global input_device_name_to_info_mapping
    for device in devices:
        input_device_name_to_info_mapping[device['name']] = device

def update_output_device_name_to_info_mapping(devices):
    # Update the mapping dictionary for output devices with new data.
    global output_device_name_to_info_mapping
    for device in devices:
        output_device_name_to_info_mapping[device['name']] = device



# Call Frame Content

call_label = ctk.CTkLabel(call_frame, text="Enter Callee's Username:", font=("Arial", 20, "bold"))
call_label.pack(pady=(30,20) , padx=20)

callee_id_entry = ctk.CTkEntry(call_frame)
callee_id_entry.pack(pady=10, padx=20)

# A function to configure and display the call window.
def open_call_window(callee_username, call_session):
    # Declare global to modify the hang-up button across function calls.
    global hang_up_button

    # Define a function to mute the user's microphone.
    def mute_on():
        user.is_muted = True
        mute_button.configure(fg_color='red')
        mute_button.configure(hover_color='red')
        mute_button.configure(image=mute_photo)
        mute_button.configure(command=mute_off)
    # Define a function to unmute the user's microphone.
    def mute_off():
        user.is_muted = False
        mute_button.configure(fg_color='white')
        mute_button.configure(hover_color='white')
        mute_button.configure(image=unmute_photo)
        mute_button.configure(command=mute_on)
    # Define a function to display a temporary message at the bottom of the call window.
    def show_message(message):
        obfuscate_display_label.configure(text=message)
        obfuscate_display_label.pack(side='bottom', fill='x', padx=10, pady=5)
    # Define a function to hide the temporary message from the call window.
    def hide_message():
        obfuscate_display_label.pack_forget()

    # Define a function to toggle voice obfuscation.
    def obfuscate_toggle():
        if user.obfuscation_on.is_set():
            # Configurations when turning off obfuscation
            obfuscate_button.configure(fg_color='blue', hover_color='#7D7D7D', image=obfuscate_photo)
            user.obfuscation_on.clear()
            show_message("Voice now obfuscated")  # Show this message while unobfuscated
        else:
            # Configurations when turning on obfuscation
            obfuscate_button.configure(fg_color='red', hover_color='#7D7D7D', image=unobfuscate_photo)
            user.obfuscation_on.set()
            show_message("Voice now unobfuscated")  # Show this message while obfuscated

    # Define a function to toggle the transcription feature on and off.
    def transcribe_toggle():
        if user.transcription_on.is_set():
            user.transcription_on.clear()
        else:
            user.transcription_on.set()
    # Define a function to toggle the text-to-speech feature.
    def tts_toggle():
        if user.tts_on.is_set():
            user.tts_on.clear()
        else:
            user.tts_on.set()

    # Initialize the call window.
    call_window = Toplevel(app)
    call_window.title("Call")
    call_window.geometry("1400x740")
    call_window.configure(bg="#333333")  # Light gray background
    # Initialize a label to display obfuscation status, initially hidden.
    obfuscate_display_label = ctk.CTkLabel(call_window, text="", height=20)  # main_frame should be your main GUI frame
    obfuscate_display_label.pack_forget()  # Start with the label hidden
    # Create and configure a text box for transcription display.
    transcribe_textbox = ctk.CTkTextbox(call_window, height=200, width=500)
    transcribe_textbox.pack(pady=10, padx=20, expand=True, fill='both')
    transcribe_textbox.configure(state= "disabled")

    # A function to update the text displayed in the transcription textbox.
    def update_transcribe_textbox(text):
        def callback():
            transcribe_textbox.configure(state="normal")
            transcribe_textbox.delete('1.0', 'end')
            transcribe_textbox.insert(tk.END, text + '\n')
            transcribe_textbox.see(tk.END)
            transcribe_textbox.configure(state="disabled")
            
        app.after(0, callback)

    call_session.update_transcription_textbox = update_transcribe_textbox

    # Layout and configuration of buttons for various call functions is handled below.
    # Images are loaded, buttons are created with these images, and packed into the UI.
    pfp_image = Image.open("assets/pfp.png")
    pfp_photo = ctk.CTkImage(pfp_image, size=(200,200))
    pfp_label = ctk.CTkLabel(call_window, image = pfp_photo, text="")
    pfp_label.pack(pady=(100,20))

    user_label = ctk.CTkLabel(call_window, text=callee_username, font=("Roboto", 30))
    user_label.pack()
    # Frame for all the buttons in call window
    buttons_frame = ctk.CTkFrame(call_window, fg_color="transparent")
    buttons_frame.pack(side='bottom', pady=40)

    hang_up_image = Image.open("assets/hangup.png")
    # resized_image = hang_up_image.resize((40, 40), Image.ANTIALIAS)

    # Convert to PhotoImage
    hang_up_photo = ctk.CTkImage(hang_up_image, size=(40,40))

    # Now create the button with the image
    hang_up_button = ctk.CTkButton(buttons_frame, 
                                   image=hang_up_photo, 
                                   text="", 
                                   height=40, 
                                   width=40, 
                                   corner_radius=40, 
                                   fg_color="red", 
                                   hover_color="#d3d3d3",
                                   command=lambda: hang_up_call(call_window, call_session))
    # hang_up_button.image = hang_up_photo  # Keep a reference to avoid garbage collection
    # hang_up_button.pack(side="left", padx=10)

    mute_image = Image.open("assets/muteicon.png")

    mute_photo = ctk.CTkImage(mute_image, size=(40,40))

    unmute_image = Image.open("assets/unmuteicon.png")

    unmute_photo = ctk.CTkImage(unmute_image, size=(40,40))

    mute_button = ctk.CTkButton(buttons_frame, 
                                image=unmute_photo, 
                                text="", 
                                height=40, 
                                width=40, 
                                corner_radius=40, 
                                fg_color="white",
                                hover_color='white', 
                                command=mute_on)
    # mute_button.pack(side="right", padx=10)
    
    obfuscate_image = Image.open("assets/obfuscate.png")

    obfuscate_photo = ctk.CTkImage(obfuscate_image, size=(40,40))

    unobfuscate_image = Image.open("assets/unobfuscate.png")

    unobfuscate_photo = ctk.CTkImage(unobfuscate_image, size=(40,40))

    obfuscate_button = ctk.CTkButton(buttons_frame, 
                                image=obfuscate_photo, 
                                text="", 
                                height=40, 
                                width=40, 
                                corner_radius=40, 
                                fg_color='blue', 
                                command=obfuscate_toggle)
    # obfuscate_button.pack(side="left", padx=10)
    
    transcribe_image = Image.open("assets/transcribe.png")

    transcribe_photo = ctk.CTkImage(transcribe_image, size=(40,40))

    transcribe_button = ctk.CTkButton(buttons_frame, 
                                image=transcribe_photo, 
                                text="", 
                                height=40, 
                                width=40, 
                                corner_radius=40, 
                                fg_color="white", 
                                command=transcribe_toggle)
    
    tts_image = Image.open("assets/tts.png")

    tts_photo = ctk.CTkImage(tts_image, size=(40,40))
    
    tts_button = ctk.CTkButton(buttons_frame, 
                                image=tts_photo, 
                                text="", 
                                height=40, 
                                width=40, 
                                corner_radius=40, 
                                fg_color="white", 
                                command=tts_toggle)
    # Pack all of the buttons created above
    # Transcribe Button
    transcribe_button.pack(side="right", padx=25)
    # Text-To-Speech Button
    tts_button.pack(side="right", padx=25)
    # Obfuscate Button
    obfuscate_button.pack(side="right", padx=25)
    # Mute Button
    mute_button.pack(side="left", padx=25)
    # Hang Up Button
    hang_up_button.pack(side="left", padx=25)

def mute_call():
    # Logic to mute the call
    print('Mic has been muted.')
    pass

def hang_up_call(window, call_session):
    global input_stream, output_stream, audio, start_call_thread, listen_call_thread
    # Signal that the call has ended.
    call_session.call_end.set()
    # Join threads handling the call.
    #listen_call_thread.join()
    start_call_thread.join()
    # Close the input stream if it exists.
    if input_stream is not None:
        input_stream.stop_stream()
        input_stream.close()
        print("input stream closed")
     # Close the output stream if it exists.
    if output_stream is not None:
        output_stream.stop_stream()
        output_stream.close()
        print("output stream closed")

    # Log the call details to the database.
    call_session.end_time = time.time()
    print(call_session.call_log)
    database.log_call(call_session.caller, call_session.callee, call_session.call_date, call_session.call_log)

    # Reset call session settings.
    call_session.call_end.clear()
    user.in_call.clear()
    window.destroy() # Close the call window.

# Modified call_user function to include hiding and showing the Start Recording button
def call_user():
    callee_id = callee_id_entry.get()  # Get the value from the entry field
    # print(f"Calling User with ID: {callee_id}")  # Placeholder for actual call functionality
    messagebox.showinfo("Call Authenticated", f"Calling User with ID: {callee_id}")  # Show a dialog box as feedback
    send_call_message(callee_id)

call_button = ctk.CTkButton(call_frame, text="Call", fg_color='green', command=call_user)
call_button.pack(pady=10, padx=20)

contact_label = ctk.CTkLabel(call_frame, text="Your Contacts:", font=("Arial", 20, "bold"))
contact_label.pack(pady=(30,20) , padx=20)

# Frame for the search box and button
search_frame = ctk.CTkFrame(call_frame, fg_color='transparent')
search_frame.pack(padx=10, pady=5)
# search_frame.grid_columnconfigure((0, 1), weight=1)  # Make username and nickname entries expand equally

# Entry for adding a new username
new_username_entry = ctk.CTkEntry(search_frame, placeholder_text="Enter username")
new_username_entry.pack(side='left', padx=5)

# Entry for adding a new nickname
new_nickname_entry = ctk.CTkEntry(search_frame, placeholder_text="Enter alias")
new_nickname_entry.pack(side='left', padx=5)

def handle_add_contact():
    # Fetch user input for a new contact.
    username = new_username_entry.get().strip()
    nickname = new_nickname_entry.get().strip()
    if username and nickname:
        # Add the new contact to the database
        database.add_contact(user.username, username, nickname)
        
        # Refresh the contacts display
        update_contacts_display()
        
        # Clear the input fields
        new_username_entry.delete(0, 'end')
        new_nickname_entry.delete(0, 'end')
    else:
        # Alert the user if necessary information is missing.
        messagebox.showwarning("Missing Information", "Please enter BOTH a username and an alias.")


def update_contacts_display(filtered_contacts=None):
    # Clear existing contact widgets.
    for widget in scrollable_contacts_frame.winfo_children():
        widget.destroy()

    # Fetch contacts from the database
    if filtered_contacts is None:
        filtered_contacts = database.get_contacts(user.username)
    # Display each contact in the scrollable frame.
    for contact in filtered_contacts:
        display_name = contact.get("username")  # Adjust field names based on your database schema
        nickname = contact.get("nickname")
        contact_label = ctk.CTkLabel(scrollable_contacts_frame, text=display_name)
        contact_label.pack(pady=2, anchor='w')
        # Bind mouse events to show and hide nicknames, and handle clicking on the contact.
        contact_label.bind("<Enter>", lambda event, nickname=nickname: show_nickname(event, nickname))
        contact_label.bind("<Leave>", hide_nickname)
        contact_label.bind("<Button-1>", lambda event, username=display_name: callee_id_entry.delete(0, tk.END) or callee_id_entry.insert(0, username))

# Button to trigger adding a new contact
add_contact_button = ctk.CTkButton(search_frame, text="Add Contact", command=handle_add_contact, width=50)
add_contact_button.pack(side='left', padx=10)

# Scrollable Frame for displaying contacts
scrollable_contacts_frame = ctk.CTkScrollableFrame(call_frame, width=380, height=200, corner_radius=10)
scrollable_contacts_frame.pack(pady=10, padx=10)

# Display nickname on hover label
nickname_display_label = ctk.CTkLabel(call_frame, text="", height=20)
nickname_display_label.pack(side='bottom', fill='x', padx=10, pady=5)
nickname_display_label.pack_forget()  # Initially, hide the label

def show_nickname(event, nickname):
    # Display nickname/ alias in a label.
    nickname_display_label.configure(text=f"Alias: {nickname}")
    nickname_display_label.pack(side='bottom', fill='x', padx=10, pady=5)

def hide_nickname(event):
    # Hide the nickname label.
    nickname_display_label.pack_forget()
    pass

def copy_to_clipboard(username):
    # Copy the selected username to the clipboard.
    pyperclip.copy(username)
    print(f"Copied to clipboard: {username}")

back_button_call = ctk.CTkButton(call_frame, text="Back to Main", command=lambda: raise_frame(main_frame))
back_button_call.pack(pady=20, padx=20)



# Logs Frame Content - Placeholder content for now

logs_label = ctk.CTkLabel(logs_frame, text="Call Logs", font=(clock_font_family, 35))
logs_label.pack(pady=20, padx=20)
# Include button to take user back to main 
back_button_logs = ctk.CTkButton(logs_frame, text="Back to Main", command=lambda: raise_frame(main_frame))
back_button_logs.pack(pady=20, padx=20)

def open_transcript_window(transcript):
    # This function creates a window to display the call transcript.
    transcript_window = Toplevel(app)
    transcript_window.title("Call Transcript")
    transcript_window.geometry("500x300")  # Set a reasonable size for the transcript window

    transcript_text = tk.Text(transcript_window, wrap='word', height=15)
    transcript_text.pack(padx=10, pady=10, fill='both', expand=True)

    transcript_text.insert('end', transcript)
    transcript_text.config(state='disabled')  # Make the text widget read-only

    # Add a scrollbar
    scrollbar = ttk.Scrollbar(transcript_window, command=transcript_text.yview)
    scrollbar.pack(side='right', fill='y')
    transcript_text.config(yscrollcommand=scrollbar.set)

# Set this up to be window so that its not hardcoded
def setup_logs_frame(username):
    # Sets up the logs frame with a table to display call logs.
    logs_table = ttk.Treeview(logs_frame, height=10)
    logs_table.pack(expand=True, fill='both', side='top')

    # Define and format the columns
    logs_table['columns'] = ('callID', 'callDate', 'caller', 'callee', 'call_transcript')
    logs_table.column("#0", width=0, stretch=tk.NO)
    logs_table.column("callID", anchor=tk.W, width=40)
    logs_table.column("callDate", anchor=tk.W, width=120)
    logs_table.column("caller", anchor=tk.W, width=120)
    logs_table.column("callee", anchor=tk.W, width=120)
    logs_table.column("call_transcript", anchor=tk.W, width=400)

    # Create Headings
    logs_table.heading("#0", text="", anchor=tk.W)
    logs_table.heading("callID", text="Call ID", anchor=tk.W)
    logs_table.heading("callDate", text="Call Date", anchor=tk.W)
    logs_table.heading("caller", text="Caller", anchor=tk.W)
    logs_table.heading("callee", text="Callee", anchor=tk.W)
    logs_table.heading("call_transcript", text="Call Recording", anchor=tk.W)

    # Fetch the call logs from the database
    call_logs = database.get_calls(username)

    # Create a dictionary to store transcripts for later access
    transcripts_dict = {}

    for call_log in call_logs:
        logs_table.insert("", 'end', iid=call_log[0], text="", values=(
            call_log[0],  # Call ID
            call_log[1],  # Caller
            call_log[2],  # Callee
            call_log[3],  # Formatting date as string
            "Click to view transcript"  # Placeholder text*
        ))
        transcripts_dict[call_log[0]] = call_log[4]  # Store actual transcript

    # Define an event handler for row clicks that opens the transcript window
    def on_row_click(event):
        item_id = logs_table.selection()[0]
        transcript = transcripts_dict[item_id]  # Fetch the actual transcript from the dictionary
        open_transcript_window(transcript)

    logs_table.bind("<Double-1>", on_row_click)


# Function to handle the sign-in process (placeholder for actual functionality)
def sign_in():
    # Process user credentials and transition to the main interface.
    username = username_entry.get()
    password = password_entry.get()
    update_input_devices_combobox()  # Update the devices combobox
    update_output_devices_combobox()
    if(database.login(username, password)):
        user.username = username
        connect_with_server() # Connect to the server if login is successful.

        raise_frame(main_frame) # Change UI to the main frame.
        setup_logs_frame(username) # Setup the logs frame with user-specific logs.
        update_contacts_display() # Update the displayed contacts.

    else:
        # Inform the user if login fails.
        messagebox.showinfo("Login Attempt Failed", "The username or password you entered is incorrect.")
        password_entry.delete(0, tk.END)
    
def sign_up():
     # Registers a new user if passwords match.
    username = username_entry_signup.get()
    password = password_entry_signup.get()
    verify_password = confirm_password_entry.get()

    if (password == verify_password):
        database.create_user(username, password)
        raise_frame(log_in_frame) # Return to the login frame after successful signup.
    else:
        # Inform the user if the passwords do not match.
        messagebox.showinfo("Signup Attempt", f"Passwords do not match\nPlease try again")

# Setting up the log_in_frame
log_in_frame_content = ctk.CTkFrame(log_in_frame,fg_color='transparent')
log_in_frame_content.pack(pady=20, padx=20, expand=True)

welcome = ctk.CTkLabel(log_in_frame_content, text="Login To Your Account\n", font=('Helvetica', 36), fg_color='transparent')
welcome.pack()

# Load the image
login_image = ctk.CTkImage(light_image=Image.open('assets/login.png'), 
                           dark_image=Image.open('assets/login.png'), 
                           size=(230,230))

# Create a frame for the image and place it to the left
image_frame = ctk.CTkFrame(log_in_frame_content, fg_color='transparent', width=50, height=50)  # Adjust size as needed
image_frame.pack(side='left', fill='both', expand=True)
# image_frame.pack_propagate(True)  # Prevent the frame from shrinking to fit the image

# Display the image using a label inside the image_frame
image_label = ctk.CTkLabel(image_frame, image=login_image, text="", width=20, height=20)
image_label.pack(padx=(0,40))

# Create a frame for the login boxes and place it to the right
login_boxes_frame = ctk.CTkFrame(log_in_frame_content, fg_color='transparent')
login_boxes_frame.pack(side='right', fill='both', expand=True)

# Username Entry
username_label = ctk.CTkLabel(log_in_frame_content, text="Username:")
# username_label.pack(pady=(10,0))
username_entry = ctk.CTkEntry(log_in_frame_content, placeholder_text="Username")
# username_entry.pack(pady=(0,20))

# Password Entry
password_label = ctk.CTkLabel(log_in_frame_content, text="Password:")
# password_label.pack(pady=(10,0))
password_entry = ctk.CTkEntry(log_in_frame_content, placeholder_text="Password", show="*")
# password_entry.pack(pady=(0,20))

password_entry.bind("<Return>", lambda event=None: sign_in())

# Sign In Button
sign_in_button = ctk.CTkButton(log_in_frame_content, text="Sign In", command=sign_in)
# sign_in_button.pack(pady=20)

# "Sign Up" button on the login page
sign_up_button = ctk.CTkButton(log_in_frame_content, text="Create Account", command=lambda: raise_frame(sign_up_frame))
# sign_up_button.pack(pady=(10, 0))

# username_label.pack(in_=login_boxes_frame, pady=(30,0))
username_entry.pack(in_=login_boxes_frame, pady=(20,0))
# password_label.pack(in_=login_boxes_frame, pady=(0,0))
password_entry.pack(in_=login_boxes_frame, pady=(20,30))
sign_in_button.pack(in_=login_boxes_frame)
sign_up_button.pack(in_=login_boxes_frame, pady=(30, 0))



# Sign Up Frame Content

sign_up_frame_content = ctk.CTkFrame(sign_up_frame, fg_color='transparent')
sign_up_frame_content.pack(pady=20, padx=20, expand=True)

# Username Entry (Reused from login)
username_label_signup = ctk.CTkLabel(sign_up_frame_content, text="Username:")
username_label_signup.pack(pady=(10, 5))
username_entry_signup = ctk.CTkEntry(sign_up_frame_content)
username_entry_signup.pack(pady=5)

# Password Entry
password_label_signup = ctk.CTkLabel(sign_up_frame_content, text="Password:")
password_label_signup.pack(pady=(10, 5))
password_entry_signup = ctk.CTkEntry(sign_up_frame_content, show="*")
password_entry_signup.pack(pady=5)

# Confirm Password Entry
confirm_password_label = ctk.CTkLabel(sign_up_frame_content, text="Confirm Password:")
confirm_password_label.pack(pady=(10, 5))
confirm_password_entry = ctk.CTkEntry(sign_up_frame_content, show="*")
confirm_password_entry.pack(pady=(5, 20))

# Placeholder for the actual sign-up button functionality
sign_up_confirm_button = ctk.CTkButton(sign_up_frame_content, text="Create Account", command=sign_up) # Implement functionality later
sign_up_confirm_button.pack(pady=10)

# Button to go back to the login page
back_to_login_button = ctk.CTkButton(sign_up_frame_content, text="Back to Login", command=lambda: raise_frame(log_in_frame))
back_to_login_button.pack(pady=10)

def on_close():
    # Function to handle the application close event, ensuring all resources are properly released.
    global input_stream, output_stream, audio
    # Check if there is an active input stream and stop and close it if it exists.
    if input_stream is not None:
        input_stream.stop_stream()
        input_stream.close()
        # Check if there is an active output stream and stop and close it if it exists.
    if output_stream is not None:
        output_stream.stop_stream()
        output_stream.close()
        # Check if the PyAudio instance is active and terminate it if it exists.
    if audio is not None:
        audio.terminate()
        # Finally, destroy the application window to close the application completely.
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_close)

# raise_frame(main_frame)
# Initially, show the main frame
raise_frame(log_in_frame)
# Start main app
app.mainloop()