import asyncio
import socket
from chat_server2_tools import read_processed_data, exist_chat, create_token, process_tcp_data


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
data_unit = 4096
server_address = '0.0.0.0'
TCP_PORT = 9001
UDP_PORT = 9002

# ユーザ固有のトークン文字列、IPアドレス、登録するユーザ名を保有したオブジェクトを返す。
def create_user_info(user_name, client_ip):
    return {
        'IP': client_ip,
        'username': user_name,
        'hash_token': create_token()
    }

# あらたなchat_roomを作成し、payloadとして送信したい文字列を返す
def create_new_chat(chat_name, user_name, client_ip):
    print(f"create new {chat_name} chat!! {user_name} is host user.")
    chatroom_tokens[chat_name] = create_user_info(user_name, client_ip)
    return f"You're the host user in {chat_name}"

# userをチャットに追加
def add_user_to_chat(chat_name, user_name, client_ip):
    print(f"create new {chat_name} chat!! {user_name} is host user.")
    chatroom_tokens[chat_name].append(create_user_info(user_name, client_ip))
    return f"The chatroom you requested already exist So, You are'nt the host."

async def operate_tcp_server(reader, writer):
    data = await reader.read(data_unit)
    client_ip = writer.get_extra_info('peername')

    print(f'Recieved data from {client_ip}') # clientIPアドレスの取得

    # リクエスト応答処理（state: 1）
    ope, _, chat_name, user_name = read_processed_data(data)
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
            message_payload = add_user_to_chat(chat_name, user_name, client_ip)
        else:
            # 新規参加依頼で新規作成は適切でないかもしれない。
            message_payload = create_new_chat(chat_name, user_name, client_ip)

    token = chatroom_tokens[chat_name][-1]['hash_token'] if chatroom_tokens[chat_name] else ''
    writer.write(process_tcp_data(len(message_payload), ope, 2, message_payload+token))
    await writer.drain()





async def run_udp_server():
    print(3)

async def service_entry():
    print(3)