import time, struct, socket, sys, threading, Receiver, player, pickle

mCastAddr = ""
  
  
class GameHandler(threading.Thread):
    def __init__(self,m,socket,serverAddr, serverPort):
        self.mCastAddr = m
        self.serverAddr = serverAddr
        self.serverPort = serverPort
        self.gameState = 0
        self.timeToAnswer = 0
        self.mainSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.mainPort = 30000
        self.buffer = 2048
        self.controlSocket = socket
        self.timeToAnswer = 0
        self.choices = []
        
    #function that receives the array of choices and displays a menu with the choices, for the user to choose
    def round(self):
        counter = 1
        for entry in self.choices:
            print(str(counter) + " - " + entry)
            counter += 1
        timeStart = time.time()
        option = input("Choose a song: ")
        timeEnd = time.time()
        finalTime = timeEnd - timeStart
        selected = self.choices[int(option)-1]
        return str(selected) + "-" + str(finalTime)
        
    def run(self):
        self.mainSocket.bind(('', self.mainPort))
        rec = Receiver(mCastAddr,self.mainPort,self.mainSocket,self.buffer).start()
        res = rec.worker()
        if res == 1:
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
        round()
        

def messageHandler(s, buffer):
    global mCastAddr
    while True:
        data, addr = s.recvfrom(buffer)
        if data.split('-')[0] == 'hello' and data.split('-')[1] == 'ack':
            print("Hello OK!")
            mCastAddr = data.split('-')[2]
            break
        elif data.split('-')[0] == 'ready' and data.split('-')[1] == 'ack':
            print("Ready ok!")
            break
        elif data.split('-')[0] == 'start' and data.split('-')[1] == 'ack':
            g = GameHandler(mCastAddr)
            g.start()            
            break
        else:
            print("Unknown message!")
            break
    
    
    
def main():
    serverAddr = sys.argv[1]
    controlPort = 8080
    mainPort = 30000
    controlSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    controlSocket = socket.bind('', controlPort)
    mainSocket = socket.bind('b', mainPort)
    buffer = 2048
    
    
    controlSocket.sendto(b'hello', (serverAddr, controlPort))
    messageHandler(controlSocket, buffer)
    controlSocket.sendto(b'ready', (serverAddr, controlPort))
    messageHandler(controlSocket, buffer)
    
