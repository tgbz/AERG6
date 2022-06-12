import socket, time, threading, queue



class commsManager(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.settimeout(100)
        self.port = 5555
        self.s.bind(('', self.port))
        self.q = queue.Queue()
        self.s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, False)
        self.myGamePacketQueue = queue.Queue()
        self.neighboors = {}

    def run(self):
        iH = inHandler(self, self.s)
        iH.start()
        oH = outHandler(self, self.s)
        oH.start()
      


class inHandler(threading.Thread):
    def __init__(self, parent,socket):
        threading.Thread.__init__(self)
        self.socket = socket
        self.parent = parent
        self.hostname = socket.gethostname()
        
    def run(self):
        while True:
            data, addr = self.socket.recvfrom(4096)
            #put in parent queue the data
            if data.split('-')[0] == str(self.hostname):
                print("GO GAME")
            else:
                self.parent.q.put({'data':data.decode(), 'addr':addr[0], 'port':addr[1]})


class outHandler(threading.Thread):
    def __init__(self, parent, socket):
        threading.Thread.__init__(self)
        self.socket = socket
        self.parent = parent
    def run(self):
        while True:
            if not self.parent.q.empty():
                msg = self.parent.q.get()
                print(msg)
                self.socket.sendto("PUTAS".encode(), (msg['addr'], msg['port']))    







def main():
    cM = commsManager()
    cM.start()
    
if __name__ == "__main__":
    main()