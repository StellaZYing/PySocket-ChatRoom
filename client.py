"""
Author: StellaZYing
Github: https://github.com/StellaZYing
Date: 2024-12-19 18:25:27
Copyright (c) 2024 by Hmily, All Rights Reserved.
Function: Multi person chat room
"""

# 客户端
import socket
import threading
import time
from tkinter import scrolledtext
from tkinter.filedialog import askopenfilename
from tkinter.ttk import Treeview
from stickers import * # 表情包模块
from login import * # 登录模块
from register import * # 注册模块

'''
参数：
    sock:定义一个实例化socket对象
    server:传递的服务器IP和端口
'''
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 使用tcp传输方式
server = ('127.0.0.1', 9999)
# 连接到服务器
sock.connect(server)


# 聊天室客户端类
class ChatClient():
    def __init__(self, name, scr1, scr2, fri_list, obj_emoji):
        self.name = name # 用户名
        self.scr1 = scr1 # 聊天显示框
        self.scr2 = scr2 # 聊天输入框
        self.fri_list = fri_list # 在线用户列表
        self.obj_emoji = obj_emoji # 表情包对象

    def toSend(self, *args):
        '''
        群聊消息发送功能
        - 获取用户输入框中的消息，发送到服务器
        - 更新聊天显示框
        '''
        self.msg = self.scr2.get(1.0, 'end').strip()   # 获取输入框内容
        self.send(self.msg)
        if self.msg != '':
            now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())  # 获取当前日期和时间
            self.scr1.configure(state=NORMAL) # 将聊天显示框设置为可编辑状态
            self.scr1.insert("end", "{} {}:\n".format(self.name, now_time), 'green') # 显示用户名和时间
            self.scr1.insert("end", self.msg + '' + '\n') # 显示聊天输入内容
            self.scr1.see(END)  # 将聊天窗口滚动到最新消息的位置
            self.scr2.delete('1.0', 'end')  # 清空输入框
            self.scr1.config(state=DISABLED)
            print(f'{self.name}：成功发送消息', self.msg.strip())
            return "break"

    def toPrivateSend(self, *args):
        '''
        私聊消息发送功能
        - 支持文本、文件、表情等多种消息类型
        '''
        self.msg = self.scr2.get(1.0, 'end').strip()  # 从文本框的开头到末尾获取内容，并去掉前后空白
        print(f"self.msg:{self.msg}")
        self.scr2.delete('1.0', 'end') # 清空输入框
        send_type, send_file = self.private_send(self.msg) # 调用 private_send 方法，判断消息的类型（文本或文件）
        if self.msg != '' and self.fri_list.selection() != (): # 如果消息内容非空且已选择私聊目标
            now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            self.scr1.configure(state=NORMAL)
            tar_name = self.fri_list.selection()[0] # 获取当前选中的好友名称（私聊目标）
            print('私聊用户名称:', tar_name)  # 打印私聊目标名称，便于调试
            self.scr1.insert("end", "{} {}:\n".format(self.name, now_time), 'green')
            if send_type == 'text': # 如果消息类型为文本
                self.scr1.insert("end", f'{self.msg}')  # 显示发送的文本消息内容
                self.scr1.insert("end", f'  |私聊{tar_name}\n', 'zise')   # 显示附加的私聊信息
                self.scr1.see(END)
                # self.scr2.delete('1.0', 'end') #冗余？
                self.scr1.config(state=DISABLED)  # 将聊天显示框设置为只读
                print(f'{self.name}：成功发送消息', self.msg, '[私聊]')   # 打印成功发送的消息内容，便于调试
            else: # 如果消息类型为文件
                self.scr1.insert("end", f'{send_file} 文件正在发送中，等待对方接收', 'shengzise') # 在聊天显示框中显示文件发送提示
                self.scr1.insert("end", f' |目标:{tar_name}\n', 'zise')
                self.scr1.see(END)
                print(f'{self.name}：成功发送文件', send_file, '[私聊]')

    def Get_File(self, filename):
        '''
        获取文件的路径、名称和扩展名
        '''
        if os.path.exists(self.msg):
            # 如果存在，可以进一步处理
            fpath, tempfilename = os.path.split(filename)
            fname, extension = os.path.splitext(tempfilename)
            print(f"Path: {fpath}")
            print(f"File name without extension: {fname}")
            print(f"Extension: {extension}")
        else:
            print("The provided path does not exist.")
        return fpath, fname, extension, tempfilename

    def send_file(self, fileType, fileName, filePath):
        '''
        向服务器发送文件信息
        - 用于私聊时发送文件的请求，通知服务器准备处理文件传输。
    
        参数:
        - fileType (str): 文件类型（如 "image" 表示图片文件，"normal-file" 表示普通文件等）。
        - fileName (str): 文件的名称（带后缀，如 "example.txt"）。
        - filePath (str): 文件的路径（表示文件在本地的存储位置）。
        '''
        message = {}
        message["chat_type"] = "private" # 消息类型：这里固定为 "private"，表示这是一个私聊操作
        message["message_type"] = "ask-file" # 消息功能类型：固定为 "ask-file"，表示请求发送文件的操作
        message["file_type"] = fileType # 文件类型：记录文件的种类（如图片、文档等）
        message["file_name"] = fileName # 文件名称：包含文件名和扩展名（如 "example.jpg"）
        message["send_user"] = self.name # 发送用户：当前登录用户的用户名（由 self.name 保存）
        message["recv_user"] = self.fri_list.selection()[0] # 接收用户：从好友列表中选中的用户，表示文件接收者
        message["content"] = filePath # 文件内容：这里使用文件的本地路径来表示具体的文件内容
        jsondata = json.dumps(message, ensure_ascii=False) # 将消息字典转换为 JSON 格式的字符串，方便网络传输。
        sock.sendall(jsondata.encode('utf-8'))# 将编码后的 JSON 数据通过 TCP 协议发送到服务器

    def cut_data(self, fhead, data):
        '''
        将文件数据分段发送给服务器。

        参数：
        - fhead (int): 文件数据的总长度（以字节为单位）。
        - data (bytes): 文件的二进制数据。

        功能：
        - 将大文件分成 1024 字节的块，逐块发送。
        - 防止数据发送过快导致服务器无法及时处理。
        '''
        for i in range(fhead // 1024 + 1): # 计算总共需要发送多少块数据 (每块大小为 1024 字节)
            time.sleep(0.0000000001)  # 防止数据发送太快，服务器来不及接收出错
            if 1024 * (i + 1) > fhead:  # 是否到最后
                sock.sendall(data[1024 * i:])  # 最后一次剩下的数据传给对方
                print('第' + str(i + 1) + '次发送文件数据')
            else:
                sock.sendall(data[1024 * i:1024 * (i + 1)]) # 发送完整的 1024 字节块数据
                print('第' + str(i + 1) + '次发送文件数据')

    def succ_recv(self, filename, sourcename):
        '''
        显示文件接收成功的提示信息。

        参数：
        - filename (str): 接收到的文件名。
        - sourcename (str): 文件发送者的名称。

        功能：
        - 在聊天窗口中显示接收文件的时间、文件名和发送者信息。
        - 格式化输出，使提示信息易于辨识。
        '''
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        self.scr1.configure(state=NORMAL)
        self.scr1.insert("end", "{} {}:\n".format(self.name, now_time), 'green')
        self.scr1.insert("end", f'你已成功接收 {filename}文件', 'shengzise') # 插入接收文件成功的提示信息，带有文件名
        self.scr1.insert("end", f' |来源:{sourcename}\n', 'zise') # 插入文件发送者的信息
        self.scr1.see(END) # 将聊天窗口滚动到最新消息的位置
        self.scr1.config(state=DISABLED) # 将聊天窗口设置为只读状态（DISABLED），防止用户手动编辑

    def succ_send(self, recv_user, filename):
        '''
        显示文件发送成功的提示信息。

        参数：
        - recv_user (str): 文件接收者的用户名。
        - filename (str): 发送的文件名。

        功能：
        - 在聊天窗口中显示文件发送成功的提示信息。
        - 格式化输出，使提示信息清晰易读。
        '''
        self.scr1.configure(state=NORMAL)
        self.scr1.insert("end", f'{filename}', 'shengzise')
        self.scr1.insert("end", f' |已成功发送给{recv_user}\n', 'zise')
        self.scr1.see(END)
        self.scr1.config(state=DISABLED)
        print(f'{self.name}：{filename}--文件成功发送文件给', recv_user)

    def send(self, msg):
        '''
        发送普通文本聊天消息。

        参数：
        - msg (str): 用户输入的聊天消息。

        功能：
        - 构造一个消息对象，包含消息的发送者、内容及消息类型等信息。
        - 将消息序列化为 JSON 格式后，通过网络发送给服务器。
        '''
        if msg != '': # 检查消息内容是否为空，只有非空消息才发送
            message = {}
            message["chat_type"] = "normal"
            message["message_type"] = "text"
            message["send_user"] = self.name
            message["content"] = msg.strip()
            jsondata = json.dumps(message, ensure_ascii=False) # 将消息字典序列化为 JSON 字符串，确保非 ASCII 字符（如中文）也能正确处理
            sock.sendall(jsondata.encode('utf-8')) # 将 JSON 数据编码为 UTF-8 字节流，并通过套接字发送给服务器

    def private_send(self, msg):
        """
        私聊消息发送功能，根据消息内容判断是普通文本还是文件类型，并执行相应的发送逻辑。

        参数：
        - msg (str): 用户输入的消息，可能是文本信息或文件路径。

        返回值：
        - tuple: 包含消息类型和文件名（如果是文件发送），否则返回空字符串。
        """
        fpath, fname, extension, tempfilename = self.Get_File(msg)  # 判断是路径还是信息
        # print(extension)
        if self.fri_list.selection() == (): # 如果用户未选择私聊对象，则弹出提示警告框
            messagebox.showwarning(title='提示', message='你没有选择发送对象！')
        # 判断输入内容的扩展名，执行不同类型文件的发送逻辑
        elif str(extension) in ('.py', '.doc', '.txt', '.docx'):  # 普通文件
            self.send_file('normal-file', tempfilename, msg) # 调用 send_file 发送普通文件
            return 'normal-file', tempfilename # 返回文件类型和文件名

        elif str(extension) in ('.jpg', '.png'): # 如果是图片文件
            self.send_file('image', tempfilename, msg) # 调用 send_file 发送图片
            return 'image', tempfilename

        elif str(extension) in ('.avi', '.mp4'): # 如果是视频文件
            self.send_file('video', tempfilename, msg)  # 调用 send_file 发送视频
            return 'video', tempfilename

        else: # 如果是文本消息
            message = {}
            message["chat_type"] = "private"
            message["message_type"] = "text"
            message["send_user"] = self.name
            message["recv_user"] = self.fri_list.selection()[0]
            message["content"] = msg.strip()
            jsondata = json.dumps(message, ensure_ascii=False)
            sock.sendall(jsondata.encode('utf-8'))
            return 'text', ''

    def recv(self):
        '''
        客户端消息接收功能
        - 持续监听来自服务器的消息并处理
        - 支持普通消息、私聊消息、文件接收等多种消息类型
        '''
        # 初始化连接服务器的消息
        message = {}
        message["message_type"] = "init_message"
        message["content"] = self.name   # 初始化消息内容为客户端用户名
        jsondata = json.dumps(message, ensure_ascii=False)  # 将消息序列化为 JSON 格式
        sock.sendall(jsondata.encode('utf-8')) # 发送初始化消息到服务器

        while True:
            try:
                # 接收服务器发来的数据
                data = sock.recv(1024)  # 从服务器接收数据（每次接收最大 1024 字节）
                print(f"data:{data}")
                if not data:
                    break
                # source = data.decode('utf-8') # 将数据解码为字符串
                json_data = json.loads(data.decode('utf-8'))  # 将 JSON 字符串反序列化为字典
                print(f"rec_from_sever:{json_data}")
                now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                self.scr1.configure(state=NORMAL) # 解锁消息显示区域，用于写入消息内容

                # 处理初始化消息
                if json_data['message_type'] == "init_message":
                    self.scr1.insert("end", f'欢迎{json_data["content"]}加入聊天室' + '\n', 'red')
                    print(f"json_data:{json_data['online_user']}")  # 打印当前在线用户列表
                    # 将在线用户添加到好友列表中
                    #user_list = eval(json_data["online_user"])
                    user_list = json_data["online_user"]
                    for user in user_list:
                        if str(user) not in self.fri_list.get_children() and str(user) != self.name:  # 如果不在列表中
                            self.fri_list.insert('', 2, str(user), text=str(user).center(24), values=("1"), tags='其他用户')
                    print(json_data["content"] + '进入了聊天室...')

                # 处理离开消息
                elif json_data['message_type'] == "leave_message":
                    self.scr1.insert("end", f'{json_data["content"]}离开了聊天室...' + '\n', 'red') # 显示离开消息
                    if json_data["content"] in self.fri_list.get_children():  # 从好友列表中移除离开的用户
                        self.fri_list.delete(json_data["content"])
                    print(json_data["content"] + '离开了聊天室...')

                # 处理普通群聊消息
                elif json_data['chat_type'] == "normal":
                    if json_data['message_type'] == "text":  # 普通文本消息
                        self.scr1.insert("end", "{} {}:\n".format(json_data['send_user'], now_time), 'green')
                        self.scr1.insert("end", json_data['content'] + '\n')

                    elif json_data['message_type'] == "stickers":  # 表情包消息
                        self.scr1.configure(state=NORMAL)
                        self.scr1.insert("end", "{} {}:\n".format(json_data['send_user'], now_time), 'green')
                        dics = self.obj_emoji.dics  # 获取表情包字典
                        if json_data['content'] in dics:  # 如果表情包在字典中
                            mes = json_data['content']
                            self.scr1.image_create(END, image=dics[mes])
                            self.scr1.insert("end", '\n', 'zise')
                            self.scr1.see(END)
                        self.scr1.config(state=DISABLED)
                        print(f'收到{json_data["send_user"]}发的表情包：', json_data['content'])

                # 处理私聊消息
                elif json_data['chat_type'] == "private":
                    if json_data['message_type'] == "text":  # 私聊文本消息
                        self.scr1.insert("end", "{} {}:\n".format(json_data['send_user'], now_time), 'green')
                        self.scr1.insert("end", json_data['content'])
                        self.scr1.insert("end", f'  |私聊消息\n', 'zise')
                        print(f'[私聊]收到{json_data["send_user"]}的消息：', json_data['content'])

                    elif json_data['message_type'] == "stickers":  # 私聊表情包消息
                        self.scr1.configure(state=NORMAL)
                        self.scr1.insert("end", "{} {}:\n".format(json_data['send_user'], now_time), 'green')
                        dics = self.obj_emoji.dics
                        if json_data['content'] in dics:
                            mes = json_data['content']
                            self.scr1.image_create(END, image=dics[mes])
                            self.scr1.insert("end", f'  |私聊消息\n', 'zise')
                            self.scr1.see(END)
                        self.scr1.config(state=DISABLED)
                        print(f'[私聊]收到{json_data["send_user"]}发的表情包：', json_data['content'])

                    elif json_data['message_type'] == "ask-file":  # 私聊文件消息
                        fileType = json_data["file_type"]
                        self.scr1.configure(state=NORMAL)
                        self.scr1.insert("end", "{} {}:\n".format(json_data["send_user"], now_time), 'green')
                        self.scr1.insert("end", f'正在向你发送一个{fileType}文件...\n', 'shengzise')
                        self.scr1.see(END)
                        self.scr1.config(state=DISABLED)

                        # 判断是否接收文件
                        flag = messagebox.askyesno(title='提示',
                                                message=f'{json_data["send_user"]}向你发送了一个{fileType}\n你是否要接收和保存？')
                        if flag:
                            json_data['message_type'] = "isRecv"
                            json_data['isRecv'] = "true"  # 同意接收文件
                            jsondata = json.dumps(json_data, ensure_ascii=False)
                            sock.sendall(jsondata.encode('utf-8'))

                        else:  # 用户拒绝接收文件
                            json_data['message_type'] = "isRecv"
                            json_data['isRecv'] = "false"
                            jsondata = json.dumps(json_data, ensure_ascii=False)
                            sock.sendall(jsondata.encode('utf-8'))
                            self.scr1.configure(state=NORMAL)
                            self.scr1.insert("end", "{} {}:\n".format(self.name, now_time), 'green')
                            self.scr1.insert("end", f'你已拒绝接收{fileType}', 'shengzise')
                            self.scr1.insert("end", f' |来源:{json_data["send_user"]}\n', 'zise')
                            self.scr1.see(END)
                            self.scr1.config(state=DISABLED)

                    elif json_data['message_type'] == "isRecv":  # 处理发送文件的数据
                        if json_data['isRecv'] == "true":  # 对方同意接收文件
                            if json_data["file_type"] in ('normal-file', 'image', 'video'):
                                f = open(json_data["content"], 'rb')  # r方式读到str格式数据，rb方式读到bytes型。
                                data = f.read()  # 读取文件数据
                                fhead = len(data)  # 计算文件大小
                                print('文件大小:', fhead)

                                # 构造文件数据头消息
                                message = {}
                                message["chat_type"] = "private"
                                message["message_type"] = "file-data"
                                message["file_length"] = str(fhead)  # 文件长度
                                message["file_name"] = json_data["file_name"]
                                message["send_user"] = json_data["send_user"]
                                message["recv_user"] = json_data["recv_user"]
                                message["content"] = ''  # 内容为空，用于标记文件数据开始
                                jsondata = json.dumps(message, ensure_ascii=False)  # 序列化消息
                                sock.sendall(jsondata.encode('utf-8')) # 发送到服务器

                                print('开始发送文件数据...')
                                self.cut_data(fhead, data)  # 调用分片函数cut_data发送文件数据
                                print('文件数据已成功发送到服务器！')
                                f.close() # 关闭文件句柄
                                
                        else:  # 对方拒绝接收文件
                            self.scr1.insert("end", "{} {}:\n".format(json_data["send_user"], now_time), 'green')
                            self.scr1.insert("end", f"对方拒绝接收你发的{json_data['file_name']}文件\n", 'chengse')
                            self.scr1.see(END)

                    elif json_data['message_type'] == "file-data":  # 接收文件数据
                        print('正在接收文件')
                        filename = json_data['file_name']
                        data_size = int(json_data['file_length'])
                        print('文件大小为' + str(data_size))
                        recvd_size = 0  # 初始化已接收数据大小
                        data_total = b''  # 存储完整文件数据
                        j = 0  # 计数变量

                        # 循环接收文件数据
                        while not recvd_size == data_size:
                            j = j + 1
                            if data_size - recvd_size > 1024:  # 如果剩余数据大于1024字节
                                data, addr = sock.recvfrom(1024)  # 接收 1024 字节数据
                                recvd_size += len(data)
                                print('第' + str(j) + '次收到文件数据')
                            else:  # 最后一片
                                data, addr = sock.recvfrom(1024) 
                                recvd_size = data_size  # 标记文件接收完成
                                print('第' + str(j) + '次收到文件数据')
                            data_total += data  # 将接收到的数据拼接

                        # 将接收的文件数据写入到本地文件
                        f = open(filename, 'wb')  # 收到的数据是bytes型，可以直接用wb写入，不用Decode。若用的是w方式，要对接收数据decode后写入
                        f.write(data_total)
                        f.close()
                        print(filename, '文件接收完成！')

                        self.succ_recv(filename, json_data["send_user"])  # 调用成功接收文件的处理函数

                        # 通知服务器文件接收成功
                        message = {}
                        message["chat_type"] = "private"
                        message["message_type"] = "Recv_msg"
                        message["Recv_msg"] = "true"  # 接收成功标记 ACK
                        message["file_length"] = json_data['file_length']
                        message["file_name"] = json_data["file_name"]
                        message["send_user"] = json_data["recv_user"]
                        message["recv_user"] = json_data["send_user"]
                        jsondata = json.dumps(message, ensure_ascii=False)
                        sock.sendall(jsondata.encode('utf-8'))  # 发送接收成功消息到服务器

                    elif json_data['message_type'] == "Recv_msg":  # 文件发送者收到接收者确认消息
                        if json_data['Recv_msg'] == "true":
                            recv_user = json_data['recv_user']
                            filename = json_data['file_name']
                            self.succ_send(recv_user, filename)  # 调用文件发送成功处理函数
            except Exception as e:
                print(f"Error: {e}")
                break


class ChatUI():
    def __init__(self, root):
        self.root = root

    def JieShu(self):
        flag = messagebox.askokcancel(title='提示', message='你确定要退出聊天室吗？')
        # sock.sendall(f":{self.name} 已退出聊天室...".encode('utf-8'),server)
        if flag:
            message = {}
            message["message_type"] = "leave_message"
            message["content"] = self.name
            jsondata = json.dumps(message, ensure_ascii=False)
            sock.sendall(jsondata.encode('utf-8'))
            sys.exit(0)

    def openfile(self):
        r = askopenfilename(title='打开文件', filetypes=[('All File', '*.*'), ('文本文件', '.txt'), ('python', '*.py *.pyw')])
        self.scr2.insert(INSERT, r)

    def chat(self, usename):
        self.name = usename
        self.root.title('聊天室--用户名:' + self.name)
        sw = self.root.winfo_screenwidth()  # 计算水平距离
        sh = self.root.winfo_screenheight()  # 计算垂直距离
        w = 1720  # 宽
        h = 1120  # 高
        x = (sw - w) / 2
        y = (sh - h) / 2
        self.root.geometry("%dx%d+%d+%d" % (w, h, (x + 200), (y + 400)))
        self.root.iconbitmap(r'images/icon/chat.ico')  # 设置左上角窗口图标

        self.root.resizable(0, 0)  # 窗口设置为不可放大缩小
        # 告诉操作系统使用程序自身的dpi适配
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        # 获取屏幕的缩放因子
        ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
        # 设置程序缩放
        self.root.tk.call('tk', 'scaling', ScaleFactor / 75)

        self.root.resizable(1, 1)  # 窗口设置为不可放大缩小
        self.scr1 = scrolledtext.ScrolledText(self.root, height=18, font=('黑体', 13))
        self.scr1.tag_config('green', foreground='#008C00', font=('微软雅黑', 10))  # 设置组件字体颜色
        self.scr1.tag_config('red', foreground='red')
        self.scr1.tag_config('zise', foreground='#aaaaff')
        self.scr1.tag_config('shengzise', foreground='#9d4cff')
        self.scr1.tag_config('chengse', foreground='#ff7f27')

        # 创建树形列表
        self.fri_list = Treeview(self.root, height=30, show="tree")
        self.fri_list.insert('', 0, 'online_user', text='在线用户'.center(10, '-'), values=("1"), tags='在线用户')
        if self.name not in self.fri_list.get_children():  # 如果不在列表中
            self.fri_list.insert('', 1, 'me', text=self.name.center(24), values=("1"), tags='自己')  # 自己在列表中颜色为红色
        self.fri_list.grid(row=1, column=2, rowspan=7, sticky=N)
        self.fri_list.tag_configure('在线用户', foreground='#aa5500', font=('黑体', 13))  # 设置组件字体颜色
        self.fri_list.tag_configure('自己', foreground='red', font=('微软雅黑', 10))  # 设置组件字体颜色
        self.fri_list.tag_configure('其他用户', font=('微软雅黑', 10))  # 设置组件字体颜色

        self.scr1.grid(row=1, column=1)
        l0 = Label(self.root, text='')
        l0.grid(row=2)
        l1 = Label(self.root, text='下框输入你要的发送的内容：')
        l1.grid(row=3, column=1)
        self.scr2 = scrolledtext.ScrolledText(self.root, height=6, font=('黑体', 13))
        self.scr2.grid(row=4, column=1)
        l2 = Label(self.root, text='')
        l2.grid(row=5)
        tf = Frame(self.root)
        tf.grid(row=6, column=1)

        obj_emoji = Emoji(self.root, self.send_mark)
        chat = ChatClient(self.name, self.scr1, self.scr2, self.fri_list, obj_emoji)

        b0 = Button(tf, text=' 表情包 ', command=obj_emoji.express)
        b0.grid(row=1, column=0, padx=20)
        b1 = Button(tf, text=' 群发 ', command=chat.toSend)
        b1.grid(row=1, column=1, padx=20)
        b4 = Button(tf, text=' 私聊 ', command=chat.toPrivateSend)
        b4.grid(row=1, column=2, padx=20)
        b2 = Button(tf, text=' 传文件 ', command=self.openfile)
        b2.grid(row=1, column=3, padx=20, pady=20)
        b3 = Button(tf, text=' 发邮件 ', command='')
        b3.grid(row=1, column=4, padx=20)
        b4 = Button(tf, text=' 开启FTP ', command='')
        b4.grid(row=1, column=5, padx=20)
        b5 = Button(tf, text=' 登录FTP ', command='')
        b5.grid(row=1, column=6, padx=20)
        b6 = Button(tf, text=' 退出 ', command=self.JieShu)
        b6.grid(row=1, column=7, padx=20)

        tr = threading.Thread(target=chat.recv, args=(),
                              daemon=True)
        # daemon=True 表示创建的子线程守护主线程，主线程退出子线程直接销毁
        tr.start()
        self.root.protocol("WM_DELETE_WINDOW", self.JieShu)

    def send_mark(self, exp, dics):
        stick_code = exp
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        self.scr1.configure(state=NORMAL)
        self.scr1.insert("end", "{} {}:\n".format(self.name, now_time), 'green')
        message = {}
        message["message_type"] = "stickers"
        message["send_user"] = self.name
        message["content"] = stick_code

        if self.fri_list.selection() != () and self.fri_list.selection()[0] != 'me':
            message["chat_type"] = "private"
            message["recv_user"] = self.fri_list.selection()[0]
            jsondata = json.dumps(message, ensure_ascii=False)
            sock.sendall(jsondata.encode('utf-8'))
            self.scr1.image_create(END, image=dics[stick_code])
            self.scr1.insert("end", f'  |私聊{self.fri_list.selection()[0]}\n', 'zise')
            print(f'表情消息:{stick_code}发送成功！[私聊{self.fri_list.selection()[0]}]')
        else:
            message["chat_type"] = "normal"
            jsondata = json.dumps(message, ensure_ascii=False)
            sock.sendall(jsondata.encode('utf-8'))
            self.scr1.image_create(END, image=dics[stick_code])
            print(f'表情消息:{stick_code}发送成功！')
            self.scr1.insert(END, '\n')
        self.scr1.see(END)
        self.scr1.config(state=DISABLED)


if __name__ == '__main__':
    root = Tk()
    Main = ChatUI(root)
    Login(Register, Main.chat, root)
    root.mainloop()
