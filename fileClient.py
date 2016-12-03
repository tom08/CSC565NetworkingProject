"""
Author:             Thomas Kroll
File:               fileClient.py
RUN REQUIREMENTS:   This program requires Python3 to run correctly.
                    (Written using Python 3.5)
Description:
        This file contains the source code for the client/peer program. This handles
    requests entered by the user to either exit the program or send a specified file
    to a specified destination. If the destination is offline, this program will handle
    sending the specified file to the server. This program also handles recieving files
    that have been queued on the server to send to this client.
        In a seperate thread, this program listens for file transfer requests from the
    server. In the event of a request, (and the user accepts the file) the program will
    use the address supplied by the server to contact the client wishing to send the file
    and will handle the sending/recieving of that file.
"""
import os.path, sys, select
import socket
import threading
from settings import SERVER_ADDR, CLIENT_DOWNLOAD_DIR


class ListenerThread(threading.Thread):
    """
        This class is a seperate thread to listen for requests from either
        the server or other peers.
    """

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
        # This method handles sending a file to a peer.

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
        # This method handles recieving a file from a peer.

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
        # This method handles the central server contacting the client
        # with a peer's request to send a file.

        data = client_sock.recv(1024).decode()
        if not data:
            return
        args = data.split("::")

        # IF: This client is the destination of a send file request.
        if(len(args) >= 5 and args[0] == "REQUEST"):
            ask_approve = input("Host: "+args[2]+" wants to send the file: "+args[4]+".  Do you accept? [y/N]:")
            # If the user rejects the file, tell the server the file is rejected.
            if ask_approve not in ('y', 'Y', 'yes', 'Yes', 'YES'):
                ack = "REJECTED::FILE::"+args[4]
                client_sock.send(ack.encode())
                return
            # Else, tell the server that the file is accepted.
            ack = "ACCEPTED::FILE::"+args[4]

            # Use the information sent by the server to connect to the peer requesting
            # to send a file.
            client_sock.send(ack.encode())
            file_sock = socket.socket()
            file_sock.connect((args[2], self.port))

            # Tell the peer it is ok to send the file.
            file_request = "OKFILE::FILE::"+args[4]
            file_sock.send(file_request.encode())
            ack = file_sock.recv(1024).decode()
            # Handle recieving the file.
            self.recv_file(file_sock, args[4])

        # ELSE IF: this is the client that initiated a send file request.
        elif(len(args) >= 3 and args[0] == "OKFILE"):
            ack = "SENDING::FILE::"+args[2]
            client_sock.send(ack.encode())
            # Handle sending the file.
            self.send_file(client_sock, args[2])

    def run(self):
        # Start listening for the server to contact with a request
        # to have a file sent to this client,
        # or for a peer to contact with an OK to send the file that
        # this client requested to send.

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
        # Handle sending a file to the server in the case that
        # the destination client is offline.

        with open(fname, "rb") as f:
            line = f.read(1024)
            while line:
                self.socket.send(line)
                line = f.read(1024)
            self.socket.shutdown(socket.SHUT_WR)

    def get_file_from_server(self, fname):
        # Handle downloading a file from a server that was sent when
        # this client was offline.

        path = CLIENT_DOWNLOAD_DIR+"/"+fname
        print("Recieving "+fname+" from server...")
        with open(path, "wb") as f:
            line = self.socket.recv(1024)
            while line:
                f.write(line)
                line = self.socket.recv(1024)
        print("File Recieved")

    def start(self):
        # Handles the main thread's communication with the server. Here the
        # client handles files stored on the server to send to this client,
        # send or exit commands entered by the user, the case where the server
        # has no record of this client, and some validation.

        listener = ListenerThread(self.local_addr)
        listener.start()
        print("Client main program started!")
        print("Checking for queued files...")
        queued_files = True
        self.socket = socket.socket()
        self.socket.connect((self.host, self.port))

        msg = self.socket.recv(1024).decode()
        msg = msg.split("::")
        # If the server has no record of this client, handle setting a username.
        if len(msg) and msg[0] == "NORECORD":
            username = input("The server has no record of you, please enter a username: ")
            while not username:
                username = input("Please enter a username!")
            username = "UNAME::"+username
            self.socket.send(username.encode())

        # IF there are files queued on the server to send to this client, handle each of them.
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

        # Once all of the administration is complete (username and queued files)
        # wait for the user to enter a send or exit command.
        print("Type 'exit' to quit else 'send <filename> <computer_username>':")
        while True:
            self.socket = socket.socket()
            self.socket.connect((self.host, self.port))
            rcv = self.socket.recv(1024).decode()
            msg = None
            timeout = 2
            while(not msg):
                # Timeout to give the listen thread a chance to interject if a request is made
                # of the client.
                msg, o, e = select.select([sys.stdin], [], [], timeout)
            args = sys.stdin.readline().strip().split()

            # The client has had enough and wishes to exit, handle that.
            if args[0] == "exit":
                self.socket.close()
                break
            # if the not a send command, or it is incorrectly formatted, handle that.
            if args[0] != 'send' or not len(args) >= 3:
                print("That was not a valid command!")
                continue
            # IF the file specified does not exist, handle that.
            if(not os.path.isfile(args[1])):
                print("The file '"+args[1]+"' does not exist!")
                continue

            # Validation passed, send request.
            msg = "TO::"+args[2]+"::FILE::"+args[1]
            fname = args[1]
            self.socket.send(msg.encode())
            rcvd = self.socket.recv(1024).decode()
            args = rcvd.split("::")

            # IF the destination does not respond, handle sending the file to the server.
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
