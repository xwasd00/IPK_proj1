import socket
import re
import threading
import sys

# hlavickove http odpovedi
bad_request = b'HTTP/1.1 400 Bad Request\r\n\r\n'
not_found = b'HTTP/1.1 404 Not Found\r\n\r\n'
method_not_allowed = b'HTTP/1.1 405 Method Not Allowed\r\n\r\n'
ok = b'HTTP/1.1 200 OK\r\n\r\n'

## funkce resolve preklada domenova jmena na adresu  naopak, 
#  pripojuje odpoved v zadanem tvaru ke zbytku zpravy k odeslani
#  parametry: n = jmeno(domenove) nebo adresa, t = typ (A nebo PTR), to_send = zprava k odeslani
def resolve(n, t, to_send):
    if t == "A" and not re.findall(r"(\d+.\d+.\d+.\d+)", n):
        try:
            ret = socket.gethostbyname(n)
        except socket.error:
            if to_send == ok or to_send == not_found: 
                # kvuli funkci post -> pokud ve funkci post zatim neni ani jeden radek spravny,
                # vrati not found, jinak pripoji ke zprave (to_send) prelozene jmeno
                return not_found
            return to_send
        ## try except 
        if to_send == not_found:
            to_send = ok # post -> adresa/jmeno nalezeno
        to_send += bytes(n, "UTF-8") + b':A=' + bytes(ret, "UTF-8") + b'\r\n'
    elif t == "PTR" and re.findall(r"(\d+.\d+.\d+.\d+)", n):
        try:
            a,b,ret = socket.gethostbyaddr(n)
        except socket.error:
            if to_send == ok or to_send == not_found: 
                # kvuli funkci post -> pokud ve funkci post zatim neni ani jeden radek spravny,
                # vrati not found, jinak pripoji ke zprave (to_send) prelozene jmeno
                return not_found
            return to_send
        ## try except
        if to_send == not_found:
            to_send = ok #post ->adresa/jmeno nalezeno
        to_send += bytes(n, "UTF-8") + b':PTR=' + bytes(a, "UTF-8") + b'\r\n'
    return to_send


## funkce pro operaci GET
#  zjisti, jestli je dotaz ve spravnem formatu a pomoci 
#  funkce resolve vrati prislusnou odpoved serveru
def get(header, to_send):
    arr = header.split("\r\n")
    line = re.findall(r"GET (\S+) HTTP/", arr[0])
    if line:
        my_name = re.findall(r"/resolve\?name=(\S+)&type=(?:\w+)", line[0])
        my_type = re.findall(r"/resolve\?name=(?:\S+)&type=(A|PTR)", line[0])
        if my_name and my_type:
            to_send = ok
            to_send = resolve(my_name[0], my_type[0], to_send)
            if to_send == ok:
                return bad_request
    return to_send


## funkce pro operaci POST
#  zjisti, jestli je dotaz ve spravnem formatu a pomoci funkce resolve 
## zpracovava zpravu radek po radku
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
        if to_send == ok:
            return bad_request
    return to_send
  
def length(header):
    match = re.findall(r"Content-Length: (\d+)",header)
    if match:
        return int(match[0])
    return 0

if __name__ == "__main__":
    # kontrola argumentu
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
    BUFF_SIZE = 8192
    to_send = bad_request
    # v pripade, ze se nepodari nabindovat HOST s PORTem, ukonci se program
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    
        s.bind((HOST, PORT))
        s.listen()
    except:
        sys.stderr.write("Port se nejspíše používá.\n")
        sys.exit(1)

    
    while 1:
        # prijem a obsluha klienta
        conn, addr = s.accept()
        data = conn.recv(BUFF_SIZE)
        part = data.split(b'\r\n\r\n') # oddeleni hlavicky a zbytku zpravy (operace POST)

        
        if part[0][0:3] == b'GET': # operace GET
            to_send = get( part[0].decode("UTF-8"), to_send )
        elif part[0][0:4] == b'POST': #operace POST (+kontrola delky zpravy, pokud je v hlavicce)
            l = length(part[0].decode("UTF-8"))
            if (l - BUFF_SIZE > 512):
                data = conn.recv(l)
                part[1] += data
            to_send = post(part[0].decode("UTF-8"), part[1].decode("UTF-8"), to_send)
        else:
            #spatna operace (ani GET ani POST)
            to_send = method_not_allowed
        # poslani zpravy a ukonceni spojeni
        conn.sendall(to_send)
        conn.close()

    s.close()
