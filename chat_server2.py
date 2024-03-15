import socket
import time

# 新規チャット作成用
chat_create_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
chat_in_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = '0.0.0.0'
server_port = 9001
unit_data = 4096
users = {}
TIMEOUT_SECONDS = 30
TIMEOUT_CHECK_INTERVAL = 20

def check_users_timeout():
    currentime = time.time()
    remove_users = []
    for useraddress, user_info in users.items():
        if currentime - user_info['last_activity'] > TIMEOUT_SECONDS:
            print(f"ユーザー {user_info['username']} がタイムアウトしました。")
            remove_users.append(useraddress)
    
    for useraddress in remove_users:
        del users[useraddress]

    
# ユーザーの最後の活動時間を更新する関数
def update_user_activity(user_address):
    if user_address in users:
        users[user_address]["last_activity"] = time.time()



# 受信したデータをユーザ名とメッセージ部に分けて、タプルで返す
def process_data(data):
    username_length = int.from_bytes(data[:1], "big")
    username = data[1:1+username_length].decode("utf-8")
    message = data[1+username_length:].decode("utf-8")
    print("message recieved from {}. username's length is {}".format(username, username_length))
    if len(message) == 0:
        raise Exception('No data to read from client.')

    return username, message

# 送信用データ加工
def send_process(username, message):
    username_length = len(username).to_bytes(1, "big")
    usrname_bytes = username.encode('utf-8')
    message_bytes = message.encode('utf-8')
    return  username_length + usrname_bytes + message_bytes


# 接続登録されている全ユーザにメッセージ送信する
def send_to_users(message):
    for useraddress, userobj in users.items():
        byte_data = send_process(userobj["username"], message)
        chat_in_sock.sendto(byte_data, useraddress)
         

# hashmapにuserとuser_addressを格納
def create_user(username, user_address):
    users[user_address] = {"username": username, "last_activity": time.time(), "state": "active"}


def disconnect_user(username):
    print(username)


chat_in_sock.bind((server_address, server_port))

while True:
    print('\nwaiting to receive message')
    

    try: 
        check_users_timeout()
        data, address = chat_in_sock.recvfrom(unit_data)
        print("message recieved from {}".format(address))
        username, message = process_data(data)
        create_user(username, address)
        send_to_users(message)
        

    except Exception as e:
        print('Error: ' + str(e))
        


    