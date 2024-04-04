# Author: Shafin Alam

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

translator = Translator()

global last_words
last_words = ""
global input_device_name_to_info_mapping
input_device_name_to_info_mapping = {}

global output_device_name_to_info_mapping
output_device_name_to_info_mapping = {}

global input_stream, output_stream, audio, start_call_thread, listen_call_thread
input_stream = None
output_stream = None
audio = pyaudio.PyAudio()

global hang_up_button
hang_up_button = None
def check_NAT():
    try:
        nat_type, external_ip, external_port = stun.get_ip_info()
        print("Nat Type: " + str(nat_type))
        if nat_type == "Symmetric NAT":
            print("NAT is Symmetric. This service may not work")
    except:
        pass

def get_internal_address():
    internal_ip, internal_port = user.client_socket.getsockname()
    internal_ip = socket.gethostbyname(socket.gethostname()) #sometimes the first one gets the wrong internal ip or something
    return internal_ip, internal_port

def server_connection():
    print("Connecting to external server...")
    check_NAT()
    poll_time = 0
    internal_ip, internal_port = get_internal_address()
    while True:
        time.sleep(.5)
        curr_time = time.time()
        if curr_time > poll_time + server.poll_time:
            poll_time = curr_time
            message = {"Action" : "Poll", "From_Username" : user.username, "Internal_IP" : internal_ip, "Internal_Port" : internal_port, "Time" : time.time()}
            user.client_socket.sendto(json.dumps(message).encode(), (server.get_server_host(), server.get_server_port()))


def send_call_message(user_input):
    print("Calling ", user_input)
    message = {"Action" : "Calling","From_Username" : user.username, "To_Username" : user_input, "Time" : time.time()}
    user.client_socket.sendto(json.dumps(message).encode(), (server.get_server_host(), server.get_server_port()))


def recieve_messages():
    while True:
        time.sleep(0.1)
        if not user.in_call.is_set():
            data = None
            try:
                data, server_address = user.client_socket.recvfrom(1024)
            except BlockingIOError:
                pass
            if data is not None:
                try:
                    inc_message = json.loads(data.decode())
                    print("Recieved message: " + str(inc_message))
                    action = inc_message["Action"]

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
                        handle_call(destination_ip,destination_port, callee_username, user)
                        user.in_call.set()
                    elif action == "DECLINED":
                        callee_username = inc_message["To_Username"]
                        print(f"{callee_username} Declined Your Call")
                except UnicodeDecodeError as e: #this occurs for leftover packets from the audio stream
                    pass


def handle_error_message(callee_username):
    # add these messages to gui interface
    # print(f"There was an error contacting {callee_username}. Either does not exist or is not logged in.")
    # print("Try Again: Enter username you are trying to reach: ")
    pass

def handle_call(destination_ip,destination_port, callee_username):
    global input_stream, output_stream, start_call_thread, listen_call_thread
    call_session.caller = user.username
    call_session.callee = callee_username

    open_call_window(user.username)
    input_stream, output_stream = call.start_audio_stream(user.input_device, user.output_device, audio)
    start_call_thread = threading.Thread(target=call.talk, args=(user.client_socket, input_stream,callee_username, destination_ip, destination_port, user, call_session), daemon=True)
    listen_call_thread = threading.Thread(target=call.listen, args=(user.client_socket, output_stream, hang_up_button, call_session),daemon=True)
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
    user.client_socket.bind(('0.0.0.0', 0))
    user.client_socket.setblocking(0)
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

# Function to simulate starting the recording (placeholder for actual functionality)
def start_recording():
    # print("Recording started...")  # Placeholder print statement
    messagebox.showinfo("Call Authenticated", f"Recording In Progress")
    # Implement the actual recording functionality later
    # Optional: Show a dialog box as feedback

# Create frames for each page
log_in_frame = ctk.CTkFrame(app, fg_color= 'transparent')
sign_up_frame = ctk.CTkFrame(app)
main_frame = ctk.CTkFrame(app)
call_frame = ctk.CTkFrame(app)
logs_frame = ctk.CTkFrame(app)  # Frame for logs
transcribe_frame = ctk.CTkFrame(app)


for frame in (log_in_frame, sign_up_frame, main_frame, call_frame, logs_frame, transcribe_frame):
    frame.grid(row=0, column=0, sticky='nsew')

# Define clock font settings with the correct parameters for customtkinter
clock_font_family = "Helvetica"  # Font family
clock_font_size = 120  # Font size
# clock_font_weight = "bold"  # Font weight

# Main Frame Content - Adjust layout for clock and buttons
main_frame_content = ctk.CTkFrame(main_frame, fg_color='transparent')
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
    update_input_devices_combobox()  # Update the devices combobox
    update_output_devices_combobox()


start_call_button = ctk.CTkButton(button_frame, text="Start Call", command=on_start_call_button_clicked, width=200, height=40)
start_call_button.pack(side='left', padx=10, pady=10, anchor='center')

access_logs_button = ctk.CTkButton(button_frame, text="Access Logs", command=lambda: raise_frame(logs_frame), width=200, height=40)
access_logs_button.pack(side='left', padx=10, pady=10, anchor='center')

transcribe_button = ctk.CTkButton(button_frame, text="Transcribe", command=lambda: raise_frame(transcribe_frame), width=200, height=40)
transcribe_button.pack(side='left', padx=10, pady=10, anchor='center')


button = ctk.CTkButton(button_frame, text='Light', command = lambda: ctk.set_appearance_mode('light'), width=200, height=40)
button.pack(side='left', padx=10, pady=10, anchor='center')


def sign_out():
    username_entry.delete(0, tk.END)
    password_entry.delete(0, tk.END)

    raise_frame(log_in_frame)

# Update the command for the sign_out_button to use the sign_out function
sign_out_button = ctk.CTkButton(main_frame_content, text="Sign Out", command=sign_out)
sign_out_button.pack(pady=(10, 20), padx=20, anchor='e')


# Call Frame Content



call_label = ctk.CTkLabel(call_frame, text="Enter Callee's Username:")
call_label.pack(pady=(30,20) , padx=20)

callee_id_entry = ctk.CTkEntry(call_frame)
callee_id_entry.pack(pady=10, padx=20)

def open_call_window(username):
    global hang_up_button
    def mute_on():
        user.is_muted = True
        mute_button.configure(fg_color='red')
        mute_button.configure(hover_color='red')
        mute_button.configure(image=mute_photo)
        mute_button.configure(command=mute_off)
    def mute_off():
        user.is_muted = False
        mute_button.configure(fg_color='white')
        mute_button.configure(hover_color='white')
        mute_button.configure(image=unmute_photo)
        mute_button.configure(command=mute_on)

    def obfuscate_toggle():
        if user.obfuscation_on.is_set():
            user.obfuscation_on.clear()
        else:
            user.obfuscation_on.set()

    call_window = Toplevel(app)
    call_window.title("Call")
    call_window.geometry("1400x700")
    call_window.configure(bg="#333333")  # Light gray background

    pfp_image = Image.open("assets/pfp.png")
    pfp_photo = ctk.CTkImage(pfp_image, size=(200,200))
    pfp_label = ctk.CTkLabel(call_window, image = pfp_photo, text="")
    pfp_label.pack(pady=(100,20))

    user_label = ctk.CTkLabel(call_window, text=username, font=("Roboto", 30))
    user_label.pack()

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
                                   command=lambda: hang_up_call(call_window))
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

    obfuscate_button = ctk.CTkButton(buttons_frame, 
                                image=obfuscate_photo, 
                                text="", 
                                height=40, 
                                width=40, 
                                corner_radius=40, 
                                fg_color="white", 
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
                                command=mute_call)
    transcribe_button.pack(side="right", padx=25)
    obfuscate_button.pack(side="right", padx=25)
    mute_button.pack(side="left", padx=25)
    hang_up_button.pack(side="left", padx=25)

    # test_button = ctk.CTkButton(call_window, text="")
    # test_button.pack(side='bottom')

    # You will need to define mute_call() and hang_up_call(window) functions to handle the logic
    # for muting/unmuting the call and hanging up respectively.

def mute_call():
    # Logic to mute the call
    print('Mic has been muted.')
    pass

def hang_up_call(window):
    global input_stream, output_stream, audio, start_call_thread, listen_call_thread
    call_session.call_end.set()
    #listen_call_thread.join()
    start_call_thread.join()

    if input_stream is not None:
        input_stream.stop_stream()
        input_stream.close()
        print("input stream closed")
    if output_stream is not None:
        output_stream.stop_stream()
        output_stream.close()
        print("output stream closed")

    call_session.call_end.clear()
    user.in_call.clear()
    window.destroy()

# Modified call_user function to include hiding and showing the Start Recording button
def call_user():
    callee_id = callee_id_entry.get()  # Get the value from the entry field
    # print(f"Calling User with ID: {callee_id}")  # Placeholder for actual call functionality
    messagebox.showinfo("Call Authenticated", f"Calling User with ID: {callee_id}")  # Show a dialog box as feedback
    send_call_message(callee_id)
    start_recording_button.pack(before=back_button_call, pady=10, padx=20)  # Adjusted to pack before the Back button


call_button = ctk.CTkButton(call_frame, text="Call", command=call_user)
call_button.pack(pady=10, padx=20)

# test_button2 = ctk.CTkButton(call_frame, text="Receive Call", command=receive_call)
# test_button2.pack(pady=20)

def comboboxin_callback(choice):
    # Assuming `shared.py` has been imported as `shared`
    if choice in input_device_name_to_info_mapping:
        user.input_device = input_device_name_to_info_mapping[choice]
        print(f"Device selected: {user.input_device}")
    else:
        print("Selected device not found in mapping.")

comboboxin = ctk.CTkOptionMenu(call_frame, values=[], command=comboboxin_callback, width=200)
# combobox.grid(row=0, column=0, padx=20, pady=10)

comboboxin.set("Select Input")  # set initial value
comboboxin.pack(pady=10)

def comboboxout_callback(choice):
    # Assuming `shared.py` has been imported as `shared`
    if choice in output_device_name_to_info_mapping:
        user.output_device  = output_device_name_to_info_mapping[choice]
        print(f"Device selected: {user.output_device} ")
    else:
        print("Selected device not found in mapping.")

comboboxout = ctk.CTkOptionMenu(call_frame, values=[], command=comboboxout_callback, width=200)
# combobox.grid(row=0, column=0, padx=20, pady=10)

comboboxout.set("Select Output")  # set initial value
comboboxout.pack(pady=10)

# Update transcription language dropdown
def transcription_language_callback(choice):
    user.transcription_language = LANGUAGES[choice]
    print(f"Transcription language selected: {choice}")

# Create the button
combobox_translation = ctk.CTkOptionMenu(call_frame, values=list(LANGUAGES.keys()), command=transcription_language_callback, width=200)
combobox_translation.set("Select Transcription Language")
combobox_translation.pack(pady=10)

# Update spoken language dropdown
def spoken_language_callback(choice):
    user.spoken_language = LANGUAGES[choice]
    print(f"Spoken language selected: {choice}")

# Create the button
combobox_translation = ctk.CTkOptionMenu(call_frame, values=list(LANGUAGES.keys()), command=spoken_language_callback, width=200)
combobox_translation.set("Select Spoken Language")
combobox_translation.pack(pady=10)

# Initialize Start Recording Button but don't pack it initially
start_recording_button = ctk.CTkButton(call_frame, text="Start Recording", command=start_recording)

def update_input_devices_combobox():
    global comboboxin, device_name_to_info_mapping
    input_devices = get_user_input()
    device_names = [device['name'] for device in input_devices]  # Extract device names
    update_input_device_name_to_info_mapping(input_devices)  # Update the mapping

    # Destroy the existing combobox (if it exists)
    if 'comboboxin' in globals():
        comboboxin.destroy()

    # Recreate the combobox with the new values
    comboboxin = ctk.CTkOptionMenu(call_frame, values=device_names, height=40, width=200, command=comboboxin_callback)
    comboboxin.pack(pady=10)
    comboboxin.set("Select Input")  # Optionally set a default value



def update_output_devices_combobox():
    global comboboxout, output_device_name_to_info_mapping
    output_devices = get_user_output()
    device_names = [device['name'] for device in output_devices]  # Extract device names
    update_output_device_name_to_info_mapping(output_devices)  # Update the mapping

    # Destroy the existing combobox (if it exists)
    if 'comboboxout' in globals():
        comboboxout.destroy()

    # Recreate the combobox with the new values
    comboboxout = ctk.CTkOptionMenu(call_frame, values=device_names, height=40, width=200, command=comboboxout_callback)
    comboboxout.pack(pady=10)
    comboboxout.set("Select Output")  # Optionally set a default value


def update_input_device_name_to_info_mapping(devices):
    global input_device_name_to_info_mapping
    for device in devices:
        input_device_name_to_info_mapping[device['name']] = device

def update_output_device_name_to_info_mapping(devices):
    global output_device_name_to_info_mapping
    for device in devices:
        output_device_name_to_info_mapping[device['name']] = device

back_button_call = ctk.CTkButton(call_frame, text="Back to Main", command=lambda: raise_frame(main_frame))
back_button_call.pack(pady=20, padx=20)


# Logs Frame Content - Placeholder content for now
logs_label = ctk.CTkLabel(logs_frame, text="Call Logs", font=(clock_font_family, 35))
logs_label.pack(pady=20, padx=20)

back_button_logs = ctk.CTkButton(logs_frame, text="Back to Main", command=lambda: raise_frame(main_frame))
back_button_logs.pack(pady=20, padx=20)

# Modify the Logs Frame Content to include the sample logs table

#Set this up to be window so that its not hardcoded
def setup_logs_frame(username):
    # Create the Treeview widget for displaying the table within logs_frame
    logs_table = ttk.Treeview(logs_frame, height=10)
    logs_table.pack(expand=True, fill='both', side='top')

    # Define the columns
    logs_table['columns'] = ('callID', 'caller', 'callee', 'callDate', 'call_transcript')

    # Format the columns
    logs_table.column("#0", width=0, stretch=tk.NO)  # Phantom column
    logs_table.column("callID", anchor=tk.W, width=80)
    logs_table.column("caller", anchor=tk.W, width=120)
    logs_table.column("callee", anchor=tk.W, width=120)
    logs_table.column("callDate", anchor=tk.W, width=120)
    logs_table.column("call_transcript", anchor=tk.W, width=300)

    # Create Headings
    logs_table.heading("#0", text="", anchor=tk.W)
    logs_table.heading("callID", text="Call ID", anchor=tk.W)
    logs_table.heading("caller", text="Caller", anchor=tk.W)
    logs_table.heading("callee", text="Callee", anchor=tk.W)
    logs_table.heading("callDate", text="Call Date", anchor=tk.W)
    logs_table.heading("call_transcript", text="Call Recording", anchor=tk.W)

    #CHANGE THE USERNAME HERE
    print("current user is " +  username)
    for log in database.get_calls(username):
        logs_table.insert(parent='', index='end', iid=log[0], text="", values=log)

# Call the setup_logs_frame function to initialize the logs table when the app starts


# Function to handle the sign-in process (placeholder for actual functionality)
def sign_in():
    username = username_entry.get()
    password = password_entry.get()
    if(database.login(username, password)):
        user.username = username
        connect_with_server()

        raise_frame(main_frame)
        setup_logs_frame(username)

    else:
        messagebox.showinfo("Login Attempt Failed", "The username or password you entered is incorrect.")
        password_entry.delete(0, tk.END)
    
def sign_up():
    username = username_entry_signup.get()
    password = password_entry_signup.get()
    verify_password = confirm_password_entry.get()

    if (password == verify_password):
        database.create_user(username, password)
        raise_frame(log_in_frame)
    else:
        messagebox.showinfo("Signup Attempt", f"Passwords do not match\nPlease try again")

# Transcribe Frame Content
transcribe_label = ctk.CTkLabel(transcribe_frame, text="Transcription:", font=(clock_font_family, 20))
transcribe_label.pack(pady=20, padx=20)

transcribe_textbox = ctk.CTkTextbox(transcribe_frame, height=400, width=500)
transcribe_textbox.pack(pady=10, padx=20, expand=True, fill='both')
transcribe_textbox.configure(state= "disabled")


def update_transcribe_textbox(text):
    # global last_words
    # result = utilities.subtract_strings(text, last_words)
    # last_words = text
    translation = translator.translate(text, src=user.spoken_language, dest=user.transcription_language)
    print(user.spoken_language)
    print(user.transcription_language)
    def callback():
        transcribe_textbox.configure(state="normal")
        transcribe_textbox.insert(tk.END, translation.text)
        transcribe_textbox.insert(tk.END, "\n")
        transcribe_textbox.configure(state="disabled")
    app.after(0, callback)

def start_transcription_thread():
    # Start the speech-to-text process in a separate thread to keep UI responsive
    transcription_thread = Thread(target=start_speech_to_text_transcription, args=(update_transcribe_textbox, user.stop_transcription, user),daemon=True)
    transcription_thread.start()

def start_transcription():
    user.stop_transcription.clear()  # Ensure the stop event is clear at start
    stop_transcription_button.configure(state="normal")  # Enable the Stop button
    start_transcription_button.configure(state="disabled")  # Optionally disable the Start button
    start_transcription_thread()


def stop_transcription():
    user.stop_transcription.set()  # Signal the transcription thread to stop
    stop_transcription_button.configure(state="disabled")  # Disable the Stop button
    start_transcription_button.configure(state="normal")  # Re-enable the Start button


button_container_frame = ctk.CTkFrame(transcribe_frame)
button_container_frame.pack(pady=10, padx=20)  # Adjust padding as needed

# Modify the start_transcription_button to be packed inside button_container_frame
start_transcription_button = ctk.CTkButton(button_container_frame, text="Start", command=start_transcription)
start_transcription_button.pack(side='left', padx=5)  # Pack it on the left, add some padding for spacing

# Modify the stop_transcription_button similarly
stop_transcription_button = ctk.CTkButton(button_container_frame, text="Stop", state="disabled")
stop_transcription_button.pack(side='left', padx=5)  # Pack it next to the start button
stop_transcription_button.configure(command=stop_transcription)

back_button_transcribe = ctk.CTkButton(transcribe_frame, text="Back to Main", command=lambda: raise_frame(main_frame))
back_button_transcribe.pack(pady=20, padx=20)


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

# Setting up the sign_up_frame
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
    global input_stream, output_stream, audio
    if input_stream is not None:
        input_stream.stop_stream()
        input_stream.close()
    if output_stream is not None:
        output_stream.stop_stream()
        output_stream.close()
    if audio is not None:
        audio.terminate()
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_close)

# raise_frame(main_frame)
# Initially, show the main frame
raise_frame(log_in_frame)

app.mainloop()

