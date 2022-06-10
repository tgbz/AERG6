import threading, json, socket, time, gameGenerator, pprint


connectedClients = dict()
remoteConnectedClients = dict()
nClients = 0





class clientHandler(threading.Thread):
    def __init__(self, addr, port, socket):
        self.clientAddr = addr
        self.clientPort = port
        self.socket = socket
    def startGame(self):
        
        
    def run(self):




class gameServer(threading.Thread):
    def __init__(self, rounds, gameSize):
        threading.Thread.__init__(self)
        self.rounds = rounds # Numero de rondas associadas a cada jogo
        self.gameSize = gameSize # Numero de jogadores por jogo
        self.gameClients = dict()
        self.port = int(8080)
        self.clientsAnswers = dict()
        self.gameSolutions = dict()
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #bind the socket to the port
        self.socket.bind(('', self.port))
        self.buffer = 2048
        
    def selectClientsForGame(self):
        global connectedClients
        #go over connectedClients and random clients for game who have the status = 1, change status to 2
        #and add them to the game
        for client in connectedClients:
            if connectedClients[client]["status"] == 1:
                connectedClients[client]["status"] = 2
                self.gameClients[client] = connectedClients[client]
        print("Selected Clients for game: ")
        pprint.pprint(self.gameClients)


    def multiUnicastMessageLoop(self, message):
        for client in self.gameClients:
            

    def ackLoop(self, message):
        


    def getWinner(self):
        """
        Return the winner of the game, comparing the answers of each client with the correct solution, and return the client with the highest score which is correspondent to the lowest time
        """        
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
    
    def endGame(self):
        """
        Send the results to each client, if the client won, send the score and "Ganhaste o jogo" message. If the client did not won, send the score and "Perdeste o jogo" message.
        """
        winner = self.getWinner()
        for client in self.gameClients:
            if client == winner:
                self.socket.sendto("Ganhaste o jogo" + str(self.clientsAnswers[client]["score"]), (self.gameClients[client]["addr"], self.port))
            else:
                self.socket.sendto("Perdeste o jogo" + str(self.clientsAnswers[client]["score"]), (self.gameClients[client]["addr"], self.port))
        self.gameClients.clear()
        self.clientsAnswers.clear()
        self.gameSolutions.clear()
    
    def run(self):
        while nClients < self.gameSize:
            print("game not ready...")
            time.sleep(1)
        self.selectClientsForGame()
        self.messageHandler("gameStart")    
        #gG = gameGenerator.gameGenerator(self.rounds)
        #correctSongs, songOptions = gG.chooseSongs(), gG.getOptionsForSongs()
        #self.gameSolutions = correctSongs
       #self.objectHandler(json.dumps(correctSongs))
        #self.objectHandler(json.dumps(songOptions))
        



    

class clientsHandler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.port = 8081
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        self.socket.bind(('', self.port))
        self.buffer = 2048
        self.hostname = socket.gethostname()
        
    def addClient(self, hostname, addr, port):
        global connectedClients, nClients
        if hostname not in connectedClients.keys():
            connectedClients[hostname] = {
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
        if hostname in connectedClients.keys():
            connectedClients.pop(hostname)
            print("Client " + hostname + " removed")
            return 1
        else:
            print("Client " + hostname + " not found")
            return 0
    def run(self):
        global connectedClients, nClients
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

def main():
    ch = clientsHandler()
    gs = gameServer(3,2)
    ch.start()
    gs.start()
    

if __name__ == "__main__":
    main()