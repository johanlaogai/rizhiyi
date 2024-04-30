import selectors
import socket
 
sel = selectors.DefaultSelector()#生成一个selector对象
def accept(sock,mask):#mask连接数量（当前多少个客户端连接）
    conn, addr = sock.accept()  # conn：链接标记位,addr：对方的地址
    conn.setblocking(False)# 把该链接设置为非阻塞IO模式
    sel.register(conn, selectors.EVENT_READ, read)
    #把该客户端conn注册到sel#让sel监听
    #如果该连接再次活动就调用read该函数（往while循环看）
 
def read(conn, mask):
    data = conn.recv(1000)  #接收数据
    if data:#如果有数据
        print('echoing', repr(data), 'to', conn)
        conn.send(data)  # 返回数据
    else:
        print('closing', conn)#该连接断开了
        sel.unregister(conn)#取消注册
        conn.close()#关闭该连接
 
sock = socket.socket()#生成socket
sock.bind(('localhost', 10000))#绑定端口
sock.listen(100)#最多并发100
sock.setblocking(False)#设置非阻塞IO模式
sel.register(sock, selectors.EVENT_READ, accept)
#server对象sock注册到sel#让sel监听
#第一次客户端连接的时候经过下面的while True
#如果是新连接经过了while True判断以后会调用accept函数
 
 
while True:
    events = sel.select() #默认阻塞，有活动连接就返回活动的连接列表
    for key, mask in events:
            # events相当于sel监听的连接列表（里面目前监听sock本服务器的连接）
            # 由于server连接活动代表新的客户连接进来了
            # 新连接的客户端信息返回值放入key
            # key =客户端发起访问连接的信息
        callback = key.data  # callback = key.data = 调取accept函数
        callback(key.fileobj, mask)  
            #key.fileobj =文件句柄==还没有建立连接的客户端信息
            # accept(key.fileobj,mask) key.xx：实参 mask：实参