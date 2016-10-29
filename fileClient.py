"""
Initial contact: TO::hostname::FILE::filename
"""
import socket
import threading


class ListenerThread(threading.Thread):

    def __init__(self, host):
        threading.Thread.__init__(self)
        self.socket = socket.socket()
        self.host = host
        self.port = 12002
        self.ok_to_run = True
        self.daemon = True

    def exit(self):
        self.ok_to_run = False

    def listen(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)

    def handle(self, client_sock):
        while self.ok_to_run:
            data = client_sock.recv(1024).decode()
            if not data:
                break
            print(str(data))
            to_send = "Recieved: " + str(data)
            client_sock.send(to_send.encode())

    def run(self):
        self.listen()
        print("Client Listener starting at: " + self.host +":"+str(self.port))
        while self.ok_to_run:
            client, client_addr = self.socket.accept()
            print("Established Connection: " + str(client_addr))
            self.handle(client)
        self.socket.close()




class FileClient:

    def __init__(self, host):
        self.host = host
        self.port = 12001
        self.socket = socket.socket()

    def start(self):
        self.socket.connect((self.host, self.port))
        print("Client main program started!")
        listener = ListenerThread("127.0.0.1")
        listener.start()
        print("Type 'exit' to quit else 'send filename hostname':")
        while True:
            msg = input("> ")
            if msg == "exit":
                break
            args = msg.split()
            if args[0] != 'send' or not len(args) >= 3:
                print("That was not a valid command!")
                continue
            msg = "TO::"+args[2]+"::FILE::"+args[1]
            self.socket.send(msg.encode())
            rcvd = self.socket.recv(1024).decode()
            print("> "+str(rcvd))
        self.socket.close()
        listener.exit()

def main():
    host = "127.0.0.1"
    client = FileClient(host)
    client.start()

if __name__ == "__main__":
    main()
