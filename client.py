import time, struct, socket, sys, threading

class gameClient(threading.Thread):
    def __init__(self,serverAddr):
        self.controlPort = 8080
        self.mainPort = 30000
        self.controlSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.mainSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.hostname = socket.gethostname()
        self.buffer = 2058
        self.serverAddr = None

    def auth(self):
        self.controlSocket.sendto(b"hello-" + self.hostname.encode() + b"-join", self.serverAddr)
        #wait for ack
        while True:
            data, addr = self.controlSocket.recvfrom(self.buffer)
            if data.split('-')[0] == 'hello' and data.split('-')[1] == 'ack':
                    print("Client " + self.hostname + " authenticated")
            else:
                print("Client " + self.hostname + " not authenticated\n" + "error:")
                sys.exit()
            self.controlSocket.sendto(b"ready-" + self.hostname.encode() + b"-join", self.serverAddr)
            #wait for ack
            data, addr = self.controlSocket.recvfrom(self.buffer)
            if data.split('-')[1] == 'ack':
                print("Client " + self.hostname + " ready")
                break
            else:
                print("Client " + self.hostname + " not ready\n" + "error:")
                sys.exit()
    