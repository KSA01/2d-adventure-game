#mySocket.py

import socket
import threading
import time
import json
import queue

# None = no connection, False = Trying to connect, idx = is connected and this is the connection
_connections =[None]
_connLock = threading.Lock()

_messages = {}
_mesLock = threading.Lock()

# None = no connection, False = Trying to connect, True = is connected
def IsConnected(index):
    global _connections
    global _connLock

    with _connLock:
        if index >= len(_connections):
            return None
        if _connections[index] is not None:
            if isinstance(_connections[index], bool) and _connections[index] == False:
                return False
            return True
    return None

def Init(asListener, index=0, port=None, address=None):
    global _connections
    global _connLock

    with _connLock:
        while len(_connections) <= index:
            _connections.append(None)
        _connections[index] = False

    if asListener:
        t = threading.Thread(target=_Listener, args=[index, port])
    else:
        t = threading.Thread(target=_Connector, args=[address, port])
    t.start()

def GetMessage(name):
    global _messages
    global _mesLock

    with _mesLock:
        if not name in _messages:
            return None
        mesList = _messages[name]
        if mesList.empty():
            return None
        mes = mesList.get()

    return mes

def SendMessageLocal(name, mes):
    global _messages
    global _mesLock

    with _mesLock:
        if not name in _messages:
            _messages[name] = queue.Queue()
        _messages[name].put(mes)

def SendMessage(name, mes, source=None, target=None):
    global _connections
    global _connLock

    if target is None: # Send to all targets that are not source
        with _connLock:
            ln = len(_connections)
        for i in range(ln):
            with _connLock:
                cn = _connections[i]

            if cn is None or i == source:
                continue

            try:
                cn.sendall(bytearray(json.dumps({"dst":name, "msg":mes})+"\x01", "utf-8"))
            except:
                with _connLock:
                    cn = _connections[i] = None
    else:
        with _connLock:
            if target < len(_connections):
                cn = _connections[target]
            else:
                cn = None

        if cn:
            try:
                cn.sendall(bytearray(json.dumps({"dst":name, "msg":mes})+"\x01", "utf-8"))
            except:
                with _connLock:
                    cn = _connections[target] = None


def _Process(idx):
    global _connections
    global _connLock
    global _messages
    global _mesLock

    data = ""
    with _connLock:
        cn = _connections[idx]
    while cn:
        try:
            d = cn.recv(64)
        except Exception as e:
            break
        if not d:
            break
        
        data += d.decode("utf-8")
        index = data.find("\x01")
        if index != -1:
            msg = json.loads(data[:index])
            data = data[index+1:]

            ky = msg["dst"]
            ms = msg["msg"]
            #print(f"{ky}:{ms}")

            with _mesLock:
                if not ky in _messages:
                    _messages[ky] = queue.Queue()
                _messages[ky].put(ms)

        with _connLock:
            cn = _connections[idx]

    with _connLock:
        _connections[idx] = None
    print("Disconnected " + str(idx))

#assumes we are already in an independent thread
def _Listener(index, port):
    global _connections
    global _connLock

    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    conn.bind(('127.0.0.1', port))
    conn.listen()
    conn.settimeout(25)
    try:
        conn, addr = conn.accept()
    except socket.timeout:
        with _connLock:
            _connections[index] = None
        return
    conn.settimeout(None)
    with _connLock:
        _connections[index] = conn

    _Process(index)

#assumes we are already in an independent thread
def _Connector(address, port):
    global _connections
    global _connLock

    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    connected = False
    tries = 25
    conn.settimeout(1)
    while not connected and tries > 0:
        try:
            conn.connect((address, port))
            connected = True
        except Exception as e:
            time.sleep(1)
            tries -= 1
    conn.settimeout(None)

    if connected:
        with _connLock:
            _connections[0] = conn
        _Process(0)
    else:
        with _connLock:
            _connections[0] = None