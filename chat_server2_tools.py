import socket
import secrets
import asyncio

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
data_unit = 4096
token_bytes_len = 5
server_address = '0.0.0.0'
TCP_PORT = 9001
UDP_PORT = 9002
sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def create_token():
    return secrets.token_bytes(token_bytes_len)

def exist_chat(chatroom_tokens, chat_name):
    return chat_name in chatroom_tokens

def is_host(chatroom_tokens, user_ip, chat_name):
    return exist_chat(chat_name) and user_ip in chatroom_tokens[chat_name][0] # hostは0番目

def create_ip_and_hash(ip):
    return {ip: create_token()}



def announce_by_udp(chatroom_tokens, packet, chat_name):
    if exist_chat(chat_name):
        for ip in chatroom_tokens[chat_name]:
            sock_udp.sendto((ip, packet))

# def announce_by_tcp(msg_bytes):

# ユーザが所属するかどうかを確認し、ホストとして所属する場合チャットルーム事削除その際、削除メッセージを送信して、ホストでなければそのユーザだけ削除する
def delete_user(ip):
    print(ip)

def read_processed_data(data):
    chat_name_len = int.from_bytes(data[:1], "big")
    operation_code = int.from_bytes(data[1:2], "big")
    state_code = int.from_bytes(data[2:3, "big"])

    chat_name = data[3:chat_name_len].decode('utf-8')
    user_name = data[3+chat_name_len:].decode('utf-8')
    
    return operation_code, state_code, chat_name, user_name

def process_tcp_data(rn_size, ope, state, payloads):
    rn_size_bytes = rn_size.to_bytes(1, "big")
    ope_bytes = ope.to_bytes(1, "big")
    state_byes = state.to_bytes(1, "big")
    payloads_bytes = payloads.encode('utf-8')

    return rn_size_bytes + ope_bytes + state_byes + payloads_bytes


