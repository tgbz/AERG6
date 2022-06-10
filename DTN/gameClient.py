import socket, json, sys, Player, pickle, time, os, pprint, threading, subprocess, time, playsound 

from multiprocessing import Process


serverAddr = ""




stopMusic = False

def playMusic(file):
    playsound.playsound(file)





class gameClient():
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.buff = 4096
        self.clientPort = 8081
        self.gamePort = 8080
        self.hostName = socket.gethostname()
        self.gameSolutions = dict()
        self.gameMenu = dict()
        self.aSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.aSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(None)
        self.aSocket.bind(('', self.clientPort))
        
    def auth(self):
        
        #send hello-hostname message to server
        self.aSocket.sendto("hello-".encode() + self.hostName.encode(), (serverAddr, self.clientPort))
        print("Mensagem enviada: hello-" + self.hostName)
        while True:
            try:
                data,addr = self.aSocket.recvfrom(self.buff)
                if data.decode() == "hello-ack":
                    print("Conexao ao servidor no endereço" + str(addr[0]) + ":" + str(addr[1]) + " bem sucedida")
                self.gameQueue()
            except socket.timeout:
                
                print("Timeout")
        
        
        
    
        
    
        
    def gameQueue(self):
        
        print("in gameQueue")
        print("À espera de jogo....")
        self.socket.bind(('', self.gamePort))
        

        data, addr = self.socket.recvfrom(self.buff)
        data = data.decode()
        if data=='gameStart':
            #send ack with ack-hostname
            self.socket.sendto(("gameStartack-" + self.hostName).encode(), (serverAddr, self.gamePort))
        print("A espera de informacoes de jogo...")
        time.sleep(0.1)
        try:
            
            data, addr = self.socket.recvfrom(self.buff)
            self.gameMenu = pickle.loads(data)
            pprint.pprint(self.gameMenu)
            self.socket.sendto(("gameOptionsack-" + self.hostName).encode(), (serverAddr, self.gamePort))
        except Exception as e:
            print(e)
        time.sleep(0.1)
        print("Informacoes de jogo recebidas")
        print("A espera das solucoes...")
    
        try :
            data, addr = self.socket.recvfrom(self.buff)
            self.gameSolutions = pickle.loads(data)
            self.socket.sendto(("gameSolutionsack-" + self.hostName).encode(), (serverAddr, self.gamePort))
            
        except Exception as e:
            print(e)
        time.sleep(0.1)
        print("Solucoes recebidas")
        
        pprint.pprint(self.gameSolutions)
        pprint.pprint(self.gameMenu)
        input("Aperte enter para continuar...")
        self.game()


    def game(self):
        global stopThreads
        print("A iniciar jogo")
        myGame = []
        paths = []
        timeArr = []
        results = dict()
        self.socket.settimeout(None)
        for entry in self.gameSolutions.values():
            paths.append(entry["filePath"])
        i = 0
        for round in self.gameMenu.values():
            j = 0    
            tmpSongs = []
            p = Process(name="playsound", target=playMusic, args=(paths[i],))
            p.start()
            print("\x1b[2J\x1b[H",end="")
            startTime = time.time()
            for song in round.values():
                tmpSongs.append(song["title"] + " - " + song["artist"])
                print(str(j) + " : " + song["title"] + " - " + song["artist"])
                j+=1
            print("\n\n")
            option = input("Escolha uma opção:")
            endTime = time.time()
            finalTime = endTime - startTime
            myGame.append(tmpSongs[int(option)])
            timeArr = timeArr + [finalTime]
            stopThreads = True
            p.terminate()
            i+=1
            time.sleep(0.5)
        for i in range(len(myGame)):
            results[str(i)] = {"song":myGame[i], "time":timeArr[i]}
        print("\x1b[2J\x1b[H",end="")            
        self.socket.sendto(pickle.dumps(results), (serverAddr, self.gamePort))
        time.sleep(0.1)
        print("A espera dos oponentes terminarem o jogo...")
        data, addr = self.socket.recvfrom(self.buff)
        if data.decode() == "gameEndAck":
            print("Confirmação de envio de jogada!")
        else:
            print("error")
        print("À espera dos resultados finais...")
        data, addr = self.socket.recvfrom(self.buff)
        
        pprint.pprint(results)











def main():
    global serverAddr
    serverAddr = sys.argv[1]
    client = gameClient()
    client.auth()

if __name__ == '__main__':
    main()