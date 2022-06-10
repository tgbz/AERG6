import socket, time, threading,json, struct



class Sender(threading.Thread):
    def __init__(self, ip, port, file, flag, socket):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.file = file
        self.s = socket
        self.buffer = 2048
        self.type = flag # 0 for song, 1 for options, 2 for strings
        
    def run(self):
        print("Flag recebida: ", self.type)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('', self.port))
        self.s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, True)
        mreq = struct.pack("16s15s".encode('utf-8'),socket.inet_pton(socket.AF_INET6,self.ip),(chr(0)*16).encode('utf-8'))
        self.s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)
        
        if self.type == 0:
            self.f = open(self.file, 'rb')
            data = self.f.read(self.buffer)
            print("Ficheiro lido no Sender")
            while(data):
                print("A tentar enviar..")
                if(self.s.sendto(data,(self.ip,self.port))):
                    data=self.f.read(self.buffer)
                    print("ficheiro enviado")
                    time.sleep(0.05)
            self.f.close()
            print("Ficheiro enviado em multicast")
        #enviar opções de jogo em formato json(dicionário)
        elif self.type == 1:
            data = self.file
            print("A enviar opcoes de musicas")
            while(data):
                print("A tentar enviar")
                self.s.sendto(json.dumps(self.file),(self.ip,self.port))
                time.sleep(0.05)
                print("ficheiro enviado")
            print("Opções enviadas em multicast")
        #enviar strings passadas como argumento
        elif self.type == 2:
            data = self.file
            print("A enviar strings")
            print("A tentar enviar")
            self.s.sendto(data.encode(),(self.ip,self.port))
            time.sleep(0.05)
            print("String % s enviada em multicast" % self.file)
        