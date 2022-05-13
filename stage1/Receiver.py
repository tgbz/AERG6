import socket, select, threading

class Receiver():
    def __init__(self,ip,port,socket,filepath):
        self.ip = ip
        self.port = port
        self.timeout = 20
        self.buffer = 2048
        self.s = socket
        self.f=open(filepath,'wb')
    def worker(self):
        print("In Receiver Worker")
        self.s.settimeout(self.timeout)
        data,addr = self.s.recvfrom(self.buffer)
        if data:
            print("file received\n")
            filename = data.decode()
        while True:
            ready = select.select([self.s],[],[],self.timeout)
            if ready[0]:
                data,addr = self.s.recvfrom(self.buffer)
                if data:
                    self.f.write(data)
            else:
                print("file transfer complete")
                self.f.close()
                break
        return 1
        