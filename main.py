# Author: Shafin Alam

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox  # Import messagebox for showing dialog messages
from tkinter import ttk  # Import ttk module for Treeview
from datetime import datetime  # Import datetime to fetch the current time
from PIL import Image # from tkinter import PhotoImage
from threading import Thread, Event
import database
from shared import stop_transcription_event
from stt import start_speech_to_text_transcription


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

start_call_button = ctk.CTkButton(button_frame, text="Start Call", command=lambda: raise_frame(call_frame), width=200, height=40)
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
call_label = ctk.CTkLabel(call_frame, text="Enter Callee's Unique ID:")
call_label.pack(pady=(30,20) , padx=20)

callee_id_entry = ctk.CTkEntry(call_frame)
callee_id_entry.pack(pady=10, padx=20)

# Modified call_user function to include hiding and showing the Start Recording button
def call_user():
    callee_id = callee_id_entry.get()  # Get the value from the entry field
    # print(f"Calling User with ID: {callee_id}")  # Placeholder for actual call functionality
    messagebox.showinfo("Call Authenticated", f"Calling User with ID: {callee_id}")  # Show a dialog box as feedback
    start_recording_button.pack(before=back_button_call, pady=10, padx=20)  # Adjusted to pack before the Back button

call_button = ctk.CTkButton(call_frame, text="Call", command=call_user)
call_button.pack(pady=10, padx=20)

def combobox_callback(choice):
    print("combobox dropdown clicked:", choice)

comboboxin = ctk.CTkOptionMenu(call_frame,
                                     values=["Yeti Mic", "Laptop Mic", "Camera Mic"],
                                     command=combobox_callback)
# combobox.grid(row=0, column=0, padx=20, pady=10)

comboboxin.set("Select Input")  # set initial value
comboboxin.pack(pady=10)

comboboxout = ctk.CTkOptionMenu(call_frame,
                                     values=["Desktop Speakers", "HyperX Headphones", "Apple Airpods", "Digital Audio"],
                                     command=combobox_callback)
# combobox.grid(row=0, column=0, padx=20, pady=10)

comboboxout.set("Select Output")  # set initial value
comboboxout.pack(pady=10)

# Initialize Start Recording Button but don't pack it initially
start_recording_button = ctk.CTkButton(call_frame, text="Start Recording", command=start_recording)

# # Dropdown menu options 
# inputOptions = [ 
#     "yetiMic", 
#     "LaptopMic", 
#     "CameraMic", 
# ] 
  
# # datatype of menu text 
# clicked = StringVar() 
  
# # initial menu text 
# clicked.set( "yetiMic" ) 
  
# # Create Dropdown menu 
# drop = tk.OptionMenu( app , clicked , *inputOptions ) 
# drop.pack() 

back_button_call = ctk.CTkButton(call_frame, text="Back to Main", command=lambda: raise_frame(main_frame))
back_button_call.pack(pady=20, padx=20)


# Logs Frame Content - Placeholder content for now
logs_label = ctk.CTkLabel(logs_frame, text="Call Logs", font=(clock_font_family, 35))
logs_label.pack(pady=20, padx=20)

back_button_logs = ctk.CTkButton(logs_frame, text="Back to Main", command=lambda: raise_frame(main_frame))
back_button_logs.pack(pady=20, padx=20)

# Modify the Logs Frame Content to include the sample logs table

#Set this up to be window so that its not hardcoded
def setup_logs_frame():
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
    for log in database.get_calls("azwad"):
        logs_table.insert(parent='', index='end', iid=log[0], text="", values=log)

# Call the setup_logs_frame function to initialize the logs table when the app starts
setup_logs_frame()

# Function to handle the sign-in process (placeholder for actual functionality)
def sign_in():
    username = username_entry.get()
    password = password_entry.get()
    if(database.login(username,password)):
        raise_frame(main_frame)
    else:
        messagebox.showinfo("Login Attempt Failed", f"The username or password you entered is incorrect.")
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
    def callback():
        transcribe_textbox.configure(state="normal")
        transcribe_textbox.insert(tk.END,text)
        transcribe_textbox.configure(state="disabled")
    app.after(0, callback)

def start_transcription_thread():
    # Start the speech-to-text process in a separate thread to keep UI responsive
    transcription_thread = Thread(target=start_speech_to_text_transcription, args=(update_transcribe_textbox, stop_transcription_event))
    transcription_thread.start()

def start_transcription():
    stop_transcription_event.clear()  # Ensure the stop event is clear at start
    stop_transcription_button.configure(state="normal")  # Enable the Stop button
    start_transcription_button.configure(state="disabled")  # Optionally disable the Start button
    start_transcription_thread()


def stop_transcription():
    stop_transcription_event.set()  # Signal the transcription thread to stop
    stop_transcription_button.configure(state="disabled")  # Disable the Stop button
    start_transcription_button.configure(state="normal")  # Re-enable the Start button

# Configure the Stop button's command


start_transcription_button = ctk.CTkButton(transcribe_frame, text="Start", command=start_transcription)
start_transcription_button.pack(pady=10, padx=20)

stop_transcription_button = ctk.CTkButton(transcribe_frame, text="Stop", state="disabled")
stop_transcription_button.pack(side="left", pady=10, padx=20)
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


# raise_frame(main_frame)
# Initially, show the main frame
raise_frame(log_in_frame)

app.mainloop()
