import socket, threading, json, Receiver, pickle, time, sys, Player

mcastAddr = ""
gameState = 0

class loginStatusHandler(threading.Thread):
    def __init__(self, serverAddr):
        threading.Thread.__init__(self)
        self.controlSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.controlPort = 8080
        
        self.serverAddr = serverAddr
        global mCastAddr
        self.buffer = 2048

        
    def run(self):
        self.controlSocket.bind(('', self.controlPort))
        self.controlSocket.sendto('hello-'.encode(), (self.serverAddr, self.controlPort))
    
        data, addr = self.controlSocket.recvfrom(self.buffer)
        data = data.decode()
        if data.split ('-')[0] == 'hello' and data.split('-')[1] == 'ack':
            print("Hello OK!")
            mCastAddr = data.split('-')[2]
        
        else:
            print(str(data))
            print("Unknown message!")
        
        self.controlSocket.sendto('ready-'.encode(), (self.serverAddr, self.controlPort))
        data, addr = self.controlSocket.recvfrom(self.buffer)
        data = data.decode()
        if data.split ('-')[0] == 'ready' and data.split('-')[1] == 'ack':
            print("Ready ok!")
        else:
            print("message:" +str(data))
            print("Unknown message!")
'''         while True:
            time.sleep(5)
            self.controlSocket.sendto('control-'.encode(), (self.serverAddr, self.controlPort))
            data, addr = self.controlSocket.recvfrom(self.buffer)
            data = data.decode()
            if data.split ('-')[0] == 'control' and data.split('-')[1] == 'ack':
                print("Control ok!")
                time.sleep(5)
            else:
                print("message:" +str(data)) 
                print("Unknown message!")
                break '''
        
class GameHandler(threading.Thread):
    def __init__(self, serverAddr):
        threading.Thread.__init__(self)
        self.mainSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.mainPort = 50000
        self.controlSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.controlPort = 30000
        self.serverAddr = serverAddr
        self.buffer = 2048
        self.choices = []
        self.timeStart = 0
        self.timeEnd = 0
        self.finalTime = 0
        self.selected = 0
       
    def displayChoices(self):
        print("Choices:")
        for i in range(len(self.choices)):
            print(str(i+1) + ": " + self.choices[i])
        print("")
           
       
        
    def run(self):
        global gameState
        print("Waiting for Game...")
        self.mainSocket.bind(('', self.mainPort))
        self.controlSocket.bind(('', self.controlPort))
        rec = Receiver.Receiver(mcastAddr,self.mainPort,self.mainSocket,'file.wav')
        res = rec.worker()
        if res:
            self.controlSocket.sendto(b'song-ok' + self.mCastAddr, rec.addr)
            while True:
                data, addr = self.controlSocket.recvfrom(self.buffer)
                self.choices = pickle.loads(data)
                if data.split('-')[0] == 'choices':
                    self.controlSocket.sendto(b'choices-ok' + self.mCastAddr, addr)
                elif data.split('-')[0] == 'game-start':
                    self.controlSocket.sendto(b'game-start-ok' + self.mCastAddr, addr)
                    break
        else:
            self.controlSocket.sendto(b'song-not-ok' + self.mCastAddr, rec.addr)
        self.timeStart = time.time()
        p = Player(res)
        p.start()
        self.displayChoices()
        selected = input("Enter your choice: ")
        choice = self.choices[selected-1]
        self.timeEnd = time.time()
        self.finalTime = self.timeEnd - self.timeStart
        print("You selected: " + choice)
        print("final time: " + str(self.finalTime))
        self.controlSocket.sendto(b'choice-' + choice.encode() + '-' + str(self.finalTime), addr)
        data, addr = self.controlSocket.recvfrom(self.buffer)
        if data.split('-')[0] == 'choice-ok':
            print("Choice ok!")
        else:
            print("Unknown message!")
        print("gameOver!")
        gameState = 0
    
    
def main():
    if len(sys.argv) != 2:
        print("Usage: python3 client.py <server-ip>")
        sys.exit(1)
    serverAddr = sys.argv[1]
    loginStatus = loginStatusHandler(serverAddr)
    loginStatus.start()
    loginStatus.join()
    game = GameHandler(serverAddr)
    game.start()
    game.join()
    
if __name__ == "__main__":
    main()
