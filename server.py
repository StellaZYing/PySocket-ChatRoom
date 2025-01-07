import socket  # 导入socket模块，用于网络通信
from need_module import json, logging, time  # 导入其他需要的模块，分别用于JSON处理、日志记录和时间处理
import threading

def handle_client(conn, addr, users):
    with conn:
        print('Connected by', addr)
        while True:
            try:
                data = conn.recv(1024)
                print(f"rev_data: {data}")
                if not data:
                    break
                json_data = json.loads(data.decode('utf-8'))
                print(f"json_data: {json_data}")

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
                    print(f"recv_user: {recv_user}")
                    print(f"send_user: {send_user}")
                    
                    if recv_user in users and json_data['message_type'] != "file-data":
                        users[recv_user].sendall(data)
                    else:
                        # 文件传输逻辑
                        filename = json_data['file_name']  # 获取文件名
                        data_size = int(json_data.get('file_length', 0))  # 获取文件大小
                        
                        print(f'准备接收文件: {filename}, 大小: {data_size} bytes')
                        
                        recvd_size = 0  # 已接收的数据大小
                        data_total = b''  # 存储所有接收到的文件数据
                        
                        # 循环接收文件数据，直到接收到完整的文件
                        while recvd_size < data_size:
                            chunk = conn.recv(min(1024, data_size - recvd_size))
                            if not chunk:
                                raise Exception("File transfer was interrupted.")
                            data_total += chunk
                            recvd_size += len(chunk)
                            print(f'已接收: {recvd_size}/{data_size} bytes')

                        # 构建文件传输消息
                        message = {
                            "chat_type": "private",  # 消息类型为私聊
                            "message_type": "file-data",  # 消息类型为文件数据
                            "file_length": str(len(data_total)),  # 文件大小
                            "file_name": filename,  # 文件名
                            "send_user": send_user,  # 发送者
                            "recv_user": recv_user,  # 接收者
                            "content": ''  # 内容为空，标记文件数据开始
                        }
                        jsondata = json.dumps(message, ensure_ascii=False)  # 序列化消息
                        users[recv_user].sendall(jsondata.encode('utf-8'))  # 发送给接收者

                        print('开始发送文件数据...')
                        # 按1024字节分块发送文件数据
                        for i in range(0, len(data_total), 1024):
                            users[recv_user].sendall(data_total[i:i+1024])
                            print(f'已发送: {i+1024}/{len(data_total)} bytes')

                        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                        print(f'{now_time}: "{filename}" 文件发送完成! from {addr[0]}:{addr[1]} [目标:{recv_user}] at {now_time}')

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
