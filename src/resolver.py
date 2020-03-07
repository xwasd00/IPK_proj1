import socket
import re

bad_request = b'HTTP/1.1 400 Bad Request\r\n\r\n'
method_not_allowed = b'HTTP/1.1 405 Method Not Allowed\r\n\r\n'
ok = b'HTTP/1.1 200 OK\r\n\r\n'

def resolve(n, t, to_send):
    if t == "A":
        try:
            ret = socket.gethostbyname(n)
        except socket.error:
            return to_send
        to_send += bytes(ret, "UTF-8") + b':PTR\r\n'
        return to_send
    elif t == "PTR": #and re.findall(r"\d+.\d+.\d+.\d+", n):
        try:
            a,b,ret = socket.gethostbyaddr(n)
        except socket.error:
            return to_send
        to_send += bytes(ret[0], "UTF-8") + b':A\r\n'
        return to_send
    else:
        return bad_request


def get(header, to_send):
    arr = header.split("\r\n")
    line = re.findall(r"GET (\S+) HTTP/1.1", arr[0])
    if line:
        print (line[0])
        my_name = re.findall(r"/resolve\?name=(\S+)&type=(?:\w+)", line[0])
        my_type = re.findall(r"/resolve\?name=(?:\S+)&type=(A|PTR)", line[0])
        if my_name and my_type:
            to_send = ok
            to_send = resolve(my_name[0], my_type[0], to_send)
    return to_send


def post(header, body, to_send):
    arr = header.split("\r\n")
    if arr[0] == "POST /dns-query HTTP/1.1":
        to_send = ok
        print (body)
        #TODO
    return to_send



def length(header):
    match = re.findall(r"Content-Length: (\d+)",header)
    if match:
        return int(match[0])
    return 0

if __name__ == "__main__":
    HOST = ''
    PORT = 5005
    BUFF_SIZE = 4096
    to_send = bad_request
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    
    s.bind((HOST, PORT))
    s.listen()
    while 1:
        conn, addr = s.accept()
        #conn.settimeout(500)
        data = conn.recv(BUFF_SIZE)
        part = data.split(b'\r\n\r\n')

        if part[0][0:3] == b'GET':
            to_send = get( part[0].decode("UTF-8"), to_send )
        elif part[0][0:4] == b'POST':
            l = length(part[0].decode("UTF-8"))
            if (l - BUFF_SIZE > 512):
                data = conn.recv(l)
                part[1] += data
            to_send = post(part[0].decode("UTF-8"), part[1].decode("UTF-8"), to_send)
        else:
            #bad request
            to_send = method_not_allowed
        
        conn.sendall(to_send)
        conn.close()

    s.close()
