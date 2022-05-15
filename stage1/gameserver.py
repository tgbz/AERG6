import socket, threading, time, sys, pickle, random, time, sys, json, Sender



clients = dict()
maxPlayersForGame = 2
totalReadyPlayers = 0
maxGameRounds = 3


class networkStatusHandler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.hostName = socket.gethostname()
        self.buffer = 2048
        self.mcastAddr = "ff02::abcd:1"
        self.port = 8080
        self.hostName = socket.gethostname()
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
   
    #Funcao Utilitaria que adiciona o cliente, utilizando o endereço ipv6 como chave.
    #Caso ele já exista, não faz nada.    
    def addClient(self,addr,port):
        if addr not in clients.keys():
            if addr not in clients.keys():
                clients[addr] = {
                "port": port,
                "ready": 0,
                "ingame": 0,
                "online": 1
            }
            print("Cliente " + str(addr) + " adicionado")
            return 1
        else:
            print("Cliente " + str(addr) + " já existe")
            return 0 
    #Funcao utilitaria que remove um dado cliente da lista de clientes.
    def removeClient(self,addr):
        if addr in clients.keys():
            clients.pop(addr)
            print("Cliente " + str(addr) + " removido")
        else:
            print("Cliente " + str(addr) + " não encontrado")
    #Funcao utilitaria que devolve o endereço de um dado cliente.
    def getClient(self,addr):
        if addr in clients.keys():
            return clients[addr]
        else:
            print("Cliente nao encontrado")
            return None
    
    #Funcao utilitaria que actualiza o estado de um dado cliente para online
    def setClientOnline(self,addr):
        if addr in clients.keys():
            clients[addr]["online"] = 1
        else:
            print("Cliente nao encontrado")
    #Funcao utilitaria que actualiza o estado de um dado cliente para pronto
    def setClientReady(self,addr):
        global totalReadyPlayers
        if addr in clients.keys():
            clients[addr]["ready"] = 1
            totalReadyPlayers += 1
            
    
    def run(self):
        global totalReadyPlayers
        print("networkStatusHandler iniciada")
        #bind the socket para ipv6
        #Incializaçaõ de loop para gestao de users:
        while True:
            data, addr = self.socket.recvfrom(self.buffer)
            data = data.decode()
            #Cases para a receção de dados:
            """
            1 - Cliente envia mensagem new-addr
            2 - Servidor responde com hello-addr-mcastAddr
            3 - Cliente envia mensagem de confirmação de mcastAddr
            4 - Servidor envia mensagem com ready?
            5 - Cliente responde com readyOk
            7 - Servidor entra em loop de hearbeat (e cliente associado)
            8 - Cliente envia mensagem de disconnect opcional quando quiser.
            """
            if data.split('-')[0]=="new":
                print("Nova conexao de " + str(data.split('-')[1]))
                if self.addClient(addr[0],addr[1])==1:
                    print("Cliente adicionado"  + str(addr))
                    print("Estado actual dos clientes:")
                    print(clients)
                    print("A enviar confirmação para os clientes:")
                    msg = "hello-" + self.hostName + "-" + self.mcastAddr
                    print(msg)
                    self.socket.sendto(msg.encode(),addr)
                    print("Endereço Multicast Enviado")
            elif data.split('-')[0]=="mcast" and data.split('-')[1]=="ok":
                print(data)
                print("Estado actual da lista de clientes:")
                print(clients)
                #verificar se o cliente já está na lista de clientes
                if clients[addr[0]] is not None:
                    print("confirmação de recepção de multicast recebida de " + str(addr[0]))
                    print("A atualizar o seu estado para online")
                    self.setClientOnline(addr[0])
                    msg = "ready?-"+ str(addr[0])
                    self.socket.sendto(msg.encode(), addr)
                else:
                    print("Cliente não está autenticado... A descartar...")
            elif data.split('-')[0]=="readyOk":
                print("cliente " + str(addr[0]) + " está pronto")
                print("Estado actualizado dos clientes")
                self.setClientReady(addr[0])
            
            elif data.split('-')[0]=="disconnect":
                print("A remover cliente " + str(addr[0]))
                self.removeClient(addr[0])
                            
            
class heartbeatHandler(threading.Thread):
    #Funcao que inicializa a thread de heartbeat
    def __init__(self):
        threading.Thread.__init__(self)
        self.hostName = socket.gethostname()
        self.buffer = 2048
        self.port = 8081
    #Funcao que envia um heartbeat para todos os clientes
    def sendHeartbeat(self):
        for addr in clients.keys():
            self.socket.sendto(bytes(("heartbeat-%s"),addr),addr)
            print("Heartbeat enviado para " + str(addr))
        
    #Funcao que recebe um heartbeat de todos os clientes num espaço de 10 segundos, o seu estado é actualizado para online = 0
    def receiveHeartbeat(self):
        global clients
        while True:
            
            data, addr = self.socket.recvfrom(self.buffer)
            data = data.decode()
            if data.split('-')[0]=="heartbeat":
                print("Heartbeat recebido de " + str(addr))
                self.setClientOnline(addr[0])
                self.socket.sendto(bytes(("heartbeatOk-%s"),addr),addr)
            time.sleep(10)
            #Verificar se há clientes offline
            for addr in clients.keys():
                if clients[addr]["online"]==0:
                    print("Cliente " + str(addr) + " offline")
    #Funcao que actualiza o estado de um dado cliente para offline
    
    #Funcao que inicializa a thread de heartbeat
    def run(self):
        print("heartbeat inicializado")
        #bind the socket para ipv6
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
        #Incialização de loop para gestao de heartbeat
        while True:
            self.sendHeartbeat()
            time.sleep(10)
    

"""
Thread para gestão do jogo, que inicializa o jogo e o envio das músicas assim como as opções de jogo para todos os clientes via mutlicast.        
"""
class game(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.songDB = "songlist.json"
        self.songList = json.load(open(self.songDB))
        self.mCastSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.mcastPort = 8888
        self.mcastAddr = "ff02::abcd:1"
        self.buffer = 2048
        self.controlSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.controlPort = 8081
        self.controlSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.controlSocket.bind(('', self.controlPort))
        self.currentGamePlayers = []
        self.currentGameNumberOfPlayers = 0
    
    #Função que escolhe ids de músicas aleatórias da base da dados disponível   
    def chooseSongs(self):
        global maxGameRounds
        options = []
        maxOptions = maxGameRounds
        while len(options)<maxOptions:
            option = str(random.randint(1,len(self.songList)))
            if option not in options:
                options.append(option)
        return options    
    
    """Função que recebe a lista de músicas escolhidas para o jogo (options),  vai buscar outras 3 opções para cada musica escolhida e coloca num dicionário no seguinte formato:
    
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
                        ...
                    }
            O número de opções é sempre 4, e o número de rondas é igual ao maxGameRounds passado como argumento.
    """
    def getOptions(self,options,maxGameRounds):
        print("options: " + str(options))
        print("maxGameRounds: " + str(maxGameRounds))
        optionsDict = {}
        for i in range(0,len(options)):
            optionsDict[str(i+1)] = {}
            for j in range(1,5):
                optionsDict[str(i+1)][str(j)] = self.songList[options[i]]["artist"] + "-" + self.songList[options[i]]["title"]
        print(optionsDict)
        return optionsDict
     
    #Função respnsável por popular o dicionário de currentGamePlayers com os ids dos clientes com estado ready até um máximo de totalReadyPlayers
    def getReadyPlayers(self,totalReadyPlayers):
        global clients
        readyPlayers = []
        for addr in clients.keys():
            if clients[addr]["ready"]==1:
                readyPlayers.append(addr)
        if len(readyPlayers)<totalReadyPlayers:
            print("Número de jogadores insuficiente para iniciar o jogo")
            return False
        else:
            return readyPlayers
    
    def multiSender(self,file,flag):
        sen = Sender.Sender(self.mcastAddr,self.mcastPort,file,flag,self.mCastSocket)
        sen.start()
        sen.join()
       
    def controlMCast(self,controlString):
        print("A espera de confirmacoes...")
        controlCounter = 0
        while controlCounter < len(self.currentGamePlayers):
            data, addr = self.controlSocket.recvfrom(self.buffer)
            if data.decode() == controlString:
                print("Jogador " + str(addr) + " confirmou a recepção do ficheiro")
                controlCounter += 1
        print("Todos os jogadores acusam rececao do ficheiro")
    
    """
    Funcao responsável por iniciar um loop de recolha de respostas de jogadores através do controlSocket
    
    No final deverá ser preenchido um dicionario com o seguinte formato:

        respostas = {
                        "<player>":{ <ronda>: <opcao>-<tempo>,
                                     <ronda>: <opcao>-<tempo>,
                                     ....
                                     
                        }
        }
    
    formatoDeEntrada:
        answers$<opcao>$tempo>$<opcao>$<tempo>$<opcao>$<tempo>
    """
        
    def getPlayersChoices(self,rounds):
        playersAnswers = {}
        controlCounter = 0
        while controlCounter <= len(self.currentGamePlayers):
            data, addr = self.controlSocket.recvfrom(self.buffer)
            data = data.decode()
            print("Escolhdas do jogador %s: %s recebidas" % (str(addr[0]),str(addr[1])))
            controlCounter += 1
            if addr[0] not in playersAnswers.keys():
                playersAnswers[addr[0]] = {}
                controlRoundsCounter = 0
                splitsCounter = 1
                while controlRoundsCounter < rounds:
                    playersAnswers[addr[0]][controlRoundsCounter][data.split('$')[splitsCounter]] = data.split('$')[splitsCounter+1]
                    splitsCounter += 2
                    controlRoundsCounter += 1
                return playersAnswers
            else:
                print("erro nas opções")
                return None
    
    
    #funcao que recebe uma lista de ids de musicas e vai a songlist procurar o titlo e adicionalo ao array songstittle
    
    def getSongsTittle(self,list):
        songsTittle = []
        for i in list:
            songsTittle.append(self.songList[i]["song"])
        return songsTittle
    """
    
    Função de calculo de vençedor
    Recebe as opções e as solucoes.
    Vai a cada entrada no dicionario:
          respostas = {
                        "<player>":{ <ronda>: <opcao>-<tempo>,
                                     <ronda>: <opcao>-<tempo>,
                                     ....
                        }
        }
    """
    
    def findWinner(self,answers,solutions):
        winners = []
        currentGamePlayers = []
        for player in answers.keys():
            currentGamePlayers.append(player)
            for round in answers[player].keys():
                if answers[player][round] == solutions[round-1]:
                    timeSelected = answers[player][round].split('-')[1]
                    temp = player
                    for i in range(0,len(winners)):
                        if not winners[i] or winners[i].split('-')[1]>=timeSelected:
                            winners.append(player+"-"+timeSelected)
        results = {}
        for p in currentGamePlayers:
            results[p]=0    
        for winner in winners:
            print("O vencedor da ronda " + str(round) + " é o jogador " + winner.split('-')[0])
            results[p]=results[p]+1
        print(results)
        
        #get the winner from results dictionary, which is the key with the highest value
        winner = max(results, key=results.get)
        print("O vencedor do jogo é o jogador " + winner)
        return winner
        
    
    
    def generateGame(self):
        global totalReadyPlayers
        global clients
        self.currentGamePlayers = self.getReadyPlayers(totalReadyPlayers)
        #Escolher <maxGameRounds> músicas aleatórias da base de dados para o jogo
        selectedSongs = self.chooseSongs()
        gameOptions = self.getOptions(selectedSongs,maxGameRounds)
        controlCounter = 0
        filepaths = []
        filepaths = [self.songList[song]["filePath"] for song in selectedSongs]
        print("filepaths")
        self.multiSender("loading-",2)
        self.controlMCast("gameStartOk")
        for i in range(0,len(filepaths)):
            self.multiSender(filepaths[i],0)
            self.controlMCast("songOk")
        print("Musicas enviadas")
        self.multiSender(gameOptions,1)
        self.controlMCast("optionsOk")
        print("Opções Enviadas")
        #Enviar mensagem de começo de jogo para todos os jogadores
        self.multiSender("startGame",2)
        self.controlMCast("gameStartOk")
        answers = self.getPlayersChoices()
        print("Escolhas recebidas:")
        print(answers)
        print("A determinar vencedor")
        songsTittle = self.getSongsTittle(selectedSongs)
        winner = self.findWinner(answers,songsTittle)
        self.controlMCast("O vencedor é o jogador " + winner)
        self.controlMCast("okEndgame")
        self.totalReadyPlayers = 0
        #set all players from this game to not ready
        for player in self.currentGamePlayers:
            for player in clients:
                self.clients[player]["ready"] = False
        self.currentGamePlayers = []
    def run(self):
        while totalReadyPlayers < maxPlayersForGame:
            time.sleep(0.1)
        print("game Thread incializada")
        self.generateGame()


def main():
    #Inicializar as threads networkStatusHandler, heartbeatHandler e Game
    net = networkStatusHandler()
    #heart = heartbeatHandler()
    gamet = game()
    net.start()
    #heart.start()
    gamet.start()

if __name__ == "__main__":
    main()