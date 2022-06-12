
from http import server
import socket, sys, time, pprint, time, playsound, json, re
from multiprocessing import Process

serverAddr = ""

def playMusic(file):
    playsound.playsound(file)
    
class gameClient():
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.buff = 4096
        self.clientPort = 8081
        self.gamePort = 0
        self.hostName = socket.gethostname()
        self.gameMenu = ""
        self.paths = [] #caminhos das musicas a reproduzir
        self.opts = [] #ids opcoes de jogo por ronda,
        self.sols = [] #ids musicas a reproduzir
        self.aSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.aSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(None)
        self.aSocket.bind(('', self.clientPort))
        self.songList = json.load(open("../common/songlist.json"))
        self.results = ""
    
    def auth(self):
    
        self.aSocket.sendto("hello-".encode() + self.hostName.encode(), (serverAddr, self.clientPort))
        print("Mensagem enviada: hello-" + self.hostName)
        while True:
            try:
                data,addr = self.aSocket.recvfrom(self.buff)
                if data.decode().split('-')[0] == "hello" and data.decode().split('-')[1] == "ack":
                    print("Conexao ao servidor no endereço" + str(addr[0]) + ":" + str(addr[1]) + " bem sucedida")
                    self.gamePort = int(data.decode().split('-')[2])
                    self.socket.bind(('', self.gamePort))
                    print(self.gamePort)
                    self.gameQueue()
            except socket.timeout:
                print("Timeout")
            
    #atraves da string com o formato menu-r<numero>$id$id$id$id-r<numero>$id$id$id$id(...)-end
    #extrair os ids das musicas
    def generateMenu(self, msg):
        print(msg)
        self.opts = []
        self.sols = []
        msg = msg.split('-end')[0]
        print(msg)
        for g in re.findall(r'r\d((\$\d){4})',msg):
            self.opts.append(g[0].split('$')[1:])
        print(self.opts)
        for sols in re.findall(r'((\%\d){'+str(len(self.opts))+'})',msg):
            #print(sols[0].split('%')[1:])
            self.sols = sols[0].split('%')[1:]
        print(self.sols)

       
    def findPaths(self):
        for i in range(len(self.sols)):
            self.paths.append(self.songList[self.sols[i]]["filePath"])
        print(self.paths)
   
       
       
    def gameOn(self):
        self.findPaths()
        print("in gameMenu")
        self.results = "results-"
    
        for i in range(len(self.opts)):
            men = []
            for j in range(len(self.opts[i])):
                tp = str(j) + " : " + self.songList[self.opts[i][j]]["title"] + " - " + self.songList[self.opts[i][j]]["artist"]
                men.append(tp)
            p = Process(name="playsound", target=playMusic, args=(self.paths[i],))
            p.start()
            pprint.pprint(men)
            startTime = time.time()
            choice = input("Escolha uma opção: ")
            endTime = time.time()
            p.terminate()
            print("\x1b[2J\x1b[H",end="")
            finalTime = endTime - startTime
            self.results += "r" + str(i) + "-@" + str(finalTime) + "#" + choice + "-"
        print(self.results)
        self.sendResults()
    

    def gameQueue(self):
        self.socket.settimeout(6)
        print("A espera de jogos...")
        while True:
            try:
                data, addr = self.socket.recvfrom(self.buff)
                msg = data.decode()
                if msg == "gameStart":
                    self.socket.sendto("gameStart-ack".encode(), addr)
                elif msg.split('-')[0] == "menu":
                    print("Recebido menu")
                    self.socket.sendto("gameMenu-ack".encode(), addr)
                    self.generateMenu(msg)
                elif msg.split('-')[0] == "go":
                    self.socket.sendto("go-ack".encode(), addr)
                    self.gameOn()
                    self.sendResults()
                elif msg.split('-')[0] == "final":
                    self.socket.sendto("final-ack".encode(), addr)
                    break
            except socket.timeout:
                print("Timeout")

    def sendResults(self):
        self.sR()
        while True:
            print("a enviar resultados...")
            try:
                self.socket.sendto(self.results.encode(), (serverAddr, self.gamePort))
                data, addr = self.socket.recvfrom(self.buff)
                if data.decode() == "results-ack":
                    print("Resultados enviados")
                    break
            except socket.timeout:
                print("Timeout")
        self.waitForWinner()
     
     
    def sR(self):
        res = self.results.replace("results", "")
        res = res[:-1]
        res = re.split(r'-r[0-9]-', res)
        print("res split " + str(res))
        times = []
        opt = []
        for i in range(1, len(res)):
            times.append(res[i].split('#')[0][1:])
            opt.append(res[i].split('#')[1])
        print("tempos: " + str(times))
        print("options: " + str(opt))        
        
        nCorrectas = 0
        for i in range(len(opt)):
            if opt[i] == self.sols[i]:
                nCorrectas += 1
        timeSum = 0
        for i in range(len(times)):
            timeSum += float(times[i])
        self.results = "results-" + str(nCorrectas) + "-" + str(timeSum)
        
        
    def waitForWinner(self):
        print("A espera resultados finais")
        while True:
            data, addr = self.socket.recvfrom(self.buff)
            if data.decode('-')[0] == "final":
                print("Recebido resultados finais")
                print(data.decode())
                break
        print("Fim do jogo...")
        
def main():
    global serverAddr
    serverAddr = sys.argv[1]
    client = gameClient()
    client.auth()
    
if __name__ == "__main__":
    main()