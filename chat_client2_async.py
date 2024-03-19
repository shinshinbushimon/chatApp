import asyncio
import socket
from chat_server2_tools import read_processed_data, read_udp_data, process_tcp_data, process_client_udp, read_client_tcp
data_unit = 4096
TCP_PORT = 9001
UDP_PORT = 9002

server_address = input('Enter server address: ')
user_operate = ''
WAITTIME = 5

# 依頼確認
while not user_operate == '0' and not user_operate == '1':
    user_operate = input('choose the following options\ncreate new chat: 0\njoin to chat: 1\n')
    if not user_operate == '0' and not user_operate == '1':
        print("You made an wrong decision.")


target_chatname = input('enter roomname in your mind: ')


def display_response(message):
    print(f"Recieved response from {server_address}. the recieved message: {message}.")
    
async def request_tcp():
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(server_address, TCP_PORT),
            WAITTIME
        )

        tcp_request_data = process_tcp_data(len(target_chatname), int(user_operate), 0, target_chatname)
        writer.write(tcp_request_data)
        await writer.drain()
        response_data = await reader.read(data_unit) # 応答レスポンス
        _, _, _, payloads = read_processed_data(response_data)
        display_response(payloads)

        response_tokens_data = await reader.read(data_unit)
        global TOKEN
        message, _, state, TOKEN = read_client_tcp(response_tokens_data)
        if state == 2:
            display_response(message)
        else: 
            print("request is falled")
        print("close the connection")
        writer.close()
        await writer.wait_closed()

    except asyncio.TimeoutError:
        raise RuntimeError("Connection time out")


async def request_udp():
    while True:
        data, _ = await loop.sock_recvfrom(data_unit)
        roomname, _, message = read_udp_data(data)
        print(f"here room is {roomname}.\n{message}")


async def entry_point():
    await request_tcp()

    global udp_sock
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((server_address, UDP_PORT))
    message = input("enter your message: ")
    processed_data = process_client_udp(target_chatname, message, TOKEN)
    udp_sock.sendto(processed_data)
    # looptaskにすること
    loop.create_task(request_udp())

    print("Sent your message")



loop = asyncio.get_event_loop()
loop.run_until_complete(entry_point())




    

