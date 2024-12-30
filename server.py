import socket  # 导入socket模块，用于网络通信
from need_module import json, logging, time  # 导入其他需要的模块，分别用于JSON处理、日志记录和时间处理
import threading

def handle_client(conn, addr, users):
    with conn:
        print('Connected by', addr)
        while True:
            try:
                data = conn.recv(1024)
                print(f"data:{data}")
                if not data:
                    break
                json_data = json.loads(data.decode('utf-8'))
                print(json_data)

                # 处理初始化消息（用户加入）
                if json_data['message_type'] == "init_message":
                    username = json_data['content']
                    if username not in users:
                        users[username] = conn
                        user_list = list(users.keys())
                        json_data['online_user'] = user_list
                        json_str = json.dumps(json_data, ensure_ascii=False)
                        for client_conn in users.values():
                            client_conn.sendall(json_str.encode('utf-8'))
                            print(f"sever_send_all:{json_str}")
                        print(f'{username}进入了聊天室')
                        print(f'当前在线用户{user_list}')

                # 处理离开消息
                elif json_data['message_type'] == "leave_message":
                    username = json_data['content']
                    if username in users:
                        del users[username]
                        user_list = list(users.keys())
                        for client_conn in users.values():
                            client_conn.sendall(data)
                        print(f'{username}离开了聊天室')
                        print(f'当前在线用户{user_list}')
                        break

                # 处理普通消息
                elif json_data['chat_type'] == "normal":
                    if json_data['message_type'] != "file":
                        for client_conn in users.values():
                            if client_conn != conn:
                                client_conn.sendall(data)

                # 处理私聊消息
                elif json_data['chat_type'] == "private":
                    recv_user = json_data['recv_user']
                    send_user = json_data['send_user']
                    if recv_user in users and json_data['message_type'] != "file-data":
                        users[recv_user].sendall(data)
                    else:
                        # 文件传输逻辑应在此处实现
                        pass

            except ConnectionResetError:
                logging.warning('Someone left unexpectedly.')
                break


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 允许快速重启服务
    s_addr = ('0.0.0.0', 9999)
    s.bind(s_addr)
    s.listen(5)
    
    users = {}  # 用于存储在线用户的连接对象，键为用户名，值为该用户的连接对象

    print('----------服务器已启动-----------')
    print('Bind TCP on ' + str(s_addr))
    print('等待客户端数据...')

    try:
        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr, users))
            thread.setDaemon(True)
            thread.start()
            logging.info('连接来自: %s', addr)
    except KeyboardInterrupt:
        print('服务器正在关闭...')
    finally:
        s.close()


if __name__ == '__main__':
    main()  # 调用主函数，启动服务器
