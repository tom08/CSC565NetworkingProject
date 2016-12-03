"""
Author:             Thomas Kroll
File:               fileServer.py
RUN REQUIREMENTS:   This program requires Python3 to run correctly.
                    (Written using Python 3.5)
Description:
        This file contains the source code for the server that manages the
    communication between peers. The purpose of this server is to allow
    peers to send files to eachother without needing to store the address
    of each peer.  The server also handles the case where a peer is offline
    when a different peer wants to send a file to the offline peer.
        This server is ment to be lightweight and not store files on a permenant
    basis, so the files are removed when the destination client has had a chance
    to download them, even if the client rejects the file.
"""

import os
import socket
import threading
from settings import SERVER_ADDR, SERVER_TEMP_INFO, SERVER_TEMP_INFO_FILE, SERVER_TEMP_FILES,\
                    SERVER_CLIENT_INFO_DIR, SERVER_CLIENT_INFO, TIMEOUT


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
        self.to_socket.settimeout(TIMEOUT)

    def get_fname(self):
        # This method parses the filepath and returns the filename.

        fname = self.filename.split("/")
        return fname[len(fname)-1]

    def log_job(self):
        # This method writes a log of a file that has been temporarally
        # stored on the server, if it does not already exist on the server.
        # The information stored: address of sender, address of destination,
        # and the name of the stored file.

        fname = self.get_fname()
        check_if_exists = SERVER_TEMP_FILES+"/"+self.to_host+"/"+fname
        if os.path.isfile(check_if_exists):
            return
        log = "TOSEND::SENTBY::"+self.init_host+"::TO::"+self.to_host+"::FILENAME::"+fname+"\n"
        with open(SERVER_TEMP_INFO+"/"+SERVER_TEMP_INFO_FILE, "a+") as f:
            f.write(log)
        print(log)

    def store_temp_file(self):
        # This method recieves a file from a client and stores it
        # in a directory.  After making sure the directory exists
        # it sends a message to the client that the desitnation
        # of the file did not respond. The file is then uploaded
        # and stored in the directory.

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
        # This method calls methods to log temporary storage information
        # and store the file.

        self.log_job()
        self.store_temp_file()

    def forward_request(self, request):
        # This method takes a request to send a file and forwards it to
        # the correct destination, if the destination has already responded.

        self.to_socket.connect((self.to_host, self.to_port))
        self.to_socket.send(request.encode());
        rcv_ack = self.to_socket.recv(1024).decode()

    def check_queued_files(self):
        # This method checks the temporarally stored file log to determine
        # if there is a file queued to be sent to the currently connected
        # client.

        rewrite = []
        file_info = []
        info_path = SERVER_TEMP_INFO+"/"+SERVER_TEMP_INFO_FILE
        if not os.path.isfile(info_path):
            return file_info
        with open(info_path, "r") as f:
            line = f.readline()
            while line:
                job = line.split("::")
                # IF: there is not a job selected and the TO value is the connected host
                if not file_info and job[4] == self.init_host:
                    file_info = job
                else:
                    rewrite.append(line)
                line = f.readline()
        with open(info_path, "w+") as f:
            for line in rewrite:
                f.write(line)
        return file_info


    def send_file(self, job):
        # This method handles sending a temporarally stored file to its correct
        # destination.

        fname = job[6].strip()
        request = "SEND::FILE::"+fname+"::FROM::"+job[2]
        print(request)
        self.init_socket.send(request.encode())
        approval = self.init_socket.recv(1024).decode()
        approval = approval.split("::")
        fname = SERVER_TEMP_FILES+"/"+self.init_host+"/"+fname
        # Only send the file if the client approves the file.
        if approval[0] == "APPROVE":
            with open(fname, "rb") as f:
                line = f.read(1024)
                while line:
                    self.init_socket.send(line)
                    line = f.read(1024)
            self.init_socket.shutdown(socket.SHUT_WR)
        # No matter the outcome, we don't keep the file on the server.
        os.remove(fname)

    def write_client(self, username):
        # If the client that is making contact has not contacted the server
        # before, write the username associated with that client to storage.
        # NOTE: There is a bug here that I may not have time to fix this semester,
        # this method does not enforce unique usernames.

        fname = SERVER_CLIENT_INFO_DIR+"/"+SERVER_CLIENT_INFO
        if not os.path.exists(SERVER_CLIENT_INFO_DIR):
            os.makedirs(SERVER_CLIENT_INFO_DIR)
        with open(fname, "a+") as f:
            line = self.init_host+"::"+username+"\n"
            f.write(line)

    def check_client(self, username=None):
        # This method checks the client information file.  If a username is
        # passed, the method returns the address, else the method returns
        # the username of the client that initiated contact.
        # returns none if neither match is found.

        fname = SERVER_CLIENT_INFO_DIR+"/"+SERVER_CLIENT_INFO
        if not os.path.isfile(fname):
            return None
        with open(fname, "r") as f:
            line = f.readline()
            while line:
                entry = line.split("::")
                if not username and entry[0] == self.init_host:
                    return entry[1].strip()
                if username and entry[1].strip() == username:
                    return entry[0]
                line = f.readline()
        return None

    def initial_contact(self):
        # This method handles the initial contact with a client. It calls
        # the method to check if the client has contacted before and creates
        # a new client entry if it has not.

        username = self.check_client()
        if not username:
            not_registered = "NORECORD::"
            self.init_socket.send(not_registered.encode())
            response = self.init_socket.recv(1024).decode().split("::")
            if len(response) and response[0] == "UNAME":
                self.write_client(response[1])

    def run(self):
        # This method handles all of the communication between client/server and
        # calls the correct method to deal with every case.

        try:
            # Check if the client has contacted before.
            self.initial_contact()
            # Check if there is a file to send the client.
            file_to_send = self.check_queued_files()
            if(file_to_send): # If yes, handle sending it.
                self.send_file(file_to_send)
                self.init_socket.close()
                return
            else: # Else tell the client there are no files waiting.
                self.init_socket.send("NOFILES::".encode())
            data = self.init_socket.recv(1024).decode()
            args = data.split('::')

            # Handle the request to send a file to another client.
            if len(args) >=2 and args[0] == "TO":
                # Check if the destination exists and get the address.
                host = self.check_client(args[1])
                if host:
                    self.to_host = host
                else:
                    # If the destination does not exist, let the client know.
                    error = "ERROR::Client '"+args[1]+"' not found!"
                    self.init_socket.send(error.encode())
                    self.init_socket.close()
                    return
            # Handle forwarding a file sending request.
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
        except ConnectionResetError:
            print("The client ("+self.init_host+") has terminated the connection")
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
