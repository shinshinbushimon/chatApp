import asyncio
import socket
from chat_server2_tools import read_processed_data,exist_chat, create_token, process_tcp_data, read_udp_data, process_udp_data


'''
    TCPパケット構造 ⇒ | ChatNameLength: 1byte | Operation: 1byte | State: 1byte | Payload: 29byte |
    Operationが1の時、新規作成:
        chatroom_tokensにマッピングを新たに追加してホストを配列の最初に
    Operationが2の時、新規参加:
        chatroom_tokesに追加
    サーバから送信する場合ハッシュトークン文字列を含める
    
    UDPパケット構造 ⇒ | ChatNameLength: 1byte | TokenLength: 1byte | Payload: 30byte | 
    リクエストが来たChatNameにTokenLengthとIPアドレスの両方が同時に登録されていない場合、これはトークに参加させない
    クライアントが接続から退出あるいは接続がダウンされた際そのクライアントがホストの場合、全員にトークセッション終了を報告しトークを破棄する

    必要：
        create_token(): ハッシュを生成。トークン文字列として使用
        exist_chat(chat_name): 新規作成リクエスト受けた際にチャット名が既に作成されていないかの確認
        is_host(user_ip, chat_name): 該当のユーザがchatにホストとして登録されているかどうかを確認
        anounce_to_all(word, chat_name): wordを二番目の配列引数（chatroom_tokens[chat_name]）に該当するユーザにアナウンス 
        delete_chat(chat_name): chat_nameのchatを削除

'''

chatroom_tokens = {} # チャットルーム名をキーに、チャットルームに参加しているuserip_and_tokenの配列をvalueに
data_unit = 512
server_address = '0.0.0.0'
TCP_PORT = 9001
UDP_PORT = 9002

class UdpServerProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport
        print("Connection made")

    def datagram_received(self, data, addr):
        message = data.decode()
        print(f"Received {message} from {addr}")
        # 応答を送信するなど、ここに処理を追加
        self.transport.sendto(data, addr)
        print(f"Recyved data from {addr} by udp")
        chat_name, token, msg = read_udp_data(data)
        target_user = find_username(token, addr, chat_name)
        print(f"Recieved following message from {addr} msg: {msg}")
        if target_user:
            send_data = process_udp_data(chat_name, f"message from {target_user} msg: {msg}")

            for members_info in chatroom_tokens[chat_name]:
                self.transport.sendto(send_data, (members_info['IP'], UDP_PORT)) # クライアント側でも同じポートを指定
            print('message was sent to all sucessfully!')
        
        else:
            send_data = process_udp_data(chat_name, "You aren't avaliable...")
            self.transport.sendto(send_data, addr)
            print("There was the request given from unregistereduser")

# ユーザ固有のトークン文字列、IPアドレス、登録するユーザ名を保有したオブジェクトを返す。
def create_user_info(user_name, client_ip):
    print('it seems to be able to create user-info')
    return {
        'IP': client_ip,
        'username': user_name,
        'hash_token': create_token()
    }

def find_username(token, client_ip, chat_name):
    if chat_name in chatroom_tokens and chatroom_tokens[chat_name]:
        chat_members_info = chatroom_tokens[chat_name]
        for memberinfo in chat_members_info:
            if memberinfo['IP'] == client_ip and memberinfo['hash_token'] == token:
                return memberinfo['username']
    
    return None


# あらたなchat_roomを作成し、payloadとして送信したい文字列を返す
def create_new_chat(chat_name, user_name, client_ip):
    print(f"create new {chat_name} chat!! {user_name} is host user. this message is from create_new_chat")
    chatroom_tokens[chat_name] = [create_user_info(user_name, client_ip)]
    print("it seems to be able to return the created data")
    return f"You're the host user in {chat_name}"

# userをチャットに追加
def add_user_to_chat(chat_name, user_name, client_ip):
    print(f"create new {chat_name} chat!! {user_name} is host user. this message is from add_user_to_chat")
    chatroom_tokens[chat_name].append(create_user_info(user_name, client_ip))
    return f"The chatroom you requested already exist So, You are'nt the host."

async def operate_tcp_server(reader, writer):
    print("Called tcpentry")
    # data = await asyncio.wait_for(reader.read(100), timeout=5.0)
    data = await reader.read(data_unit)

    print(f"Reciceved data {data}")
    client_ip = writer.get_extra_info('peername')

    print(f'Recieved data from {client_ip}') # clientIPアドレスの取得

    # リクエスト応答処理（state: 1）
    ope, _, chat_name, user_name = read_processed_data(data)
    print(f"Reciceved data {data}")
    writer.write(process_tcp_data(len(chat_name), ope, 1, chat_name+'200 OK!!')) # statusコードを即座に送信
    await writer.drain() # 書き込み処理の待機

    # リクエスト完了処理（state: 2）
    message_payload = ''
    if ope == 1: # 新規チャット作成依頼
        if not exist_chat(chatroom_tokens,chat_name):
            message_payload = create_new_chat(chat_name, user_name, client_ip)
        else:
            message_payload = add_user_to_chat(chat_name, user_name, client_ip)
    
    else: # 新規参加依頼
        if not exist_chat(chatroom_tokens,chat_name):
            message_payload = create_new_chat(chat_name, user_name, client_ip)
        else:
            # 新規参加依頼で新規作成は適切でないかもしれない。
            message_payload = add_user_to_chat(chat_name, user_name, client_ip)

    print('it seems to be able to create message-payloads')
    print(f"Whether create chatroom or not: {chatroom_tokens[chat_name][-1]} and chatroom is {chat_name}")
    try:
        token = chatroom_tokens[chat_name][-1]['hash_token'] if chatroom_tokens[chat_name] else ''
        print("token is " + token)
    except Exception as e:
        print(str(e))
    print("write successfully!")
    writer.write(process_tcp_data(len(message_payload), ope, 2, message_payload+token))
    await writer.drain()
        

async def service_entry():
    
    server = await asyncio.start_server(operate_tcp_server, server_address, TCP_PORT)
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UdpServerProtocol(),
        local_addr=(server_address, UDP_PORT)
    )

    async with server:
        await server.serve_forever()

try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(service_entry())

except Exception as e:
    print(str(e))

