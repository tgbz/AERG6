from re import M
import time, struct, socket, sys, threading, Receiver, player

mCastAddr = ""
  
  
class GameHandler(threading.Thread):
    def __init__(self,m):
        self.mCastAddr = m
        self.gameState = 0
        self.timeToAnswer = 0
        self.mainSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.mainPort = 30000
        self.buffer = 2048
    def run(self):
        self.mainSocket.bind(('', self.mainPort))
        rec = Receiver(mCastAddr,self.mainPort,self.mainSocket,self.buffer).start()
        res = rec.worker()
        if res == 1:
            self.mainSocket
  
  
  
def messageHandler(self,s, buffer):
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
    
