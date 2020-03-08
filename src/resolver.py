import socket
import re
import threading
import sys

bad_request = b'HTTP/1.1 400 Bad Request\r\n\r\n'
not_found = b'HTTP/1.1 404 Not Found\r\n\r\n'
method_not_allowed = b'HTTP/1.1 405 Method Not Allowed\r\n\r\n'
ok = b'HTTP/1.1 200 OK\r\n\r\n'

def resolve(n, t, to_send):
    if t == "A" and not re.findall(r"(\d+.\d+.\d+.\d+)", n):
        try:
            ret = socket.gethostbyname(n)
        except socket.error:
            if to_send == ok or to_send == not_found:
                return not_found
            return to_send
        to_send += bytes(n, "UTF-8") + b':A=' + bytes(ret, "UTF-8") + b'\r\n'
    elif t == "PTR" and re.findall(r"(\d+.\d+.\d+.\d+)", n):
        try:
            a,b,ret = socket.gethostbyaddr(n)
        except socket.error:
            if to_send == ok or to_send == not_found:
                return not_found
            return to_send
        to_send += bytes(n, "UTF-8") + b':PTR=' + bytes(a, "UTF-8") + b'\r\n'
    return to_send

def get(header, to_send):
    arr = header.split("\r\n")
    line = re.findall(r"GET (\S+) HTTP/", arr[0])
    if line:
        my_name = re.findall(r"/resolve\?name=(\S+)&type=(?:\w+)", line[0])
        my_type = re.findall(r"/resolve\?name=(?:\S+)&type=(A|PTR)", line[0])
        if my_name and my_type:
            to_send = ok
            if my_type[0] == "A" and not re.findall(r"(\d+.\d+.\d+.\d+)", my_name[0]):
                try:
                    ret = socket.gethostbyname(my_name[0])
                except socket.error:
                    return not_found
                to_send += bytes(my_name[0], "UTF-8") + b':A=' + bytes(ret, "UTF-8") + b'\r\n'
            elif my_type[0] == "PTR" and re.findall(r"(\d+.\d+.\d+.\d+)", my_name[0]):
                try:
                    a,b,ret = socket.gethostbyaddr(n)
                except socket.error:
                    return not_found
                to_send += bytes(my_name[0], "UTF-8") + b':PTR=' + bytes(a, "UTF-8") + b'\r\n'
            else:
                return bad_request
    return to_send

def post(header, body, to_send):
    arr = header.split("\r\n")
    if re.findall(r"(POST /dns-query HTTP/)", arr[0]):
        to_send = ok
        arr = body.split("\n")
        for line in arr:
            my_name = re.findall(r"\s*([^:\s]+)\s*:\s*(?:\w+)\s*", line)
            my_type = re.findall(r"\s*(?:[^:\s]+)\s*:\s*(A|PTR)\s*", line)
            if my_name and my_type:
                to_send = resolve(my_name[0], my_type[0], to_send)
        if (to_send == ok):
            return bad_request
    return to_send


def length(header):
    match = re.findall(r"Content-Length: (\d+)",header)
    if match:
        return int(match[0])
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Málo argumentů. Použití: $python3 resolver.py PORT\n")
        sys.exit(1)
    if sys.argv[1].isdigit() == 0:
        sys.stderr.write("Argument musí být číslo.\n")
        sys.exit(1)
    if (int(sys.argv[1]) < 1024 or int(sys.argv[1]) > 49151):
        sys.stderr.write("Port musí být v rozmezí 1024-49152.\n")
        sys.exit(1)

    HOST = ''
    PORT = int(sys.argv[1])
    BUFF_SIZE = 4096
    to_send = bad_request
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    
        s.bind((HOST, PORT))
        s.listen()
    except:
        sys.stderr.write("Port se nejspíše používá.\n")
        sys.exit(1)

    
    while 1:
        conn, addr = s.accept()
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
