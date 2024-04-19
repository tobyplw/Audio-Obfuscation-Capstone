import socket
import threading
import json
import time

# Server address and port
HOST = '0.0.0.0'  # Listen on all available interfaces
PORT = 12345



# Create a publicaly available UDP socket to recieve messages on
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))
  

#Given a recieved message, call the correct function based on the action
#input: data (JSON Map with all packet information), client_address, client_port 
#output: Calls correct function
def determine_message(data, client_address, client_port):
    From_Username = data["From_Username"]
    action = data["Action"]
    time = data["Time"]

    if action == "Poll": #Poll message means the sender is wanting to keep itself "connected" to server and available for calls
        internal_ip = data["Internal_IP"]
        internal_port = data["Internal_Port"]
        add_client(From_Username, time, client_address, client_port, internal_ip, internal_port)
    elif action == "Calling": #Calling message means a user wants to reach another user. The server will help initate that call by asking the other user if they would like to get called
        To_Username = data["To_Username"]
        initiate_call(From_Username, To_Username, client_address, client_port)
    elif action == "Accept": #Accept message means that both parties have agreed to join into a call
        To_Username = data["To_Username"]
        start_call(From_Username, To_Username, client_address, client_port)
    elif action == "Decline": #Decline message means Callee does not want to join in a call.
        To_Username = data["To_Username"]
        decline_call(From_Username, To_Username, client_address, client_port)
    
#Updates clients Dictionary with username and all associated information
def add_client(From_Username, time, external_address, external_port, internal_ip, internal_port):
    clients[From_Username] = {"Username": From_Username, "Status" : "Connected",  "External_IP" : external_address, "External_Port" : external_port,"Internal_IP" : internal_ip, "Internal_Port" : internal_port, "Time" : time}

#when a User requests to call another user, we send a POKE message to that user with the username of the other user
def initiate_call(From_Username, callee_username, client_address, client_port):
    if (callee_username in clients) and (callee_username != From_Username): #check to make sure requested user is in client list and they aren't calling themselves
        callee_info = clients[callee_username]
        callee_address = callee_info["External_IP"]
        callee_port = callee_info["External_Port"]
        #send Poke message to requested username
        callee_msg = {"From_Username": From_Username, "Action" : "POKE", "To_Username" : callee_username, "Time" : time.time()}
        server_socket.sendto(json.dumps(callee_msg).encode(), (callee_address, callee_port))
    else: #send an error message
        #pack into JSON
        no_callee_msg = {"From_Username": From_Username, "Action" : "ERROR", "To_Username" : callee_username, "Time" : time.time()}
        #send message back to original message sender
        server_socket.sendto(json.dumps(no_callee_msg).encode(), (client_address, client_port))

#Faciliates the address and port sharing between the Caller and Callee
#Input: The caller and callee username. This is used to extract the calling information
def start_call(caller_username, callee_username):
    callee_info = clients[callee_username]
    callee_ip = callee_info["External_IP"]
    callee_port = callee_info["External_Port"]
    callee_address = (callee_ip, callee_port)

    caller_info = clients[caller_username]
    caller_ip = caller_info["External_IP"]
    caller_port = caller_info["External_Port"]
    caller_address = (caller_ip, caller_port)

    if caller_ip == callee_ip: #on local network, use local IP address
        callee_ip = callee_info["Internal_IP"]
        callee_port = callee_info["Internal_Port"]
        caller_ip = caller_info["Internal_IP"]
        caller_port = caller_info["Internal_Port"]

    #exchange information with the two clients
    callee_message = {"Action" : "CALL", "From_Username" : caller_username,  "To_Username" : callee_username, "Destination_IP" : caller_ip, "Destination_Port" : caller_port, "Time" : time.time()}
    server_socket.sendto(json.dumps(callee_message).encode(), callee_address)

    caller_message = {"Action" : "CALL", "From_Username" : callee_username,  "To_Username" : caller_username, "Destination_IP" : callee_ip, "Destination_Port" : callee_port, "Time" : time.time()}
    server_socket.sendto(json.dumps(caller_message).encode(), caller_address)

#Send a Decline message to the original caller if the callee declines the call
def decline_call(callee_username, caller_username):
        caller_info = clients[caller_username]
        caller_address = caller_info["External_IP"]
        caller_port = caller_info["External_Port"]
        callee_message = {"Action" : "DECLINED", "From_Username" : callee_username,  "To_Username" : callee_username,  "Time" : time.time()}
        server_socket.sendto(json.dumps(callee_message).encode(), (caller_address, caller_port))

#Periodically check on the client list. If a client hasn't send a Poll message to the server in 5 seconds, take them off the list
def check_clients():
    while True:
        time.sleep(1)
        to_remove = []
        time_now = time.time()
        for client in clients.keys():
            if time_now - clients[client]["Time"] > 5: #check if 5 seconds has passed
                to_remove.append(client) #add to remove list

        for item in to_remove: #remove all client on to_remove list from clients dict
            clients.pop(item)
        
        if len(clients) > 0: #print connected clients to the terminal
            print("Connected Clients:" + ' '.join(clients.keys()))




print("Server started, waiting for clients...")

# Dictionary to store client addresses
clients = {}

#start thread to always check if clients have connected to server within the last 5 seconds
check_clients_thread = threading.Thread(target=check_clients)
check_clients_thread.start()

#continually take in data from port, and then determine what action to take based on the data
while True:
    # Receive data and address from a client
    data, (client_address, client_port) = server_socket.recvfrom(1024)
    determine_message(json.loads(data.decode()), client_address, client_port)

