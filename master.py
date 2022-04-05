import socket, sys, threading, json, random


type = sys.argv[1]

maxPlayersForGame = 0;


songlist = "songlist.json"
multicastAddr = "FF02::1"
clients = dict()

#formato mensagens login
#hello-hostname-join
#ready-

"""dicionário clientes
    {
        hostname: {
            addr:ipv6,
            port:port,
            ready: 0,
            ingame: 0/1
            },
            ...
    }
"""


class gameLogin(threading.Thread):
    def __init__(self):
        self.port = 8080
        self.hostName = socket.gethostname()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.buffer = 2048

    def addPlayer(self, addr):
        if addr not in clients.keys():
            clients[addr] = {
                "addr": addr,
                "port": self.port,
                "ready": 0,
                "ingame": 0
            }
            print("Client " + addr + " added")
        else:
            print("Client " + addr + " already exists")
        return clients[addr]

    def removePlayer(self, addr):
        if addr in clients.keys():
            clients.pop(addr)
            print("Client " + addr + " removed")
        else:
            print("Client " + addr + " not found")
        return clients[addr]
    
    def verifyPlayerReady(self, addr):
        if addr in clients.keys():
            if clients[addr]["ready"] == 1:
                return True
            else:
                return False
        else:
            return False

    def verifyPlayerInGame(self, addr):
        if addr in clients.keys():
            if clients[addr]["ingame"] == 1:
                return True
            else:
                return False
        else:
            return False

    def handler(self):
        self.socket.bind(("",self.port))
        while True:
            data, addr = self.socket.recvfrom(self.buffer)
            data = data.decode('utf-8')
            print("Received message: " + data + " from " + str(addr))
            if data.split('-')[0] == "hello" and data.split('-')[2] == "join":
                if data.split("-")[1] not in clients.keys():
                    clients[data.split("-")[1]] = addr[0]
                    self.socket.sendto(bytes("helloOK-"+socket.gethostname()+str(multicastAddr),'utf-8'),(addr[0],self.port))
                else:
                    self.socket.sendto(bytes("youAreAlreadyAuthenticatedDiscarding-",'utf-8'),(addr[0],self.port))
            elif data.split('-')[0] == "ready":
                    if 
                    self.socket.sendto(bytes("readyOK-",(addr[0],self.port)))

class gameHandler(threading.Thread):
    def __init__(self):
        self.songList = json.load(open(songlist))
        self.mCastSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.mCastSocket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 1)
        self.mCastSocket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 1)
        self.mCastSocket.bind(('',multicastAddr))
        self.gameState = 0
    def roundHandler():
        #select random number between 1 and 5 to choose a song based on songlist key, where the keys are numbers between 1 and 5
        song = random.randint(1,5)
        #send the song to the clients
        fileToSend = songlist[song]["filepath"]
        fileToSend = 