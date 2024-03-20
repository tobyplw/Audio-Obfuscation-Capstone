import socket
import time
import sys
import select
import threading
import stun
import json
import shared
import call
from tkinter import messagebox


def check_NAT():
    try:
        nat_type, external_ip, external_port = stun.get_ip_info()
        print("Nat Type: " + str(nat_type))
        if nat_type == "Symmetric NAT":
            print("NAT is Symmetric. This service may not work")
    except:
        pass

def get_internal_address():
    internal_ip, internal_port = shared.client_socket.getsockname()
    internal_ip = socket.gethostbyname(socket.gethostname()) #sometimes the first one gets the wrong internal ip or something
    return internal_ip, internal_port

def server_connection():
    print("Connecting to external server...")
    check_NAT()
    poll_time = 0
    internal_ip, internal_port = get_internal_address()
    while True:
        curr_time = time.time()
        if curr_time > poll_time + shared.Poll_Time:
            poll_time = curr_time
            message = {"Action" : "Poll", "From_Username" : shared.current_user, "Internal_IP" : internal_ip, "Internal_Port" : internal_port, "Time" : time.time()}
            shared.client_socket.sendto(json.dumps(message).encode(), (shared.SERVER_HOST, shared.SERVER_PORT))


def send_call_message(user_input, client_socket):
    print("Calling ", user_input)
    message = {"Action" : "Calling","From_Username" : shared.current_user, "To_Username" : user_input, "Time" : time.time()}
    client_socket.sendto(json.dumps(message).encode(), (shared.SERVER_HOST, shared.SERVER_PORT))


def recieve_messages():
    IN_CALL = False
    while not IN_CALL:
        data, server_address = shared.client_socket.recvfrom(1024)
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
            handle_call(destination_ip,destination_port, callee_username )
            IN_CALL = True
        elif action == "DECLINED":
            callee_username = inc_message["To_Username"]
            print(f"{callee_username} Decline Your Call")


def handle_error_message(callee_username):
    # add these messages to gui interface
    # print(f"There was an error contacting {callee_username}. Either does not exist or is not logged in.")
    # print("Try Again: Enter username you are trying to reach: ")
    pass

def handle_call(destination_ip,destination_port, callee_username):
    record_stream, listen_stream = call.start_audio_stream(shared.input_device, shared.output_device)
    start_call_thread = threading.Thread(target=call.talk, args=(shared.client_socket, record_stream,callee_username, destination_ip, destination_port))
    listen_call_thread = threading.Thread(target=call.listen, args=(shared.client_socket, listen_stream))
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
        message = {"Action" : "Accept", "From_Username" : shared.current_user, "To_Username" : callee_username,  "Time" : time.time()}
        shared.client_socket.sendto(json.dumps(message).encode(), (shared.SERVER_HOST, shared.SERVER_PORT))
        
    else:
        # User denied the call
        print("Call denied.")
        # Add logic for what happens when a call is denied
        message = {"Action" : "Decline", "From_Username" : shared.current_user, "To_Username" : callee_username,  "Time" : time.time()}
        shared.client_socket.sendto(json.dumps(message).encode(), (shared.SERVER_HOST, shared.SERVER_PORT))


def connect_with_server():
    shared.client_socket.bind(('0.0.0.0', 0))
    server_polling_thread = threading.Thread(target=server_connection)
    server_responding_thread = threading.Thread(target=recieve_messages)

    server_polling_thread.start()
    server_responding_thread.start()


