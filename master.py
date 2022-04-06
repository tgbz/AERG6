import socket, sys, threading, json, random, Sender


type = sys.argv[1]

maxPlayersForGame = 3;


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
        global clients
        self.port = 8080
        self.hostName = socket.gethostname()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.buffer = 2048

    #Add client based on hostname as key to clients dictionary, if it doesn't exist
    def addClient(self, hostname, addr, port):
        if hostname not in clients.keys():
            clients[hostname] = {
                "addr": addr,
                "port": port,
                "ready": 0,
                "ingame": 0
            }
            print("Client " + hostname + " added")
        else:
            print("Client " + hostname + " already exists")
        return clients[hostname]

    #Remove client
    def removeClient(self, hostname):
        if hostname in clients.keys():
            clients.pop(hostname)
            print("Client " + hostname + " removed")
        else:
            print("Client " + hostname + " not found")
        return clients[hostname]

    def handler(self):
        self.socket.bind(('', self.port))
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 1)
        while True:
            data,addr = self.socket.recvfrom(self.buffer)
            
            if data.split('-')[0] == 'hello':
                hostname = data.split('-')[1]
                if hostname not in clients.keys():
                    self.addClient(hostname, addr[0], addr[1])
                    self.socket.sendto(b'hello-ack-' + hostname.encode(), addr)
                else:
                    self.socket.sendto(b'you are already in the group' + hostname.encode(), addr)
            elif data.split('-')[0] == 'ready':
                hostname = data.split('-')[1]
                if hostname in clients.keys():
                    if clients[hostname]['ready'] == 0:
                        clients[hostname]['ready'] = 1
                        self.socket.sendto(b'ack-' + hostname.encode(), addr)
                    else:
                        self.socket.sendto(b'You are already ready' + hostname.encode(), addr)
                else:
                    self.socket.sendto(b'you are not in the group' + hostname.encode(), addr)
    def run(self):
        self.handler()




class gameHandler(threading.Thread):
    def __init__(self):
        self.songDB = "songlist.json"
        self.songList = json.load(open(self.songDB))
        self.mCastSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.mCastSocket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 1)
        self.mCastSocket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 1)
        self.mCastSocket.bind(('',self.ip))
        self.controlSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ip = "FF02::1"
        self.port = 30000
        self.gameState = 0
        self.totalPlayers = 0

    def roundHandler(self):
        #select random number between 1 and 5 to choose a song based on songlist key, where the keys are numbers between 1 and 5
        song = random.randint(1,5)
        # go through clients
        #send the song to the clients
        fileToSend = self.songList[song]["filepath"]
        numberOfPlayers = self.getReadyPlayers()
        controlCounter = 0
        print("Sending song to " + str(numberOfPlayers) + " players")
        #call sender class with ip,port,filepath,socket, where ip is the multicastaddr
        Sender(self.ip, self.port, fileToSend, self.mCastSocket)         




    def verifyClientReady(self, hostname):

        if hostname in clients.keys():
            if clients[hostname]["ready"] == 1:
                return True
            else:
                return False
        else:
            return False

    #Verify if client is in game

    def verifyClientInGame(self, hostname):
        if hostname in clients.keys():
            if clients[hostname]["ingame"] == 1:
                return True
            else:
                return False
        else:
            return False

    #function to get the players that are ready, returning an array containing its addresses
    def getReadyPlayersAddr(self):
        readyPlayers = []
        for client in clients.keys():
            if clients[client]["ready"] == 1:
                readyPlayers.append(clients[client]["addr"])
        return readyPlayers

    #function to get the number of players that are ready
    def getReadyPlayers(self):
        readyPlayers = 0
        for client in clients.keys():
            if clients[client]["ready"] == 1:
                readyPlayers += 1
        return readyPlayers
 

