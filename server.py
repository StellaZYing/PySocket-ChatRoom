import socket  # 导入socket模块，用于网络通信
from need_module import json, logging, time  # 导入其他需要的模块，分别用于JSON处理、日志记录和时间处理


def main():
    # 创建UDP协议的socket对象，使用IPv4地址（AF_INET）和UDP协议（SOCK_DGRAM）
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # 绑定IP地址和端口（127.0.0.1代表本机，9999为端口）
    s_addr = ('127.0.0.1', 9999)
    s.bind(s_addr)  # 绑定地址和端口到服务器

    logging.info('UDP Server on %s:%s...', s_addr[0], s_addr[1])  # 记录日志，输出服务器运行的IP和端口

    user = {}  # 用于存储在线用户信息的字典，键为用户名，值为该用户的地址

    print('----------服务器已启动-----------')
    print('Bind UDP on ' + str(s_addr))  # 打印服务器绑定的信息
    print('等待客户端数据...')  # 提示等待客户端消息

    while True:
        try:
            # 等待接收客户端的消息，每次接收的数据最大为1024字节，数据和地址存放在data和addr中
            data, addr = s.recvfrom(1024)  
            json_data = json.loads(data.decode('utf-8'))  # 解码接收到的数据并将其转换为字典形式
            print(json_data)  # 打印收到的消息内容

            # 如果消息类型为初始化消息（用户加入）
            if json_data['message_type'] == "init_message":
                # 如果用户不在当前用户列表中，则添加该用户
                if json_data['content'] not in user:
                    user[json_data['content']] = addr  # 将用户名与地址绑定
                    user_list = [i for i in user.keys()]  # 获取当前所有在线用户
                    json_data['online_user'] = f'{user_list}'  # 更新在线用户列表
                    json_str = json.dumps(json_data, ensure_ascii=False)  # 将消息转为JSON格式
                    # 向所有在线用户广播该消息
                    for address in user.values():
                        s.sendto(json_str.encode('utf-8'), address)  # 发送给每个在线用户
                    print(json_data['content'] + '进入了聊天室')  # 输出新加入的用户
                    print(f'当前在线用户{user_list}')  # 打印当前在线用户列表

            # 如果消息类型为离开消息（用户退出）
            elif json_data['message_type'] == "leave_message":
                # 如果用户存在于在线列表中，则移除该用户
                if json_data['content'] in user:
                    user.pop(json_data['content'])  # 移除退出的用户
                    user_list = [i for i in user.keys()]  # 获取更新后的在线用户列表
                    for address in user.values():
                        s.sendto(data, address)  # 向所有在线用户广播该消息
                    print(json_data['content'] + '离开了聊天室')  # 输出退出的用户
                    print(f'当前在线用户{user_list}')  # 打印当前在线用户列表
                    continue  # 继续循环，等待下一次消息

            # 如果消息类型为普通消息（群聊）
            elif json_data['chat_type'] == "normal":
                if json_data['message_type'] != "file":  # 排除文件消息
                    # 向除发送者外的所有在线用户发送消息
                    for address in user.values():
                        if address != addr:
                            s.sendto(data, address)  # 发送数据给其他在线用户

            # 如果消息类型为私聊消息
            elif json_data['chat_type'] == "private":
                recv_user = json_data['recv_user']  # 获取接收用户的用户名
                send_user = json_data['send_user']  # 获取发送用户的用户名
                # 如果不是文件数据，则发送普通消息
                if json_data['message_type'] != "file-data":
                    s.sendto(data, user[recv_user])  # 发送消息到接收者

                else:  # 如果是文件数据
                    filename = json_data['file_name']  # 获取文件名
                    data_size = int(json_data['file_length'])  # 获取文件大小
                    print('文件大小为' + str(data_size))  # 打印文件大小
                    recvd_size = 0  # 已接收的数据大小
                    data_total = b''  # 存储所有接收到的文件数据
                    j = 0  # 接收数据的计数器

                    # 循环接收文件数据，直到接收到完整的文件
                    while not recvd_size == data_size:
                        j = j + 1
                        if data_size - recvd_size > 1024:  # 如果剩余数据大于1024字节
                            data, addr = s.recvfrom(1024)  # 接收1024字节数据
                            recvd_size += len(data)  # 累加已接收的数据大小
                            print('第' + str(j) + '次收到文件数据')
                        else:  # 如果接收的是最后一部分数据
                            data, addr = s.recvfrom(1024)
                            recvd_size = data_size  # 更新接收大小为文件总大小
                            print('第' + str(j) + '次收到文件数据')
                        data_total += data  # 将接收到的数据追加到文件内容中

                    # 获取文件数据总长度
                    fhead = len(data_total)
                    message = {}
                    message["chat_type"] = "private"  # 消息类型为私聊
                    message["message_type"] = "file-data"  # 消息类型为文件数据
                    message["file_length"] = str(fhead)  # 文件大小
                    message["file_name"] = json_data["file_name"]  # 文件名
                    message["send_user"] = json_data['send_user']  # 发送者
                    message["recv_user"] = json_data['recv_user']  # 接收者
                    message["content"] = ''  # 内容为空，标记文件数据开始
                    jsondata = json.dumps(message, ensure_ascii=False)  # 序列化消息
                    s.sendto(jsondata.encode('utf-8'), user[recv_user])  # 发送给接收者

                    print('开始发送文件数据...')
                    # 按1024字节分块发送文件数据
                    for i in range(len(data_total) // 1024 + 1):
                        time.sleep(0.0000000001)  # 防止数据发送过快，服务器来不及接收
                        if 1024 * (i + 1) > len(data_total):  # 如果是最后一块数据
                            s.sendto(data_total[1024 * i:], user[recv_user])  # 发送最后一部分数据
                            print('第' + str(i + 1) + '次发送文件数据')
                        else:  # 否则按1024字节发送
                            s.sendto(data_total[1024 * i:1024 * (i + 1)], user[recv_user])
                            print('第' + str(i + 1) + '次发送文件数据')

                    # 打印文件发送完成的时间和相关信息
                    now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                    print('%s: "%s" 文件发送完成! from %s:%s [目标:%s] at %s' % (send_user, filename, addr[0], addr[1], user[recv_user], now_time))

        except ConnectionResetError:
            logging.warning('Someone left unexpectedly.')  # 捕获异常，如果某个客户端意外离开，则记录警告信息


if __name__ == '__main__':
    main()  # 调用主函数，启动服务器
