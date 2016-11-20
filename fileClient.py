"""
Initial contact: TO::hostname::FILE::filename
"""
import os.path, sys, select
import socket
import threading
from settings import SERVER_ADDR, CLIENT_DOWNLOAD_DIR


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

    def send_file(self, client_sock, fname):
        print("Sending File")
        f = open(fname, 'rb')
        send_line = f.read(1024)
        while send_line:
            client_sock.send(send_line)
            send_line = f.read(1024)
        f.close()
        print("File Sent")
        client_sock.shutdown(socket.SHUT_WR)
        client_sock.close()

    def recv_file(self, file_sock, fname):
        print("Receiving File...")
        fname = fname.split("/")
        fname = fname[len(fname)-1]
        f = open(CLIENT_DOWNLOAD_DIR+"/"+fname, 'wb')
        write_line = file_sock.recv(1024)
        while write_line:
            f.write(write_line)
            write_line = file_sock.recv(1024)
        f.close()
        print("File Recieved")
        file_sock.close()

    def handle(self, client_sock):
        data = client_sock.recv(1024).decode()
        if not data:
            return
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
            self.recv_file(file_sock, args[4])
        elif(len(args) >= 3 and args[0] == "OKFILE"):
            ack = "SENDING::FILE::"+args[2]
            client_sock.send(ack.encode())
            self.send_file(client_sock, args[2])

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

    def send_file_to_server(self, fname):
        with open(fname, "rb") as f:
            line = f.read(1024)
            while line:
                self.socket.send(line)
                line = f.read(1024)
            self.socket.shutdown(socket.SHUT_WR)

    def get_file_from_server(self, fname):
        path = CLIENT_DOWNLOAD_DIR+"/"+fname
        print("Recieving "+fname+" from server...")
        with open(path, "wb") as f:
            line = self.socket.recv(1024)
            while line:
                f.write(line)
                line = self.socket.recv(1024)
        print("File Recieved")

    def start(self):
        listener = ListenerThread(self.local_addr)
        listener.start()
        print("Client main program started!")
        print("Checking for queued files...")
        queued_files = True
        self.socket = socket.socket()
        self.socket.connect((self.host, self.port))

        msg = self.socket.recv(1024).decode()
        msg = msg.split("::")
        if len(msg) and msg[0] == "NORECORD":
            username = input("The server has no record of you, please enter a username: ")
            while not username:
                username = input("Please enter a username!")
            username = "UNAME::"+username
            self.socket.send(username.encode())

        while queued_files:
            if msg[0] == "NORECORD":
                msg = self.socket.recv(1024).decode()
                msg = msg.split("::")
            if msg[0] == "NOFILES":
                queued_files = False
                print("No queued files on the server.")
            elif len(msg) and msg[0] == "SEND":
                approval = input(msg[4]+" would like to send the file: "+msg[2]+". Do you accept? [y/N]")
                if approval not in ('y', 'Y', 'yes', 'Yes', 'YES'):
                    self.socket.send("DENY::".encode())
                    continue
                self.socket.send("APPROVE::".encode())
                self.get_file_from_server(msg[2])
            self.socket = socket.socket()
            self.socket.connect((self.host, self.port))
            msg = self.socket.recv(1024).decode()
            msg = msg.split("::")

        print("Type 'exit' to quit else 'send filename computer_username':")
        while True:
            self.socket = socket.socket()
            self.socket.connect((self.host, self.port))
            rcv = self.socket.recv(1024).decode()
            msg = None
            timeout = 2
            while(not msg):
                msg, o, e = select.select([sys.stdin], [], [], timeout)
            args = sys.stdin.readline().strip().split()
            if args[0] == "exit":
                self.socket.close()
                break
            if args[0] != 'send' or not len(args) >= 3:
                print("That was not a valid command!")
                continue
            if(not os.path.isfile(args[1])):
                print("The file '"+args[1]+"' does not exist!")
                continue
            msg = "TO::"+args[2]+"::FILE::"+args[1]
            fname = args[1]
            self.socket.send(msg.encode())
            rcvd = self.socket.recv(1024).decode()
            args = rcvd.split("::")
            if(len(args) and args[0] == "NORESPONSE"):
                print("No response from "+args[2]+": uploading file to server")
                self.send_file_to_server(fname)
                print("File uploaded to server.")
            if len(args) > 1 and args[0] == "ERROR":
                print("Error: "+args[1])
            self.socket.shutdown(socket.SHUT_WR)
            self.socket.close()
        listener.exit()

def main():
    if not os.path.exists(CLIENT_DOWNLOAD_DIR):
        os.makedirs(CLIENT_DOWNLOAD_DIR)
    host = SERVER_ADDR
    local_addr = input("Enter your ip address:")
    client = FileClient(host, local_addr)
    client.start()

if __name__ == "__main__":
    main()
