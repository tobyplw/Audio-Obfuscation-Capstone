# Author: Shafin Alam

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox  # Import messagebox for showing dialog messages
from datetime import datetime  # Import datetime to fetch the current time
from tkinter import ttk  # Import ttk module for Treeview
from tkinter import PhotoImage

# Initialize the main application window
app = ctk.CTk()
app.title('Ombra Audio Obfuscation Platform')
# Get screen width and height
screen_width = app.winfo_screenwidth()-9
screen_height = app.winfo_screenheight()
app.geometry(f'{screen_width}x{screen_height}+0+0')
# app.attributes('-fullscreen', True)
app.iconbitmap('S:\\CapstoneGui\\NewLogo.ico')  # Set icon/logo
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
main_frame = ctk.CTkFrame(app)
call_frame = ctk.CTkFrame(app)
logs_frame = ctk.CTkFrame(app)  # Frame for logs

for frame in (main_frame, call_frame, logs_frame):
    frame.grid(row=0, column=0, sticky='nsew')

# Define clock font settings with the correct parameters for customtkinter
clock_font_family = "Helvetica"  # Font family
clock_font_size = 150  # Font size
# clock_font_weight = "bold"  # Font weight

# Main Frame Content - Adjust layout for clock and buttons
main_frame_content = ctk.CTkFrame(main_frame)
main_frame_content.pack(pady=20, padx=20, expand=True)

# Load the sponsor's logo image
logo_image = PhotoImage(file='S:\\CapstoneGui\\ombra-logo.png')

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

# Call Frame Content
call_label = ctk.CTkLabel(call_frame, text="Enter Callee's Unique ID:")
call_label.pack(pady=10, padx=20)

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

# Initialize Start Recording Button but don't pack it initially
start_recording_button = ctk.CTkButton(call_frame, text="Start Recording", command=start_recording)

back_button_call = ctk.CTkButton(call_frame, text="Back to Main", command=lambda: raise_frame(main_frame))
back_button_call.pack(pady=20, padx=20)

# Logs Frame Content - Placeholder content for now
logs_label = ctk.CTkLabel(logs_frame, text="Call Logs", font=(clock_font_family, 35))
logs_label.pack(pady=20, padx=20)

back_button_logs = ctk.CTkButton(logs_frame, text="Back to Main", command=lambda: raise_frame(main_frame))
back_button_logs.pack(pady=20, padx=20)

# Modify the Logs Frame Content to include the sample logs table
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

    # Sample Data
    sample_logs = [
        ("001", "John Doe", "Jane Smith", "2024-02-08", "This is a sample recording of call 001."),
        ("002", "Alice Johnson", "Bob Brown", "2024-02-09", "This is a sample recording of call 002."),
        # Add more sample data as needed
    ]

    # Insert sample data into the table
    for log in sample_logs:
        logs_table.insert(parent='', index='end', iid=log[0], text="", values=log)

# Call the setup_logs_frame function to initialize the logs table when the app starts
setup_logs_frame()

# Continue with your existing code to initially show the main frame and start the app's main loop
raise_frame(main_frame)
# Initially, show the main frame
raise_frame(main_frame)

app.mainloop()
