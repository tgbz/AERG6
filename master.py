import socket, threading,  json, random, Sender, pickle, time, sys

##Global Vars
clients = dict()
maxPlayersForGame = 2
totalReadyPlayers = 0

class controlHandler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        global clients
        self.port = 8080
        self.hostName = socket.gethostname()
        #ipv6 socket
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.buffer = 2048
        global totalReadyPlayers
    
    #Adicionar cliente, utilizando o endereço do cliente como chave.
    #Caso ele já exista, não faz nada.
    def addClient(self, addr, port):
        if addr not in clients.keys():
            clients[addr] = {
                "port": port,
                "ready": 0,
                "ingame": 0,
                "online": 1
            }
            print("Cliente " + addr + " adicionado")
        else:
            print("Cliente " + addr + " já existe")
        return clients[addr]

    def removeClient(self, addr):
        if addr in clients.keys():
            clients.pop(addr)
            print("Cliente " + addr + " removido")
        else:
            print("Cliente " + addr + " não encontrado")
        return clients[addr]
    
    def getClient(self, addr):
        if addr in clients.keys():
            return clients[addr]
        else:
            print("Cliente nao encontrado")
            return None
    
    def run(self):
        global totalReadyPlayers
        print("In Control Handler\n")
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
        self.mcastAddr = "FF02::1"
        while True:
            data, addr = self.socket.recvfrom(self.buffer)
            data = data.decode()
            
            if data.split('-')[0] == "hello":
                #verificar se o addr esta presente no dicionario
                if addr not in clients.keys():
                    self.addClient(addr[0], addr[1])
                    self.socket.sendto(bytes(str("hello-ack-"+ str(self.mcastAddr)).encode()), addr)
                else:
                    self.socket.sendto(bytes("Cliente ja existente" + addr.encode()), addr)
                print(clients)
            
            elif data.split('-')[0] == "ready":
                #verificar se o addr esta presente no dicionario
                if addr[0] in clients.keys():
                    if clients[addr[0]]["ready"] == 0:
                        clients[addr[0]]["ready"] = 1
                        self.socket.sendto(bytes(str("ready-ack-" + str(addr[0])).encode()), addr)
                        totalReadyPlayers += 1
                    else:
                        self.socket.sendto(bytes(str("Cliente ja esta pronto" + addr.encode())), addr)
                else:
                    self.socket.sendto(bytes(str("Cliente nao encontrado" + str(addr[0])).encode()), addr)
            elif data.split('-')[0] == "control":
                #verificar se o addr esta presente no dicionario, dar update ao atributo online para 1
                if addr in clients.keys():
                    clients[addr[0]]["online"] = 1
                    self.socket.sendto(bytes(str("control-ack" + addr.encode())), addr)
                else:
                    self.socket.sendto(bytes(str("Cliente nao encontrado" + str(addr[0]).encode())), addr)
            elif data.split('-')[0] == "disconnect":
                #verificar se o addr esta presente no dicionario, dar update ao atributo online para 0
                if addr in clients.keys():
                    clients[addr[0]]['online'] = 0
                    self.socket.sendto(bytes("disconnect-ack" + addr.encode()), addr)
                else:
                    self.socket.sendto(bytes("Cliente nao encontrado" + str(addr[0]).encode()), addr)
            elif data.split('-')[0] == "ingame":
                #verificar se o addr esta presente no dicionario, dar update ao atributo online para 1
                if addr in clients.keys():
                    clients[addr[0]]["ingame"] = 1
                    self.socket.sendto(bytes("ingame-ack" + addr.encode()), addr)
                else:
                    self.socket.sendto(bytes("Cliente nao encontrado" + addr.encode()), addr)




class gameHandler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.songDB = "songlist.json"
        self.songList = json.load(open(self.songDB))
        self.mCastSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.mCastSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.mCastSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT,1)
        self.mCastSocket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 1)
        self.mCastSocket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 5)
        self.mcastPort = 50000
        self.mcastAddr = 'FF02::1'

        self.controlSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.controlSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.controlPort = 30000

        self.gameState = 0
        self.currentGameNumberOfPlayers = 0
        global totalReadyPlayers
    

    def generateGame(self):
        song = random.randint(1,5)
        fileToSend = self.songList[song]["filepath"]
        selectedSongName = self.songList[song]["title"]
        selectedSongArtist = self.songList[song]["artist"]
        self.currentGameNumberOfPlayers = self.getReadyPlayers()
        choices = self.getRandomSongs()
        controlCounter = 0
        print("A enviar música para " + str(self.currentGameNumberOfPlayers) + " players")
        Sender(self.ip, self.port, fileToSend, self.mCastSocket)

        while controlCounter < self.currentGameNumberOfPlayers:
            data, addr = self.controlSocket.recvfrom(self.buffer)
            if data.decode() == "song-ok":
                controlCounter += 1
            print("Música enviada para todos os players")
        self.gameState = 1
        print("Procedendo ao envio das hipóteses de escolha:")
        controlCounter = 0
        self.mCastSocket.sendto(pickle.dumps(choices) (self.mcastAddr, self.mcastPort))
        
        while controlCounter < self.currentGameNumberOfPlayers:
            data, addr = self.controlSocket.recvfrom(self.buffer)
            if data.decode() == "choices-ok":
                controlCounter += 1
                print("Hipóteses de escolha enviadas para todos os players")
        controlCounter = 0
        
        self.mCastSocket.sendto(bytes("game-start", (self.mcastAddr, self.mcastPort)))
        while controlCounter < self.currentGameNumberOfPlayers:
            data, addr = self.controlSocket.recvfrom(self.buffer)
            if data.decode() == "game-start-ok":
                controlCounter += 1
                print("Jogo iniciado")
        results = dict()
        while controlCounter < self.currentGameNumberOfPlayers:
            data, addr = self.controlSocket.recvfrom(self.buffer)
            if data.split('-')[0] == 'choice':
                results[addr]["escolha"] = data.split('-')[1]
                results[addr]["tempo"] = data.split('-')[2]
                controlCounter += 1
                print("Escolha recebida")
                self.controlSocket.sendto(bytes("choice-ok", addr))
        print("Resultados Todos Recebidos:")
        print(results)

        winner = self.getWinner(results, selectedSongName)
        print("O vencedor foi: " + winner)
        self.mCastSocket.sendto(bytes("winner-" + winner[0].encode() + "-" + winner[1].encode(), (self.mcastAddr, self.mcastPort)))
        print("jogo terminado")
        self.gameState = 0
        self.currentGameNumberOfPlayers = 0
        global totalReadyPlayers 
        totalReadyPlayers = 0

    def getReadyPlayers(self):
        readyPlayers = 0
        for client in clients:
            if clients[client]['ready'] == 1:
                readyPlayers += 1
        return readyPlayers
    
    def getRandomSongs(self):
        choices = dict()
        for client in clients:
            if clients[client]['ready'] == 1:
                choices[client] = random.randint(1,5)
        return choices
    
    def getWinner(self, results, selectedSongName):
        winner = dict()
        for client in results:
            if results[client]["escolha"] == selectedSongName:
                winner[client] = results[client]["tempo"]
        return min(winner, key=winner.get)
    
    def run(self):
        global totalReadyPlayers
        global maxPlayersForGame
        while True:
            if totalReadyPlayers == maxPlayersForGame:
                self.generateGame()
            time.sleep(1)
    
def main():
    controlT = controlHandler()
    controlT.start()
    gameT = gameHandler()
    gameT.start()

if __name__ == '__main__':
    main()