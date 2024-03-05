import socket

# Create TCP Socket
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# IP Constants
receiving_ip = '127.0.0.1'
receiving_port = 2323
destination_ip = '127.0.0.1'
destination_port = 2323

# Attempt to connect to existing client or begin listening
def start_client():
    try:
        create_client()
    except ConnectionRefusedError:
        print("Could not connect to caller. Listening for connection...")
        server_start()

# Listen for peer connection requests
def server_start():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((receiving_ip, receiving_port))
    server_socket.listen(1)
    conn, addr = server_socket.accept()
    with conn:
        print(f"Connected to client at {addr}")

        message = input("Enter yes to begin communication (anything else to end): ")
        if message.lower() == 'yes':
            conn.sendall(message.encode())
        else:
            return
        
        data = conn.recv(1024)
        peer_message = data.decode()
        if peer_message =='yes':
            print('\n\nCommunication starting!!!!!')
            
# Request connection to listening peer
def create_client():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        tcp_socket.connect((destination_ip, destination_port))
        print(f"Connected to client at {destination_ip}")
        message = input("Enter yes to begin communication (anything else to end): ")
        if message.lower() == 'yes':
            tcp_socket.sendall(message.encode())
        else:
            return

        data = tcp_socket.recv(1024)
        message = data.decode()
        if message == 'yes':
            print('\n\nCommunication Starting!!!!!')
            
    except Exception as e:
        print(f"Error connectiong: {e}")
        raise ConnectionRefusedError
    
start_client()