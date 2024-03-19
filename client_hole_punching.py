import socket
import time
import sys
import select
import threading
import stun
import json

# Server address and port
SERVER_HOST = '13.58.118.16'
SERVER_PORT = 12345
IN_CALL = False

def get_external_ip_and_port():
    # Perform STUN communication
    nat_type, external_ip, external_port = stun.get_ip_info()

    return external_ip, external_port, nat_type



def non_blocking_input():

    # Create a dictionary of file descriptors to monitor
    inputs = [sys.stdin]
    # Use select to check if there is any input ready to be read
    ready_to_read, _, _ = select.select(inputs, [], [], 0)
    # If there is input ready to be read
    if sys.stdin in ready_to_read:
        # Read the input from stdin
        return sys.stdin.readline().strip()
    else:
        # Return None if no input is available
        return None


def server_connection():
    print("Connecting to external server...")
    stun_server = SERVER_HOST  # Replace with the address of the STUN server
    try:
        external_ip, external_port, nat_type = get_external_ip_and_port()
        print("Nat Type: " + str(nat_type))
        if nat_type == "Symmetric NAT":
            print("NAT is Symmetric. This service may not work")
    except:
        pass
    poll_time = 0
    print("Enter username you are trying to reach: ")
    while True:
        user_input = None
        curr_time = time.time()
        if curr_time > poll_time + 1:
            poll_time = curr_time
            message = {"Action" : "Poll", "From_Username" : user_profile["Username"], "Internal_IP" : user_profile["Internal_IP"], "Internal_Port" : user_profile["Internal_Port"], "Time" : time.time()}
            client_socket.sendto(json.dumps(message).encode(), (SERVER_HOST, SERVER_PORT))
        user_input = non_blocking_input()
        if user_input is not None:
            print("Calling ", user_input)
            message = {"Action" : "Calling","From_Username" : user_profile["Username"], "To_Username" : user_input, "Time" : time.time()}
            client_socket.sendto(json.dumps(message).encode(), (SERVER_HOST, SERVER_PORT))


def recieve_messages():
    IN_CALL = False
    while not IN_CALL:
        data, server_address = client_socket.recvfrom(1024)
        inc_message = json.loads(data.decode())
        print("Recieved message: " + str(inc_message))
        action = inc_message["Action"]
        username = inc_message["From_Username"]

        if action == "POKE":
            #user_input = input(f"User <{username}> is trying to call you! Do you accept? [y/n]")
            callee_username = inc_message["From_Username"]
            user_input = 'y'
            if user_input == 'y':
                print("Accepted Call")
                message = {"Action" : "Accept", "From_Username" : user_profile["Username"], "To_Username" : callee_username,  "Time" : time.time()}
                client_socket.sendto(json.dumps(message).encode(), (SERVER_HOST, SERVER_PORT))
            else:
                print("Decline Call")
                message = {"Action" : "Decline", "From_Username" : user_profile["Username"], "To_Username" : callee_username,  "Time" : time.time()}
                client_socket.sendto(json.dumps(message).encode(), (SERVER_HOST, SERVER_PORT))
        elif action == "ERROR":
            callee_username = inc_message["To_Username"]
            print(f"There was an error contacting {callee_username}. Either does not exist or is not logged in.")
            print("Try Again: Enter username you are trying to reach: ")
        elif action == "CALL": 
            print(inc_message)
            destination_ip = inc_message["Destination_IP"]
            destination_port = inc_message["Destination_Port"]
            callee_username = inc_message["From_Username"]
            start_call_thread = threading.Thread(target=start_call, args=(callee_username, destination_ip, destination_port))
            listen_call_thread = threading.Thread(target=listen_call)
            start_call_thread.start()
            listen_call_thread.start()
            IN_CALL = True
        elif action == "DECLINED":
            callee_username = inc_message["To_Username"]
            print(f"{callee_username} Decline Your Call")


def listen_call():
    print("Listening for incoming packets")
    while True:
        data, server_address = client_socket.recvfrom(1024)
        print("Recieved message: " + str(data.decode()) + " at " + str(server_address))

def start_call(callee_username, destination_ip, destination_port):
    IN_CALL = True
    print(f"Starting Call with {callee_username} at ip:{destination_ip} port:{destination_port}") 

    time.sleep(.05)
    data = "UDP HolePunch"
    client_socket.sendto(data.encode(), (destination_ip, int(destination_port)))
    i = 0
    while i < 20:
        data = f"Hello from {MY_USERNAME}"
        client_socket.sendto(data.encode(), (destination_ip, int(destination_port)))
        time.sleep(.1)
        i+=1


name = sys.argv[1]
MY_USERNAME = sys.argv[1]



client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.bind(('0.0.0.0', 0))

user_profile = {"Username": None, "Internal_IP" : None, "Internal_Port" : None}
internal_ip, internal_port = client_socket.getsockname()
internal_ip = socket.gethostbyname(socket.gethostname())

user_profile = {"Username": MY_USERNAME, "Internal_IP" : internal_ip, "Internal_Port" : internal_port}


server_polling_thread = threading.Thread(target=server_connection)
server_responding_thread = threading.Thread(target=recieve_messages)

server_polling_thread.start()
server_responding_thread.start()


