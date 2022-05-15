
from re import S
import time, struct, socket, sys, threading, pickle, Receiver, Player, json, pickle


gameOn = 0
mcaddr = ""
serverAddr = ""

class Auth(threading.Thread):
    def __init__(self, serverAddr):
        threading.Thread.__init__(self)
        self.serverAddr = serverAddr
        self.serverPort = 8080
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.hport = 8081
        self.buffer = 2048
        
        
    def auth(self):
        global mcaddr
        global serverAddr
        serverAddr = self.serverAddr
        self.socket=socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket.bind(('', self.serverPort))
        print("A tentar autenticar com o servidor")
        self.socket.sendto(b'new-', (self.serverAddr, self.serverPort))
        while True:
            data, addr = self.socket.recvfrom(self.buffer)
            data = data.decode()
            if data.split('-')[0] == 'hello':
                print("Autenticado com sucesso")
                mcaddr = data.split('-')[2] 
                print("Endereço multicast recebido: " + data.split('-')[2])
                print(mcaddr)
                self.socket.sendto(b'mcast-ok', addr)
            elif data.split('-')[0] == 'ready?':
                print("Servidor a perguntar se estamos prontos:")
                self.socket.sendto(b'readyOk', addr)
                print("Estado Ready enviado")
                #print("A entrar em heartbeat")
                break
            elif data.split('-')[0] == 'mcast?':
                print("Servidor a perguntar o endereço multicast:")
                self.socket.sendto(b'mcastOk', addr)
                print("Endereço multicast enviado")
                #print("A entrar em heartbeat")
                break
        print
        game = Game(mcaddr)
        game.start()
        #self.heartbeat()
    
    def heartbeat(self):
        while True:
            self.socket.sendto(b'heartbeat', (self.serverAddr, self.serverPort))
            print("Heartbeat enviado")
            data, addr = self.socket.recvfrom(self.buffer)
            data = data.decode()
            if data.split('-')[0] == 'hearbeatOk':
                print("Heartbeat OK")
            print("Heartbeat standby")

    def run(self):
        print("Thread de autenticação iniciada")
        self.auth()
    

class Game(threading.Thread):
    def __init__(self,addr):
        threading.Thread.__init__(self)
        self.port = 8888
        self.buffer = 2048
        self.mcastAddr = addr
        
        #Create socket, bind to listen to multicast ipv6 group with self.mcastAddr and self.port
        self.addrInfo = socket.getaddrinfo(self.mcastAddr,None)[0]
        self.socket = socket.socket(self.addrInfo[0], socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, True)
        self.socket.bind(('',self.port))
        self.mreq = struct.pack("16s15s".encode('utf-8'),socket.inet_pton(socket.AF_INET6,self.mcastAddr),(chr(0)*16).encode('utf-8'))
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, self.mreq)
        print("socket configurado")
        
        
        
        self.controlSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.controlPort = 8081
        self.controlSocket.bind(('', self.controlPort))
        self.options = dict()
        self.filePaths = []
        

    def inGame(self):
        print("A espera de ficheiros de musica")
        rec = Receiver.Receiver(self.mcastAddr, self.port, self.buffer)
        self.controlSocket.sendto('songOk'.encode(), (serverAddr, self.controlPort))
        rec = Receiver.Receiver(self.mcastAddr, self.port, self.buffer)
        self.controlSocket.sendto('songOk'.encode(), (serverAddr, self.controlPort))
        rec = Receiver.Receiver(self.mcastAddr, self.port, self.buffer)
        self.controlSocket.sendto('songOk'.encode(), (serverAddr, self.controlPort))
        print("Musicas Recebidas")
        
        while True:
            data, addr = self.socket.recvfrom(self.buffer)
            if json.loads(data):
                self.options = json.loads(data)
                print("Game Received")
            elif data.decode():
                if data.decode() == 'startGame':
                    self.controlSocket.sendto('gameStartOk'.encode(), (serverAddr, self.controlPort))
                    print("Inicio de jogo confirmado")

    """
    Iterar sobre o dicionário options e em cada chave, imprimir os valores e esperar pelo input do utilizador
    
    O dicionario tem o seguinte formato:
    
             = {
                    "1": {
                        "1": "<artist>-<song>",   
                        "2": "<artist>-<song>",
                        "3": "<artist>-<song>",
                        "4": "<artist>-<song>",
                        },
                    "2": {
                        "1": "<artist>-<song>",
                        "2": "<artist>-<song>",
                        "3": "<artist>-<song>",
                        "4": "<artist>-<song>",
                        },
                      
    """
    def play(self, options):
        selections = []
        for game in options:
            Player = Player.Player(game, options[game])
            for key,value in game:
                print(" %s : %s ", key, value)
            startTime = time.time()
            sel = input("Selecione uma das opções: ")
            endTime = time.time() - startTime
            selections.append(str(sel)+str(endTime))
            startTime = 0
            endTime = 0
        self.controlSocket.sendto(pickle.dumps(selections), (serverAddr, self.controlPort))
        print("À espera de resultados")
        while True:
            data, addr = self.controlSocket.recvfrom(self.buffer)
            data = data.decode()
            if data.split('-')[0] == "vencedor":
                winner = data.split('-')[1]
                if winner == self.controlSocket.getsockname()[0]:
                    print("Venceu o jogo!")
                else:
                    print("Perdeu o jogo!, o vencedor é %s" % winner)
    
    
    def run(self):
        print("Thread de jogo inciada")
        data, addr = self.socket.recvfrom(self.buffer)
        print("Depois de receber")
        data = data.decode()
        if data.split('-') == 'loading-':
            print("Inicio de jogo recebido")
            self.controlSocket.sendto('gameStartOk'.encode(), (serverAddr, self.controlPort))
            print("Inicio de jogo confirmado")
            self.inGame()
       
        
        
def main():
    serverAddr = sys.argv[1]
    #Start auth thread
    auth = Auth(serverAddr)
    auth.start()
    
if __name__ == '__main__':
    main()  