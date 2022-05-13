import socket, threading, time, sys, pickle, random, time, sys, json, Sender



clients = dict()
maxPlayersForGame = 2
totalReadyPlayers = 0
maxGameRounds = 3

""" 
clients : {
    <client_id> : {
        port : <port>,
        ready : <bool>,
        ingame : <bool>,
        online : <bool>,
    },
    <client_id> : {
        port : <port>,
        ready : <bool>,
        ingame : <bool>,
        online : <bool>,
    },
    ....
"""

class networkStatusHandler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.hostName = socket.gethostname()
        self.buffer = 2048
        self.mcastAddr = "FF01:0:0:0:0:0:0:1"
   
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
        print("Thread de gestao de utilizadores inicialziada")
        #bind the socket para ipv6
        self.port = 8080
        self.hostName = socket.gethostname()
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
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
                if self.addClient(addr,addr[1])==1:
                    print("Cliente adicionado"  + str(addr))
                    print("Estado actual dos clientes:")
                    print(clients)
                    print("A enviar confirmação para os clientes:")
                    self.socket.sendto(bytes(("hello-%s-%s"),addr[0],self.mcastAddr),addr)
                    print("Endereço Multicast Enviado")
            elif data.split('-')[0]=="mcast-ok":
                #verificar se o cliente já está na lista de clientes
                if clients[addr[0]] is not None:
                    print("confirmação de recepção de multicast recebida de " + str(addr[0]))
                    print("A atualizar o seu estado para online")
                    self.setClientOnline(addr[0])
                    self.socket.sendto(bytes(("ready?-%s"),addr[0]),addr)
                else:
                    print("Cliente não está autenticado... A descartar...")
            elif data.split('-')[0]=="readyOk":
                print("cliente " + str(addr[0]) + " está pronto")
                print("Estado actualizado dos clientes")
                self.setClientReady(addr[0])
            
            elif data.split('-')[0]=="disconnect":
                print("A remover cliente " + str(addr[0]))
                self.removeClient(addr[0])
                            
            
class hearbeatHandler(threading.Thread):
    #Funcao que inicializa a thread de heartbeat
    def __init__(self):
        threading.Thread.__init__(self)
        self.controlPort = 8081
        self.hostName = socket.gethostname()
        self.buffer = 2048
        
    #Funcao que envia um heartbeat para todos os clientes
    def sendHeartbeat(self):
        for addr in clients.keys():
            self.socket.sendto(bytes(("heartbeat-%s"),addr),addr)
            print("Heartbeat enviado para " + str(addr))
    #Funcao que recebe um heartbeat de todos os clientes num espaço de 10 segundos, o seu estado é actualizado para online = 0
    def receiveHeartbeat(self):
        while True:
            data, addr = self.socket.recvfrom(self.buffer)
            data = data.decode()
            if data.split('-')[0]=="heartbeat":
                print("Heartbeat recebido de " + str(addr))
                self.setClientOnline(addr[0])
            time.sleep(10)
            #Verificar se há clientes offline
            for addr in clients.keys():
                if clients[addr]["online"]==0:
                    print("Cliente " + str(addr) + " offline")
    #Funcao que actualiza o estado de um dado cliente para offline
    
    #Funcao que inicializa a thread de heartbeat
    def run(self):
        print("Thread de heartbeat inicializada")
        #bind the socket para ipv6
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
        #Incialização de loop para gestao de heartbeat
        while True:
            self.sendHeartbeat()
            self.receiveHeartbeat()
            time.sleep(10)
    

"""
Thread para gestão do jogo, que inicializa o jogo e o envio das músicas assim como as opções de jogo para todos os clientes via mutlicast.        
"""
class Game(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.songDB = "songlist.json"
        self.songList = json.load(open(self.songDB))
        self.mCastSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.mCastSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.mCastSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.mCastSocket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS,5)
        self.mCastSocket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP,1)
        self.mCastSocket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 100)
        self.mcastPort = 8888
        self.mcastAddr = "FF02::1"
        self.buffer = 2048
        self.controlSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.controlPort = 8081
        self.controlSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.controlSocket.bind(('', self.controlPort))
        
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
    
    """Funcao que escolhe para cada elemento da lista de opções de músicas, vai à base de dados e escolhe 3 outras músicas aleatórias, consistindo um dicionário de escolhas nos seguinte formato:
        rounds = {
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
    """
    def generateOptions(self, options, numberOfRounds):
        rounds = {}
        for i in range(numberOfRounds):
            rounds[str(i+1)] = {}
            for j in range(4):
                rounds[str(i+1)][str(j+1)] = self.songList[options[i]]["artist"] + "-" + self.songList[options[i]]["song"]
                options.remove(options[i])
                for k in range(3):
                    option = str(random.randint(1,len(self.songList)))
                    if option not in options:
                        options.append(option)
                    rounds[str(i+1)][str(j+1+k+1)] = self.songList[option]["artist"] + "-" + self.songList[option]["song"]
        return rounds
    
    def generateGame(self):
        global totalReadyPlayers
        gameSongs = self.chooseOptions()
        print("Músicas escolhidas:")
        for option in gameSongs:
            print(self.songList[option]["title"])
        print("Opções de jogo:")
        rounds = self.generateOptions(gameSongs, maxGameRounds)
        print(rounds)
        filePaths = []
        recvCounter = 0
        for option in gameSongs:
            #get all the filePaths of the songs
            filePaths.append(self.songList[option]["filePath"])
        print("Procedendo ao envio das músicas...")
        for i in range(len(filePaths)):
            print("A enviar música " + str(i+1) + " de " + str(len(filePaths)))
            sen = Sender.Sender(self.mcastAddr,self.mcastPort,filePaths[i],self.mCastSocket)
            while recvCounter <= totalReadyPlayers:
                data, addr = self.controlSocket.recvfrom(self.buffer)
                data = data.decode()
                if data.split('-')[0] == "songReceiveOk":
                    recvCounter+=1
                    print("Música " + str(i+1) + " enviada e confirmada")
            recvCounter = 0
        print("Músicas enviadas")
        print("A enviar opções de jogo...")
        sen = Sender.Sender(self.mcastAddr,self.mcastPort,json.dumps(rounds),self.mCastSocket)
        while recvCounter <= totalReadyPlayers:
            data, addr = self.controlSocket.recvfrom(self.buffer)
            data = data.decode()
            if data.split('-')[0] == "roundsReceiveOk":
                recvCounter+=1
                print("Opções de jogo enviadas e confirmadas")
        recvCounter = 0
        print("Opções de jogo enviadas")
        print("A iniciar o jogo...")
        self.currentGameNumberOfPlayers = totalReadyPlayers
        self.mCastSocket.sendto("gameStart".encode(),(self.mcastAddr,self.mcastPort))
        while recvCounter <= self.currentGameNumberOfPlayers:
            data, addr = self.controlSocket.recvfrom(self.buffer)
            data = data.decode()
            if data.split('-')[0] == "gameStartOk":
                recvCounter+=1
                print("Jogo iniciado")
        recvCounter = 0
        print("À espera de submissão das músicas...")
        playersAnswers = dict()
        """
        playersAnswers = {
                        <playerId>: {
                            <round>: { "choice": "0", "time": "0.0" },
                            <round>: { "choice": "0", "time": "0.0" },
                            <round>:    ...
                            }
        respostaplayer : <escolha>-<tempo>-<escolha>-<tempo>-<escolha>-<tempo> (nrounds)
        """
    
        
        