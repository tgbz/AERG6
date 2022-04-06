import socket, time, threading



class Sender(threading.Thread):
    def __init__(self, ip, port, filepath, socket):
        self.ip = ip
        self.port = port
        self.filepath = filepath
        self.s = socket
        self.f = open(filepath, 'rb')
        self.buffer = 2048
    def run(self):
        self.s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 1)
        self.s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 1)
        data = self.f.read(self.buffer)
        while(data):
            if(self.s.sendto(data,(self.ip,self.port))):
                data=self.f.read(self.buffer)
                time.sleep(0.05)
        self.f.close()

    