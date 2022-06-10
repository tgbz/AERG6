import threading, time, sys, json, random, socket, pprint, pickle, gameGenerator, pprint

#Global Vars
conClients = dict()
rConClients = dict()
nClients = 0

gameData = dict()


"""
{gameID <randomly generated> : { 'addr' : {
                                            
}}



"""



#Classe para gestão de autenticação de clients

class ClientsManager(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.port = 8081
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
        #reuse port and reuse addr socket
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.buffer = 2048
        self.hostname = socket.gethostname()
    def addClient(self, hostname, addr, port):
        global conClients, nClients
        if hostname not in conClients.keys():
            conClients[hostname] = {
                "addr": addr,
                "status": 1, #0 = not connected, 1 = connected, 2 = ready, 3 = ingame
            }
            nClients += 1
            print("Client " + hostname + " added")
            return 1
        else:
            print("Client " + hostname + " already exists")
            return 0
        
    def removeClient(self, hostname):
        if hostname in conClients.keys():
            conClients.pop(hostname)
            print("Client " + hostname + " removed")
            return 1
        else:
            print("Client " + hostname + " not found")
            return 0
    def run(self):
        global conClients, nClients
        print("À espera de clientes...")
        while True:
            data, addr = self.socket.recvfrom(self.buffer)
            msg = data.decode().split('-')
            if msg[0] == "hello":
                if self.addClient(msg[1], addr[0], addr[1]):
                    self.socket.sendto("hello-ack".encode(), addr)
                    print("hello ack sent to " + msg[1])
                else:
                    self.socket.sendto("You are already connected".encode(), addr)
            elif msg[0] == "disconnect":
                if self.removeClient(msg[1]):
                    self.socket.sendto("disconnect-ack".encode(), addr)
                    print("disconnect ack sent to " + msg[1])
                else:
                    self.socket.sendto("You are not connected".encode(), addr)



class GameManager(threading.Thread):
    def __init__(self, rounds, gameSize):
        threading.Thread.__init__(self)
        self.rounds = rounds #Numero de rondas associadas a cada jogo
        self.gameSize = gameSize #Numero de jogadores por jogo
        self.gameClients = dict()    
    
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
            gm = GameServer(3, 1, self.gameClients)
            gm.start()
            nClients = 0
        
        


class GameServer(threading.Thread):
    def __init__(self, rounds, gameSize, gameClients):
        threading.Thread.__init__(self)
        self.rounds = rounds #Numero de rondas associadas a cada jogo
        self.gameSize = gameSize #Numero de jogadores por jogo
        self.gameClients = dict()
        self.port = 8080
        self.clientsAnswers = dict()
        self.gameSolutions = dict()
        self.buffer = 2048
        self.gameClients = gameClients
        self.threadPool = []
        

    def getWinner(self):   
        winner = None
        winnerScore = 0
        winnerTime = 0
        for client in self.clientsAnswers:
            score = 0
            for round in self.clientsAnswers[client]:
                if self.clientsAnswers[client][round]["answer"] == self.gameSolutions[round]:
                    score += 1
                    time = self.clientsAnswers[client][round]["time"]
            if score > winnerScore and time < winnerTime:
                winner = client
                winnerScore = score
                winnerTime = time
        return winner

    def run(self):
        global gameData
        gg = gameGenerator.gameGenerator(self.rounds)
        gg.generateGame()
        gameSolutions = gg.getSongs()
        gameOptions = gg.getOptions()
        pprint.pprint(self.gameClients)
        gameID = random.randint(0, 10000)
        gameData[gameID] = dict()
        for client in self.gameClients:
            print("startedThread")
            t = ClientGame(self.gameClients[client]["addr"], self.port, gameOptions, gameSolutions, gameID)
            self.threadPool.append(t)
        #start all the threads
        for thread in self.threadPool:
            thread.start()
        #wait for all the threads to finish
        for thread in self.threadPool:
            thread.join()
        
            


class ClientGame(threading.Thread):
    def __init__(self, addr, port, gameOptions, gameSolutions, gameID):
        threading.Thread.__init__(self)
        self.addr = addr
        self.port = port
        self.gameOptions = gameOptions
        self.gameSolutions = gameSolutions
        self.buffer = 8192
        self._return = None
        self.gameID = gameID
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
    
    
    def startGame(self):
        self.socket.settimeout(5)
        #send message to client to start game
        #wait for client to start game
        while True:
            try:
                self.socket.sendto("gameStart".encode(), (self.addr, self.port))
                print(threading.get_ident(), "gameStart sent to " + self.addr)
                data, addr = self.socket.recvfrom(self.buffer)
                if addr[0] == self.addr:
                    if data.decode().split('-')[0] == "gameStartack":
                        print("gameStart received from " + self.addr)
                        print("Game started")
                        self.socket.settimeout(None)
                        time.sleep(1)
                        break
            except socket.timeout:
                print("Timeout")
        
      
    def sendGameOptions(self):
        self.socket.settimeout(3)
        #send the game options via pickle to client
        print("gameOptions sent to " + self.addr)
        #wait for client to receive game options
        while True:
            try:
                var = pickle.dumps(self.gameOptions)
                self.socket.sendto(var, (self.addr, self.port))
                data, addr = self.socket.recvfrom(self.buffer)
                if addr[0] == self.addr:
                    if data.decode().split('-')[0] == "gameOptionsack":
                        print("Game options confirmation")
                        self.socket.settimeout(None)
                        time.sleep(1)
                        break
            except socket.timeout:
                print("Timeout")
                
        time.sleep(0.1)
    def sendGameSolutions(self):
        self.socket.settimeout(3)
        #send game solution to client
        print("gameSolution sent to " + self.addr)
        while True:
            try:
                self.socket.sendto(pickle.dumps(self.gameSolutions), (self.addr, self.port))
                data, addr = self.socket.recvfrom(self.buffer)
                if addr[0] == self.addr:
                    if data.decode().split('-')[0] == "gameSolutionsack":
                        print("Game solutions confirmation")
                        self.socket.settimeout(None)
                        time.sleep(1)
                        break
            except socket.timeout:
                print("Timeout")
        time.sleep(0.1)

  
    
    def run(self):
        global gameData
        print("starting game for " + str(self.addr) + " port: " + str(self.port))
        self.startGame()
        self.sendGameOptions()
        self.sendGameSolutions()
        print("A espera dos resultdos do cliente " + str(self.addr))
        done = 0
        while not done:
            try:
                data, recv = self.socket.recvfrom(self.buffer)
                if recv[0] == self.addr:
                    gameRes = pickle.loads(data)
                    done = 1
            except pickle.UnpicklingError:
                print("Error receiving game options")
            
        gameRes = list(gameRes.values())
        print("Resultados recebidos!")
        self.socket.sendto("gameEndAck".encode(), (self.addr, self.port))
        print("Confirmação enviada")
        print("Addr :  " + str(self.addr))
        gameData[self.gameID][str(self.addr)] = gameRes
        
def main():
    cm = ClientsManager()
    cm.start()
    gm = GameManager(3, 2)
    gm.start()
    
if __name__ == "__main__":
    main()