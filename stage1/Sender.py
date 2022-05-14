import socket, time, threading,json



class Sender(threading.Thread):
    def __init__(self, ip, port, file, flag, socket):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.file = file
        self.s = socket
        self.f = open(file, 'rb')
        self.buffer = 2048
        self.type = flag # 0 for song, 1 for options, 2 for strings
        
    def run(self):
        self.s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 1)
        self.s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 1)
        if self.type == 0:
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
            while(data):
                print("A tentar enviar")
                self.s.sendto(data,(self.ip,self.port))
                time.sleep(0.05)
                print("ficheiro enviado")
            print("String % s enviada em multicast" % self.file)
        