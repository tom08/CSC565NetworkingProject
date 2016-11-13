"""
Initial contact: TO::hostname::FILE::filename
"""

import os
import socket
import threading
from settings import SERVER_ADDR, SERVER_TEMP_INFO, SERVER_TEMP_INFO_FILE, SERVER_TEMP_FILES


class HandleRequest(threading.Thread):

    def __init__(self, sock, addr):
        threading.Thread.__init__(self)
        self.init_socket = sock
        self.init_host = addr[0]
        self.init_port = addr[1]
        self.to_host = None
        self.to_port = 12002
        self.filename = None
        self.to_socket = socket.socket()
        self.to_socket.settimeout(5)

    def get_fname(self):
        fname = self.filename.split("/")
        return fname[len(fname)-1]

    def log_job(self):
        fname = self.get_fname()
        log = "TOSEND::SENTBY::"+self.init_host+"::FROM::"+self.to_host+"::FILENAME::"+fname+"\n"
        with open(SERVER_TEMP_INFO+"/"+SERVER_TEMP_INFO_FILE, "a+") as f:
            f.write(log)
        print(log)

    def store_temp_file(self):
        temp_dir = SERVER_TEMP_FILES+"/"+self.to_host
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        failure = "NORESPONSE::HOST::"+self.to_host
        self.init_socket.send(failure.encode())
        with open(temp_dir+"/"+self.get_fname(), "wb") as f:
            line = self.init_socket.recv(1024)
            while line:
                f.write(line)
                line = self.init_socket.recv(1024)

    def handle_no_response(self):
        self.log_job()
        self.store_temp_file()

    def forward_request(self, request):
        self.to_socket.connect((self.to_host, self.to_port))
        self.to_socket.send(request.encode());
        rcv_ack = self.to_socket.recv(1024).decode()
        print("CONTACTED CLIENT:"+rcv_ack)


    def run(self):
        data = self.init_socket.recv(1024).decode()
        args = data.split('::')
        if len(args) >=2 and args[0] == "TO":
            self.to_host = args[1]
        if len(args) >= 4 and args[2] == "FILE":
            self.filename = args[3]
        if self.to_host and self.filename:
            send_ack = "RECIEVED::HOST:"+self.to_host+", SEND:"+self.filename
            to_send = "REQUEST::HOST::"+self.init_host+"::FILE::"+self.filename
            try:
                self.forward_request(to_send)
                self.init_socket.send(send_ack.encode())
            except socket.error:
                self.handle_no_response()
        else:
            send_ack = "ERROR::No data or improperly formatted data recieved"
            self.init_socket.send(send_ack.encode())
        return

class FileServer:

    def __init__(self, host):
        self.host = host
        self.port = 12001;
        self.socket = socket.socket()

    def listen(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(10)

    def handle(self, client_sock, addr):
        HandleRequest(client_sock, addr).start()

    def main_loop(self):
        self.listen()
        print("Server starting at: " + self.host +":"+str(self.port))
        while True:
            client, client_addr = self.socket.accept()
            print("Established Connection: " + str(client_addr))
            self.handle(client, client_addr)

def main():
    if not os.path.exists(SERVER_TEMP_INFO):
        os.makedirs(SERVER_TEMP_INFO)
    addr = SERVER_ADDR
    server = FileServer(addr)
    server.main_loop()

if __name__ == "__main__":
    main()
