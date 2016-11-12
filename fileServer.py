"""
Initial contact: TO::hostname::FILE::filename
"""

import socket
import threading


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

    def handle_no_response(self):
        pass

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
            self.init_socket.send(send_ack.encode())
            self.to_socket.connect((self.to_host, self.to_port))
            self.to_socket.send(to_send.encode());
            rcv_ack = self.to_socket.recv(1024).decode()
            print("CONTACTDED CLIENT:"+rcv_ack)
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
    addr = input("Enter your IP Address:")
    server = FileServer(addr)
    server.main_loop()

if __name__ == "__main__":
    main()
