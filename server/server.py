import threading, random, pprint, time, socket, gameGenerator, re

#Variaveis Globais
nClients = 0 #numero de clientes online
conClients = dict() #dicionario de clientes
routingTable = dict() #dicionario de rotas
gameData = dict() #dicionario de dados do jogo

class ClientManager(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.port = 8080
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
        self.buffer = 2048
        self.gamePort = 8081
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
            print("Jogador (" + hostname + ") adicionado")
            return 1
        else:
            print("Jogador (" + hostname + ") ja existente")
            return 0

    def removeClient(self, hostname):
        global conClients, nClients, routingTable
        if hostname in conClients.keys():
            conClients.pop(hostname)
            #routingTable.pop(hostname)
            print("Jogador (" + hostname + ") removido")
            return 1
        else:
            print("Jogador (" + hostname + ") nao existe")
            return 0
    #hello-hostname-actualAddr    
    def run(self):
        global conClients, nClients
        while True:
            print("Servidor a espera de nova conexao")
            data, addr = self.socket.recvfrom(self.buffer)
            msg = data.decode().split('-')
            if msg[0] == "hello":
                if self.addClient(msg[1], addr[0], addr[1]):
                    self.socket.sendto(("hello-ack-" + str(self.gamePort)).encode(), addr)
                    print("Confirmacao de conexao com " + msg[1])
                else:
                    self.socket.sendto("You are already connected".encode(), addr)
            elif msg[0] == "disconnect":
                if self.removeClient(msg[1]):
                    self.socket.sendto("disconnect-ack".encode(), addr)
                    print("Termino de conexao com " + msg[1])
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
        print("Jogadores selecionados para novo jogo: ")
        for key in self.gameClients:
            print("Jogador: "+key+"\t| Addr: "+self.gameClients[key]["addr"]+'\t| Port: '+str(self.gameClients[key]["port"]))
    
    def run(self):
        global nClients, conClients
        print("A espera de Jogadores...")
        while True:
            while nClients < self.gameSize:
                time.sleep(0.1)
            print("Jogo a iniciar...\n\n\n")
            self.selectClientsForGame()
            gm = GameLobby(self.gameSize, self.rounds, self.gameClients)
            gm.start()
            self.gameClients = dict()
            nClients = 0

class GameLobby(threading.Thread):
    def __init__(self, gameSize, rounds, gameClients):
        threading.Thread.__init__(self)
        self.rounds = rounds
        self.gameSize = gameSize
        self.gameClients = gameClients
        self.gameData = dict()
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
        gameID = random.randint(0, 10000)
        gameData[gameID] = dict()
        for client in self.gameClients:
            t = ClientGame(self.gameClients[client]["addr"], self.gameClients[client]["port"], gameMenu, gameID, self)
            self.threadPool.append(t)
        #start all the threads
        for thread in self.threadPool:
            thread.start()
        #wait for all the threads to finish
        for thread in self.threadPool:
            thread.join()
        
        print("Resultado final: ")
        print("|\tAddress\t\t|\tNo Corretas\t|\tTempo")
        for key in self.gameData:
            print("|\t"+key+"\t|\t"+str(self.gameData[key]["nCorrectas"]) +"\t|\t"+str(self.gameData[key]["tempo"]))

        print("\nJogo Terminado")
            
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
            print("A iniciar jogo de " + self.addr)
            try:
                msg = "gameStart"
                self.socket.sendto(msg.encode(), (self.addr, self.port))
                data, addr = self.socket.recvfrom(self.buffer)
                if data.decode() == "gameStart-ack" and addr[0] == self.addr:
                    break
            except socket.timeout:
                pass
            
    def sendGameMenu(self):
        while True:
            try:
                self.socket.sendto(self.gameMenu.encode(), (self.addr, self.port))
                data, addr = self.socket.recvfrom(self.buffer)
                if data.decode() == "gameMenu-ack" and addr[0] == self.addr:
                    break
            except socket.timeout:
                pass
    
    def sendGo(self):
        while True:
            try:
                msg = "go"
                self.socket.sendto(msg.encode(), (self.addr, self.port))
                data, addr = self.socket.recvfrom(self.buffer)
                if data.decode() == "go-ack" and addr[0] == self.addr:
                    break
            except socket.timeout:
                pass
    #results-r<id>-@tempo#escolha-r<id>-@tempo#escolha-
    def waitForEnd(self):
        while True:
            try:
                data, addr = self.socket.recvfrom(self.buffer)
                if data.decode().split('-')[0] == "results" and addr[0] == self.addr:
                    print("Resultados de " + self.addr + " recebidos")
                    res = data.decode()
                    break
            except socket.timeout:
                pass
        with self.parent.lock:
            self.parent.updateGameData(self.addr, res.split('-')[1], res.split('-')[2])
    
    def finalResults(self):
        while self.parent.gameDone < self.parent.gameSize:
            time.sleep(0.1)

        max = 0
        min = 1000
        maxAddr = ""
        minAddr = ""
        for addr in self.parent.gameData:
            if float(self.parent.gameData[addr]["nCorrectas"]) > float(max):
                max = self.parent.gameData[addr]["nCorrectas"]
                maxAddr = addr
            if float(self.parent.gameData[addr]["tempo"]) < float(min):
                min = self.parent.gameData[addr]["tempo"]
                minAddr = addr
        print("Vencedor: " + maxAddr + " com " + str(max) + " resposta corretas")
        
        while True:
            try:
                if maxAddr == self.addr:
                    self.socket.sendto("final-Ganhou o  Jogo!!!".encode(), (self.addr, self.port))
                    data, addr = self.socket.recvfrom(self.buffer)
                    if data.decode() == "final-ack" and addr[0] == self.addr:
                        break
                else:
                    self.socket.sendto("final-Perdeu o Jogo!!!".encode(), (self.addr, self.port))
                    data, addr = self.socket.recvfrom(self.buffer)
                    if data.decode() == "final-ack" and addr[0] == self.addr:
                        print("game over")
                        break
            except socket.timeout:
                pass        
    
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