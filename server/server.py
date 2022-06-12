import threading, random, pprint, time, socket, gameGenerator, re



#Variaveis Globais
nClients = 0 #numero de clientes online
conClients = dict() #dicionario de clientes
routingTable = dict() #dicionario de rotas
gameData = dict() #dicionario de dados do jogo


class ClientManager(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.port = 8081
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
        self.buffer = 2048
        self.gamePort = 8080
        self.hostname = socket.gethostname()

    def addClient(self, hostname, addr, port):
        global conClients, nClients, routingTable
        if hostname not in conClients.keys():
            self.gamePort += 1
            conClients[hostname] = {
                "addr": addr,
                "status": 1, #0 = not connected, 1 = connected, 2 = ready, 3 = ingame
                "port" : self.gamePort
            }
            routingTable[addr] = addr
            nClients += 1
            print("Client " + hostname + " added")
            return 1
        else:
            print("Client " + hostname + " already exists")
            return 0

    def removeClient(self, hostname):
        global conClients, nClients, routingTable
        if hostname in conClients.keys():
            conClients.pop(hostname)
            routingTable.pop(hostname)
            nClients -= 1
            print("Client " + hostname + " removed")
            return 1
        else:
            print("Client " + hostname + " does not exist")
            return 0
    #hello-hostname-actualAddr    
    def run(self):
        global conClients, nClients
        print("À espera de clientes...")
        while True:
            data, addr = self.socket.recvfrom(self.buffer)
            msg = data.decode().split('-')
            if msg[0] == "hello":
                if self.addClient(msg[1], addr[0], addr[1]):
                    self.socket.sendto(("hello-ack-" + str(self.gamePort)).encode(), addr)
                    print("hello ack sent to " + msg[1])
                else:
                    self.socket.sendto("You are already connected".encode(), addr)
            elif msg[0] == "disconnect":
                if self.removeClient(msg[1]):
                    self.socket.sendto("disconnect-ack".encode(), addr)
                    print("disconnect ack sent to " + msg[1])
                else:
                    self.socket.sendto("You are not connected".encode(), addr)



class GameManager():
    def __init__(self, rounds, gameSize):
        self.rounds = rounds #Numero de rondas associadas a cada jogo
        self.gameSize = gameSize #Numero de jogadores por jogo
        self.gameClients = dict()
        self.run()
        
    def selectClientsForGame(self):
        global conClients
        for client in conClients:
            if conClients[client]["status"] == 1:
                conClients[client]["status"] = 2
                self.gameClients[client] = conClients[client]
        print("Selected Clients for game: ")
    
    def run(self):
        global nClients
        print("À espera de jogos....")
        while True:
            while nClients < self.gameSize:
                time.sleep(0.1)
            print("jogo a iniciar...\n\n\n")
            self.selectClientsForGame()
            gm = GameLobby(self.gameSize, self.rounds, self.gameClients)
            gm.start()
            nClients = 0

class GameLobby(threading.Thread):
    def __init__(self, gameSize, rounds, gameClients):
        threading.Thread.__init__(self)
        self.port = 8080
        self.rounds = rounds
        self.gameSize = gameSize
        self.gameClients = gameClients
        self.gameData = dict()
        self.buffer = 4096
        self.gameClients = gameClients
        self.threadPool = []
        self.gameData = dict()
        self.lock = threading.Lock()
        self.gameDone = 0
    
    def updateGameData(self, addr, nCorrectas, tempo):
        self.gameData[addr] = {
            "nCorrectas": nCorrectas,
            "tempo": tempo
        }
        self.gameDone += 1
    
    def run(self):
        global gameData
        gg = gameGenerator.gameGenerator(self.rounds)
        gameMenu = gg.getOptionsForSongs()
        pprint.pprint(self.gameClients)
        gameID = random.randint(0, 10000)
        gameData[gameID] = dict()
        for client in self.gameClients:
            print("startedThread")
            t = ClientGame(self.gameClients[client]["addr"], self.gameClients[client]["port"], gameMenu, gameID, self)
            self.threadPool.append(t)
        #start all the threads
        for thread in self.threadPool:
            thread.start()
        #wait for all the threads to finish
        for thread in self.threadPool:
            thread.join()
            
class ClientGame(threading.Thread):
    def __init__(self, caddr, cport, gameMenu, gameID, parent):
        threading.Thread.__init__(self)
        self.addr = caddr
        self.port = cport
        self.gameMenu = gameMenu + "-end"
        self.buffer = 4096
        self.gameID = gameID
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
        self.parent = parent
        
        
    def startGame(self):
        while True:
            print("trying to send startGame to " + self.addr)
            try:
                msg = "gameStart"
                self.socket.sendto(msg.encode(), (self.addr, self.port))
                data, addr = self.socket.recvfrom(self.buffer)
                if data.decode() == "gameStart-ack" and addr[0] == self.addr:
                    print("gameStart-ack received")
                    break
            except socket.timeout:
                print("timeout")
            
    def sendGameMenu(self):
        while True:
            print("trying to send gameMenu to " + self.addr)
            try:
                self.socket.sendto(self.gameMenu.encode(), (self.addr, self.port))
                data, addr = self.socket.recvfrom(self.buffer)
                if data.decode() == "gameMenu-ack" and addr[0] == self.addr:
                    print("gameMenu-ack received")
                    break
            except socket.timeout:
                print("Timeout")
    
    def sendGo(self):
        while True:
            try:
                msg = "go"
                self.socket.sendto(msg.encode(), (self.addr, self.port))
                data, addr = self.socket.recvfrom(self.buffer)
                if data.decode() == "go-ack" and addr[0] == self.addr:
                    print("go-ack received")
                    break
            except socket.timeout:
                print("Timeout")
    #results-r<id>-@tempo#escolha-r<id>-@tempo#escolha-
    def waitForEnd(self):
        while True:
            try:
                data, addr = self.socket.recvfrom(self.buffer)
                if data.decode().split('-')[0] == "results" and addr[0] == self.addr:
                    res = data.decode()
                    self.socket.sendto("results-ack".encode(), addr)
                    break
            except socket.timeout:
                print("Timeout")
        with self.parent.lock:
            self.parent.updateGameData(self.addr, res.split('-')[1], res.split('-')[2])
    
    def finalResults(self):
        while self.parent.gameDone < self.parent.gameSize:
            time.sleep(0.1)
        print("Final Results: ")
        pprint.pprint(self.parent.gameData)
        
        
        
    
    def run(self):
        self.socket.settimeout(3)
        self.startGame()
        self.sendGameMenu()
        self.sendGo()
        self.waitForEnd()
        self.finalResults()
        
                
def main():
    cm = ClientManager()
    cm.start()
    gm = GameManager(3, 2)
    
if __name__ == "__main__":
    main()