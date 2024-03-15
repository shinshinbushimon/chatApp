import socket
import os

def process_data(username, message):
    username_len_bytes = len(username).to_bytes(1, "big")
    username_bytes = username.encode('utf-8')
    message_bytes = message.encode('utf-8')

    return username_len_bytes + username_bytes + message_bytes

def recieved_byte_data(data):
    username_length = int.from_bytes(data[:1], "big")
    username = data[1:1+username_length].decode('utf-8')
    message = data[1+username_length:].decode('utf-8')
    print("This message is from {}: {}".format(username, message))

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = input("enter the server address")
server_port = 9001
unit_data = 4096

while True:
    try:
        username = ''
        while not username:
            username = input("enter your name")

        message = ''
        while not message:
            message = input('enter your message')
        
        byte_send = process_data(username, message)
        sock.sendto(byte_send, (server_address, server_port))

        data, _ = sock.recvfrom(unit_data)
        recieved_byte_data(data)

    finally:
        print('closing socket')
        sock.close()
    

