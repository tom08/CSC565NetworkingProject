"""
Initial contact: TO::hostname::FILE::filename
"""
import os.path, sys, select
import socket
import threading
from settings import SERVER_ADDR


class ListenerThread(threading.Thread):

    def __init__(self, host):
        threading.Thread.__init__(self)
        self.socket = socket.socket()
        self.host = host
        self.port = 12002
        self.ok_to_run = True
        self.approve = False
        self.daemon = True

    def exit(self):
        self.ok_to_run = False

    def listen(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)

    def handle(self, client_sock):
        data = client_sock.recv(1024).decode()
        if not data:
            return
        print(str(data))
        args = data.split("::")
#REQUEST format == REQUEST::HOST::<host>::FILE::<filename>
        if(len(args) >= 5 and args[0] == "REQUEST"):
            ask_approve = input("Host: "+args[2]+" wants to send the file: "+args[4]+".  Do you accept? [y/N]:")
            if ask_approve not in ('y', 'Y', 'yes', 'Yes', 'YES'):
                ack = "REJECTED::FILE::"+args[4]
                client_sock.send(ack.encode())
                return
            ack = "ACCEPTED::FILE::"+args[4]
            client_sock.send(ack.encode())
            file_sock = socket.socket()
            file_sock.connect((args[2], self.port))
            file_request = "OKFILE::FILE::"+args[4]
            file_sock.send(file_request.encode())
            ack = file_sock.recv(1024).decode()
            print(ack)
        elif(len(args) >= 3 and args[0] == "OKFILE"):
            ack = "SENDING::FILE::"+args[2]
            client_sock.send(ack.encode())

    def run(self):
        self.listen()
        print("Client Listener starting at: " + self.host +":"+str(self.port))
        while self.ok_to_run:
            client, client_addr = self.socket.accept()
            print("Established Connection: " + str(client_addr))
            self.handle(client)
        self.socket.close()




class FileClient:

    def __init__(self, host, local_addr):
        self.host = host
        self.local_addr = local_addr
        self.port = 12001
        self.socket = None

    def start(self):
        listener = ListenerThread(self.local_addr)
        listener.start()
        print("Client main program started!")
        print("Type 'exit' to quit else 'send filename hostname':")
        while True:
            self.socket = socket.socket()
            self.socket.connect((self.host, self.port))
            msg = None
            timeout = 2
            while(not msg):
                msg, o, e = select.select([sys.stdin], [], [], timeout)
            args = sys.stdin.readline().strip().split()
            if args[0] == "exit":
                break
            if args[0] != 'send' or not len(args) >= 3:
                print("That was not a valid command!")
                continue
            if(not os.path.isfile(args[1])):
                print("The file '"+args[1]+"' does not exist!")
                continue
            msg = "TO::"+args[2]+"::FILE::"+args[1]
            self.socket.send(msg.encode())
            rcvd = self.socket.recv(1024).decode()
            print("> "+str(rcvd))
            self.socket.close()
        listener.exit()

def main():
    host = SERVER_ADDR
    local_addr = input("Enter your ip address:")
    client = FileClient(host, local_addr)
    client.start()

if __name__ == "__main__":
    main()
